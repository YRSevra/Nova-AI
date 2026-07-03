"""
core/wake_word.py — Wake Word Detector
───────────────────────────────────────
Listens to the microphone in real-time, looking for "Hey Nova" or "Nova".
"""

import threading
import logging
import numpy as np

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)


class WakeWordDetector:
    """Listens for the wake word and fires a callback."""

    def __init__(self, config: dict, on_wake_callback):
        self.config = config
        self.on_wake = on_wake_callback

        self.running = False
        self._thread = None

        wake_cfg = config.get("wake_word", {})

        self.engine = wake_cfg.get("engine", "simple")
        self.access_key = wake_cfg.get("porcupine_access_key", "")
        self.keywords = wake_cfg.get(
            "keywords",
            ["hey nova", "nova"]
        )
        self.sensitivity = wake_cfg.get("sensitivity", 0.6)

    def start(self):
        self.running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._thread.start()

        logger.info(
            f"Wake word detector started (engine: {self.engine})"
        )

    def stop(self):
        self.running = False

    def _listen_loop(self):

        if self.engine == "porcupine" and self.access_key:
            self._porcupine_loop()
        else:
            logger.info(
                "Using simple wake word detection (Faster-Whisper)"
            )
            self._simple_loop()

    # ---------------------------------------------------------
    # PORCUPINE
    # ---------------------------------------------------------

    def _porcupine_loop(self):

        try:
            import pvporcupine
            import pyaudio

            porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=["porcupine"],
                sensitivities=[self.sensitivity],
            )

            pa = pyaudio.PyAudio()

            stream = pa.open(
                rate=porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=porcupine.frame_length,
            )

            logger.info("Porcupine listening...")

            while self.running:

                pcm = stream.read(
                    porcupine.frame_length,
                    exception_on_overflow=False,
                )

                pcm = np.frombuffer(
                    pcm,
                    dtype=np.int16,
                )

                keyword = porcupine.process(pcm)

                if keyword >= 0:
                    logger.info("Wake word detected!")
                    self.on_wake()

        except ImportError:
            logger.warning(
                "Porcupine unavailable. Using Faster-Whisper."
            )
            self._simple_loop()

        except Exception as e:
            logger.error(e)
            self._simple_loop()

    # ---------------------------------------------------------
    # FASTER WHISPER FALLBACK
    # ---------------------------------------------------------

    def _simple_loop(self):

        try:

            import sounddevice as sd

            model = WhisperModel(
                "tiny",
                device="cpu",
                compute_type="int8",
            )

            sample_rate = 16000
            chunk_duration = 2
            chunk_samples = sample_rate * chunk_duration

            logger.info(
                "Simple wake word listening (Faster-Whisper)..."
            )

            while self.running:

                audio = sd.rec(
                    chunk_samples,
                    samplerate=sample_rate,
                    channels=1,
                    dtype="float32",
                )

                sd.wait()

                audio = audio.flatten()

                segments, _ = model.transcribe(
                    audio,
                    language="en",
                    beam_size=1,
                )

                text = " ".join(
                    segment.text
                    for segment in segments
                ).lower().strip()

                print(f"[DEBUG] Heard: '{text}'")

                if not text:
                    continue

                wake_words = [
                    "nova",
                    "nova.",
                    "noah",
                    "noa",
                    "nora",
                    "hello nova",
                    "hello noah",
                    "hey nova",
                    "hey noah",
                ]

                if any(word in text for word in wake_words):
                    logger.info(f"Wake word detected: {text}")
                    self.on_wake()    
                    continue

        except Exception as e:

            logger.error(
                f"Simple wake word loop error: {e}"
            )