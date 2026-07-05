"""
core/speech_to_text.py — Speech-to-Text (STT)
───────────────────────────────────────────────
Records audio from the microphone and converts it to text using Faster-Whisper.
"""

import logging
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from core.audio_utils import has_voice

logger = logging.getLogger(__name__)


class SpeechToText:
    """Records audio and transcribes it to text using Faster-Whisper."""

    def __init__(self, config: dict):
        speech_cfg = config.get("speech", {})

        self.model_name = speech_cfg.get("whisper_model", "base")
        self.language = speech_cfg.get("language", "en")
        self.max_seconds = speech_cfg.get("max_recording_seconds", 15)
        self.silence_threshold_ms = speech_cfg.get("silence_threshold", 500)

        self.sample_rate = 16000
        self._model = None

        logger.info("Preloading Faster-Whisper model...")
        self._load_model()

        self._load_model()

    def _load_model(self):
        """Load Faster-Whisper model only once."""

        if self._model is None:
            logger.info(f"Loading Faster-Whisper '{self.model_name}' model...")
            logger.info("This happens only once...")

            self._model = WhisperModel(
                self.model_name,
                device="cpu",
                compute_type="int8",
            )

            logger.info("✅ Faster-Whisper ready")

        return self._model

    def listen(self) -> str:
        """
        Record speech from microphone.
        Waits until user starts speaking, then automatically
        stops after silence.
        """

        logger.info("Listening for command...")

        print("\n🎤 Speak now...\n")

        time.sleep(0.5)

        # -----------------------------
        # Recording Settings
        # -----------------------------

        chunk_duration = 0.25
        chunk_samples = int(self.sample_rate * chunk_duration)

        max_wait_seconds = 6
        wait_chunks = int(max_wait_seconds / chunk_duration)

        silence_energy_threshold = 0.008
        silence_chunks_needed = max(
            1,
            int(self.silence_threshold_ms / (chunk_duration * 1000))
        )

        max_chunks = int(self.max_seconds / chunk_duration)

        # -----------------------------
        # State Variables
        # -----------------------------

        voice_started = False

        wait_count = 0
        record_count = 0
        silence_count = 0

        audio_chunks = []

        # -----------------------------
        # Main Recording Loop
        # -----------------------------

        while True:

            chunk = sd.rec(
                chunk_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
            )

            sd.wait()

            energy = np.sqrt(np.mean(chunk ** 2))

            # Silence Detection

            if voice_started:

                if energy < silence_energy_threshold:

                    silence_count += 1

                    if silence_count >= silence_chunks_needed:

                        logger.info("Silence detected. Recording finished.")

                        break

            else:

                silence_count = 0

            # --------------------------------
            # Waiting for user to start talking
            # --------------------------------

            if not voice_started:

                if has_voice(chunk):

                    voice_started = True
                    audio_chunks.append(chunk)

                    logger.info("Voice detected.")

                    continue

                wait_count += 1

                if wait_count >= wait_chunks:

                    logger.info("No speech detected.")

                    return ""

                continue

            # --------------------------------
            # Already recording
            # --------------------------------

            audio_chunks.append(chunk)

            record_count += 1

            if energy < silence_energy_threshold:

                silence_count += 1

                if silence_count >= silence_chunks_needed:

                    logger.info("Silence detected. Recording stopped.")

                    break

            else:

                silence_count = 0

            if record_count >= max_chunks:

                logger.info("Maximum recording length reached.")

                break

        # -----------------------------
        # Convert to single audio array
        # -----------------------------

        if not audio_chunks:
            return ""

        audio = np.concatenate(audio_chunks, axis=0).flatten()

        return self._transcribe(audio)

    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe recorded audio using Faster-Whisper."""

        try:
            model = self._load_model()

            segments, info = model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                temperature=0.0,
            )

            text = "".join(segment.text for segment in segments).strip()

            logger.info(f"Heard: '{text}'")

            return text

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""