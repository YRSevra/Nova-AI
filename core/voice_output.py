"""
core/voice_output.py — Text-to-Speech (TTS)
─────────────────────────────────────────────
Makes Nova speak.

TWO ENGINE OPTIONS:

1. macOS built-in (default, free, no API key):
   Uses the macOS `say` command.
   Best voices: Samantha (US), Karen (Australia), Moira (Ireland)
   Runs completely offline.
   
   To see all available voices, run in Terminal:
     say -v '?' | grep en_

2. ElevenLabs (premium, requires API key):
   Much more natural and expressive female voice.
   Free tier: 10,000 characters/month.
   Sign up at: elevenlabs.io
   
   After getting your API key and voice ID,
   set them in config.yaml under the `voice:` section.
"""

import subprocess
import logging
import threading
import tempfile
import os

logger = logging.getLogger(__name__)


class VoiceOutput:
    """Speaks text using either macOS TTS or ElevenLabs."""

    def __init__(self, config: dict):
        voice_cfg = config.get("voice", {})
        self.engine = voice_cfg.get("engine", "macos")
        self.macos_voice = voice_cfg.get("macos_voice", "Samantha")
        self.macos_rate = voice_cfg.get("macos_rate", 175)
        self.elevenlabs_api_key = voice_cfg.get("elevenlabs_api_key", "")
        self.elevenlabs_voice_id = voice_cfg.get("elevenlabs_voice_id", "")
        self._speaking = False
        self._process = None

    def speak(self, text: str, block: bool = True):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            block: If True, wait for speech to finish before returning.
                   If False, speak in background.
        """
        if not text or not text.strip():
            return

        # Clean up text for speech (remove markdown, etc.)
        text = self._clean_text(text)

        if block:
            self._speak_now(text)
        else:
            threading.Thread(target=self._speak_now, args=(text,), daemon=True).start()

    def _speak_now(self, text: str):
        """Actually speak — called in thread if non-blocking."""
        self._speaking = True
        try:
            if self.engine == "elevenlabs" and self.elevenlabs_api_key:
                self._speak_elevenlabs(text)
            else:
                self._speak_macos(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # Fallback to macOS if ElevenLabs fails
            if self.engine != "macos":
                self._speak_macos(text)
        finally:
            self._speaking = False

    # ────────────────────────────────────────────────────────────────────────
    # macOS built-in TTS
    # ────────────────────────────────────────────────────────────────────────

    def _speak_macos(self, text: str):

        cmd = [
            "say",
            "-v", self.macos_voice,
            "-r", str(self.macos_rate),
            text
        ]

        logger.debug(f"Speaking: {text}")

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self._process.wait()

        self._process = None
    # ────────────────────────────────────────────────────────────────────────
    # ElevenLabs TTS (higher quality)
    # ────────────────────────────────────────────────────────────────────────

    def _speak_elevenlabs(self, text: str):
        """
        Use ElevenLabs API for high-quality voice synthesis.
        
        This generates an MP3, saves it to a temp file, and plays it.
        Requires: elevenlabs API key + voice ID from elevenlabs.io
        """
        try:
            import requests
            import tempfile

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}"
            headers = {
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.8
                }
            }

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()

            # Save audio to temp file and play with macOS `afplay`
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(response.content)
                temp_path = f.name

            subprocess.run(["afplay", temp_path], capture_output=True)
            os.unlink(temp_path)  # Clean up temp file

        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise

    # ────────────────────────────────────────────────────────────────────────
    # Utility
    # ────────────────────────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """
        Clean up text before speaking.
        Remove markdown formatting that sounds bad when spoken.
        """
        import re
        # Remove markdown bold/italic
        text = re.sub(r'\*+([^*]+)\*+', r'\1', text)
        # Remove markdown backticks
        text = re.sub(r'`+([^`]+)`+', r'\1', text)
        # Remove markdown headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove URLs
        text = re.sub(r'https?://\S+', 'link', text)
        # Remove bullet points
        text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)
        # Collapse multiple whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @property
    def is_speaking(self) -> bool:
        return self._speaking
    def stop(self):
        """Immediately stop speaking."""

        if self._process:

            try:
                self._process.terminate()
            except Exception:
                pass

            self._process = None
            self._speaking = False