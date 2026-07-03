"""
Nova Voice Engine V2

Always listens.

Returns:
None
or
command after wake word
"""

import re


class VoiceEngine:

    def __init__(self):

        self.wake_words = [
            "hello nova",
            "hey nova",
            "nova",
            "hello noah",
            "hey noah",
            "noah",
            "noa",
            "nora",
        ]

    def extract_command(self, text: str):

        text = text.lower().strip()

        for wake in self.wake_words:

            if wake in text:

                command = text.replace(wake, "").strip()

                command = re.sub(r"\s+", " ", command)

                return command

        return None