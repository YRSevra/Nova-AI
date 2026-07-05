"""
Audio Utility Functions
"""

import numpy as np


def calculate_energy(audio: np.ndarray) -> float:
    """
    Returns RMS energy of audio.
    """

    if len(audio) == 0:
        return 0.0

    return float(np.sqrt(np.mean(audio ** 2)))


def has_voice(audio: np.ndarray, threshold=0.02) -> bool:
    """
    Returns True if speech exists.
    """

    return calculate_energy(audio) > threshold