"""
core/orchestrator.py — The Main Controller
───────────────────────────────────────────
This is the central hub of Nova. It connects all modules:
  Wake Word → STT → AI Brain → Voice Output
                ↕
           Memory + macOS Control

THE MAIN LOOP:
1. WakeWordDetector runs in a background thread, always listening
2. When wake word is detected, _on_wake_word() is called
3. We record the user's command (STT)
4. We check if it's a macOS action (open app, search, etc.)
5. If yes → execute it, speak confirmation
6. If no → send to AI Brain, speak the AI response
7. Go back to listening
"""

import logging
import threading
import time
from rich.console import Console

from core.wake_word import WakeWordDetector
from core.speech_to_text import SpeechToText
from core.ai_brain import AIBrain
from core.voice_output import VoiceOutput
from core.memory import Memory
from modules.macos_control import MacOSControl

logger = logging.getLogger(__name__)
console = Console()


class Orchestrator:
    """Connects all Nova modules and runs the main conversation loop."""

    def __init__(self, config: dict):
        self.config = config
        self._active = False
        self._processing = False  # Prevent overlapping commands

        user_cfg = config.get("user", {})
        self.user_name = user_cfg.get("name", "Friend")

        # ── Initialize all modules ────────────────────────────────────────
        console.print("[dim]Initializing modules...[/dim]")

        self.memory = Memory(config)
        console.print("[green]✓[/green] Memory (SQLite)")

        self.voice = VoiceOutput(config)
        console.print("[green]✓[/green] Voice output (TTS)")

        self.stt = SpeechToText(config)
        console.print("[green]✓[/green] Speech recognition (Whisper)")

        self.brain = AIBrain(config)
        console.print("[green]✓[/green] AI Brain (OpenAI)")

        self.macos = MacOSControl(config, memory=self.memory)
        console.print("[green]✓[/green] macOS Automation")

        # Wake word detector is initialized last — it needs a callback
        self.wake_detector = WakeWordDetector(config, on_wake_callback=self._on_wake_word)
        console.print("[green]✓[/green] Wake word detector")

        # Setup logging
        log_cfg = config.get("logging", {})
        logging.basicConfig(
            level=getattr(logging, log_cfg.get("level", "INFO")),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )

    def run(self):
        """Start the main loop. Blocks until shutdown is called."""
        self._active = True

        # ── Speak greeting ────────────────────────────────────────────────
        greeting = f"Hello! I'm Nova, your personal assistant. I'm ready to help."
        console.print(f"\n[purple]Nova:[/purple] {greeting}")
        self.voice.speak(greeting)

        # ── Start wake word detection ─────────────────────────────────────
        self.wake_detector.start()

        # ── Main loop — just keep running ────────────────────────────────
        # The actual work happens in _on_wake_word() callbacks
        try:
            while self._active:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

    def _on_wake_word(self):
        """Called when the wake word is detected."""
        if self._processing:
            return  # Ignore if already handling a command

        self._processing = True
        try:
            self._handle_interaction()
        finally:
            self._processing = False

    def _handle_interaction(self):
        """Full interaction cycle: listen → process → respond."""

        # ── 1. Signal that we heard the wake word ─────────────────────────
        console.print("\n[yellow]⚡ Wake word detected![/yellow]")
        # Play a small confirmation sound (macOS built-in)
        self._play_activation_sound()

        # ── 2. Record and transcribe the command ──────────────────────────
        console.print("[dim]Listening...[/dim]")
        command = self.stt.listen()

        if not command or len(command.strip()) < 2:
            console.print("[dim]Nothing heard.[/dim]")
            return

        console.print(f"[cyan]You:[/cyan] {command}")

        # ── 3. Save the command to memory ─────────────────────────────────
        self.memory.save_message("user", command)

        # ── 4. Try macOS automation first ─────────────────────────────────
        # Some commands (open app, search, etc.) don't need AI
        macos_response = self.macos.handle(command)

        if macos_response:
            # It was a macOS command — speak the confirmation
            console.print(f"[purple]Nova:[/purple] {macos_response}")
            self.memory.save_message("assistant", macos_response)
            self.voice.speak(macos_response)
            return

        # ── 5. Ask the AI Brain ───────────────────────────────────────────
        # Load recent conversation context from memory
        recent_context = self.memory.get_recent_messages(limit=6)

        # Sync memory context into the brain's conversation history
        # (Only load if brain has empty history — avoids duplication)
        if not self.brain.conversation_history and recent_context:
            self.brain.conversation_history = recent_context

        # Show thinking indicator
        console.print("[dim]Thinking...[/dim]")

        # Get AI response
        response = self.brain.think(command)

        # ── 6. Speak and save the response ───────────────────────────────
        console.print(f"[purple]Nova:[/purple] {response}")
        self.memory.save_message("assistant", response)
        self.voice.speak(response)

    def _play_activation_sound(self):
        """Play a small sound to confirm Nova heard the wake word."""
        import subprocess
        # Use macOS `afplay` with a built-in system sound
        # /System/Library/Sounds/ has sounds like Tink, Pop, Ping, etc.
        subprocess.Popen(
            ["afplay", "/System/Library/Sounds/Tink.aiff"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def shutdown(self):
        """Gracefully shut down all modules."""
        self._active = False
        if self.wake_detector:
            self.wake_detector.stop()
        logger.info("Nova shut down")
