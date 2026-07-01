"""
core/speech_to_text.py — Speech-to-Text (STT)
───────────────────────────────────────────────
Records audio from the microphone and converts it to text using Whisper.

WHEN THIS IS CALLED:
After the wake word is detected, the orchestrator calls `listen()`.
Nova records until:
- You stop speaking (silence detected), OR
- The maximum recording time is reached

WHISPER MODELS:
  tiny   → 39M params, ~10x realtime, least accurate
  base   → 74M params, ~7x realtime  ← recommended default
  small  → 244M params, ~4x realtime
  medium → 769M params, ~2x realtime
  large  → 1550M params, ~1x realtime, most accurate

Models are downloaded automatically on first use (~100MB for base).
"""

import sounddevice as sd
import numpy as np
import whisper
import logging
import time

logger = logging.getLogger(__name__)


class SpeechToText:
    """Records audio and transcribes it to text using Whisper."""

    def __init__(self, config: dict):
        speech_cfg = config.get("speech", {})
        self.model_name = speech_cfg.get("whisper_model", "base")
        self.language = speech_cfg.get("language", "en")
        self.max_seconds = speech_cfg.get("max_recording_seconds", 15)
        self.silence_threshold_ms = speech_cfg.get("silence_threshold", 500)

        self.sample_rate = 16000  # Whisper expects 16kHz
        self._model = None        # Loaded lazily on first use

    def _load_model(self):
        """Load the Whisper model (once, on first use)."""
        if self._model is None:
            logger.info(f"Loading Whisper '{self.model_name}' model...")
            self._model = whisper.load_model(self.model_name)
            logger.info("Whisper model loaded")
        return self._model

    def listen(self) -> str:
        """
        Record audio from the microphone and return transcribed text.
        
        Listens until silence or max_seconds is reached.
        Returns empty string if nothing was heard.
        """
        logger.info("Listening for command...")
        audio_chunks = []

        # ── Recording parameters ─────────────────────────────────────────
        chunk_duration = 0.5          # Record in 0.5-second chunks
        chunk_samples = int(self.sample_rate * chunk_duration)
        silence_energy_threshold = 0.01  # Below this = silence
        silence_chunks_needed = int(self.silence_threshold_ms / (chunk_duration * 1000))
        silence_count = 0
        total_chunks = 0
        max_chunks = int(self.max_seconds / chunk_duration)

        # ── Record until silence or max time ─────────────────────────────
        while total_chunks < max_chunks:
            chunk = sd.rec(
                chunk_samples,
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32"
            )
            sd.wait()

            audio_chunks.append(chunk)
            total_chunks += 1

            # Calculate chunk energy (volume)
            energy = np.sqrt(np.mean(chunk ** 2))

            if energy < silence_energy_threshold:
                silence_count += 1
                # Stop if we've had enough silence (and at least 1 second of audio)
                if silence_count >= silence_chunks_needed and total_chunks >= 2:
                    logger.debug(f"Silence detected after {total_chunks} chunks")
                    break
            else:
                silence_count = 0  # Reset silence counter when voice is detected

        if not audio_chunks:
            return ""

        # ── Combine all chunks and transcribe ────────────────────────────
        audio = np.concatenate(audio_chunks, axis=0).flatten()
        return self._transcribe(audio)

    def _transcribe(self, audio: np.ndarray) -> str:
        """Send audio array to Whisper and return the text."""
        try:
            model = self._load_model()
            result = model.transcribe(
                audio,
                language=self.language,
                fp16=False,                # fp16 causes issues on some Macs
                condition_on_previous_text=False
            )
            text = result.get("text", "").strip()
            logger.info(f"Heard: '{text}'")
            return text
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
