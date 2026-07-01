"""
core/wake_word.py — Wake Word Detector
───────────────────────────────────────
Listens to the microphone in real-time, looking for "Hey Nova" or "Nova".

TWO MODES:
1. Porcupine mode (recommended): Uses Picovoice Porcupine engine.
   - Very accurate, low CPU, runs offline
   - Needs a free access key from: picovoice.console.ai
   
2. Simple mode (fallback): Uses Whisper to transcribe audio chunks
   and checks if they contain the wake word.
   - No API key needed, but slightly higher CPU usage
   - Less accurate in noisy environments

HOW IT WORKS:
- Continuously reads small audio chunks from the microphone
- Checks each chunk for the wake word
- When found, calls a callback function (provided by orchestrator)
"""

import threading
import numpy as np
import logging

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Listens for the wake word and fires a callback when detected."""

    def __init__(self, config: dict, on_wake_callback):
        """
        Args:
            config: The full Nova config dict
            on_wake_callback: Function to call when wake word is detected.
                              Called with no arguments.
        """
        self.config = config
        self.on_wake = on_wake_callback
        self.running = False
        self._thread = None

        wake_cfg = config.get("wake_word", {})
        self.engine = wake_cfg.get("engine", "simple")
        self.access_key = wake_cfg.get("porcupine_access_key", "")
        self.keywords = wake_cfg.get("keywords", ["hey nova", "nova"])
        self.sensitivity = wake_cfg.get("sensitivity", 0.6)

    def start(self):
        """Start listening in a background thread."""
        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info(f"Wake word detector started (engine: {self.engine})")

    def stop(self):
        """Stop listening."""
        self.running = False

    def _listen_loop(self):
        """Main loop — runs in background thread."""
        if self.engine == "porcupine" and self.access_key:
            self._porcupine_loop()
        else:
            logger.info("Using simple wake word detection (whisper-based)")
            self._simple_loop()

    # ────────────────────────────────────────────────────────────────────────
    # MODE 1: Porcupine (accurate, recommended)
    # ────────────────────────────────────────────────────────────────────────

    def _porcupine_loop(self):
        """
        Use Picovoice Porcupine for wake word detection.
        
        Porcupine listens frame-by-frame (512 audio samples at a time).
        Each frame takes ~32ms at 16kHz — extremely low CPU usage.
        """
        try:
            import pvporcupine
            import pyaudio

            # Create Porcupine instance with built-in "hey google"-style keyword.
            # For "hey nova" you'd need a custom keyword file from Picovoice console.
            # For now we use "porcupine" (the test keyword) or "hey siri"-adjacent.
            # 
            # To create your own "Hey Nova" keyword:
            # 1. Go to console.picovoice.ai
            # 2. Create a custom wake word
            # 3. Download the .ppn file and set keyword_paths below
            
            porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=["porcupine"],  # Replace with custom .ppn for "hey nova"
                sensitivities=[self.sensitivity]
            )

            pa = pyaudio.PyAudio()
            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length
            )

            logger.info("Porcupine wake word listening...")

            while self.running:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                pcm = np.frombuffer(pcm, dtype=np.int16)
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    logger.info("Wake word detected (Porcupine)!")
                    self.on_wake()

        except ImportError:
            logger.warning("pvporcupine not installed, falling back to simple mode")
            self._simple_loop()
        except Exception as e:
            logger.error(f"Porcupine error: {e}, falling back to simple mode")
            self._simple_loop()

    # ────────────────────────────────────────────────────────────────────────
    # MODE 2: Simple / Whisper-based (no API key needed)
    # ────────────────────────────────────────────────────────────────────────

    def _simple_loop(self):
        """
        Simple wake word detection using short audio chunks + Whisper.
        
        Records 2-second chunks, transcribes them, and checks if
        any wake word phrase appears in the transcription.
        
        This is slower than Porcupine but works without any API keys.
        """
        try:
            import sounddevice as sd
            import whisper

            # Load a tiny Whisper model — fast enough for always-on use
            model = whisper.load_model("tiny")
            sample_rate = 16000
            chunk_duration = 2  # seconds
            chunk_samples = sample_rate * chunk_duration

            logger.info("Simple wake word listening (Whisper tiny)...")

            while self.running:
                # Record a short chunk
                audio = sd.rec(
                    chunk_samples,
                    samplerate=sample_rate,
                    channels=1,
                    dtype="float32"
                )
                sd.wait()

                # Transcribe it
                audio_flat = audio.flatten()
                result = model.transcribe(audio_flat, language="en", fp16=False)
                text = result.get("text", "").lower().strip()

                if not text:
                    continue

                # Check for any wake word phrase
                for keyword in self.keywords:
                    if keyword.lower() in text:
                        logger.info(f"Wake word detected: '{text}'")
                        self.on_wake()
                        break

        except Exception as e:
            logger.error(f"Simple wake word loop error: {e}")
