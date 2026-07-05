"""
Nova Voice Engine V3
"""

import re


class VoiceEngine:

    def __init__(self):

        self.wake_patterns = [

            r"^(hello|hey)\s+nova[s]?\b",
            r"^(hello|hey)\s+noah\b",
            r"^(hello|hey)\s+noa\b",
            r"^(hello|hey)\s+nora\b",

            r"^nova[s]?\b",
            r"^noah\b",
            r"^noa\b",
            r"^nora\b",
        ]

        self.filler_words = {
            "please",
            "can",
            "could",
            "you",
            "would",
            "just",
            "kindly",
        }

    def extract_command(self, text: str):

        if not text:
            return None

        text = text.lower().strip()

        text = re.sub(r"[,.!?]", "", text)

        # Remove wake word
        for pattern in self.wake_patterns:

            new_text = re.sub(pattern, "", text).strip()

            if new_text != text:
                text = new_text
                break

        if not text:
            return None

        words = text.split()

        while words and words[0] in self.filler_words:
            words.pop(0)

        command = " ".join(words).strip()

        if command == "":
            return None

        return command