"""
core/intent_engine.py — Nova Intent Engine
───────────────────────────────────────────
Classifies user commands before routing them.

Supported intents:
- automation
- memory
- chat
- unknown
"""

import re
import logging

logger = logging.getLogger(__name__)


class IntentEngine:
    """Detect the intent behind a Nova user command."""

    def detect(self, command: str) -> str:

        if not command or not command.strip():
            return "unknown"

        cmd = command.lower().strip()

        automation_patterns = [
            r"\bopen\b",
            r"\blaunch\b",
            r"\bstart\b",
            r"\brun\b",
            r"\bclose\b",
            r"\bsearch\b",
            r"\bgoogle\b",
            r"\bshow\b",
            r"\bvolume\b",
            r"\bmute\b",
            r"\bunmute\b",
            r"\bshutdown\b",
            r"\brestart\b",
            r"\bsleep\b",
            r"\block\b",
            r"\bbattery\b",
            r"\bwifi\b",
        ]

        for pattern in automation_patterns:

            if re.search(pattern, cmd):

                logger.info(
                    "Intent detected: automation"
                )

                return "automation"

        memory_patterns = [
            r"\bremember\b",
            r"\bdon't forget\b",
            r"\bdo not forget\b",
            r"\bwhat do you remember\b",
            r"\bforget\b",
        ]

        for pattern in memory_patterns:

            if re.search(pattern, cmd):

                logger.info(
                    "Intent detected: memory"
                )

                return "memory"

        logger.info(
            "Intent detected: chat"
        )

        return "chat"