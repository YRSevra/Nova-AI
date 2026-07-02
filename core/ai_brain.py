"""
Nova AI Brain V2
Supports:
- Gemini
- OpenAI
- Conversation Memory
"""

import logging
from openai import OpenAI
from google import genai

logger = logging.getLogger(__name__)


class AIBrain:

    def __init__(self, config: dict):

        self.config = config

        ai_cfg = config.get("ai", {})

        self.provider = ai_cfg.get("provider", "gemini").lower()

        self.openai_model = ai_cfg.get(
            "openai_model",
            "gpt-4o-mini"
        )

        self.gemini_model = ai_cfg.get(
            "gemini_model",
            "gemini-2.5-flash"
        )

        self.max_tokens = ai_cfg.get(
            "max_tokens",
            800
        )

        self.temperature = ai_cfg.get(
            "temperature",
            0.7
        )

        personality = config.get("personality", {})

        self.system_prompt = personality.get(
            "system_prompt",
            "You are Nova."
        )

        memory_cfg = config.get("memory", {})

        self.max_context = memory_cfg.get(
            "max_context_messages",
            10
        )

        self.conversation_history = []

        self.client = None

        self._initialize_provider()

    def _initialize_provider(self):

        if self.provider == "gemini":

            api_key = self.config["ai"]["gemini_api_key"]

            self.client = genai.Client(api_key=api_key)

            logger.info("Gemini initialized")

        elif self.provider == "openai":

            self.client = OpenAI()

            logger.info("OpenAI initialized")

        else:

            raise ValueError(
                f"Unknown provider: {self.provider}"
            )
        
    def think(self, user_message: str) -> str:
        """Generate an AI response."""

        self.conversation_history.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        if len(self.conversation_history) > self.max_context * 2:
            self.conversation_history = (
                self.conversation_history[-self.max_context * 2:]
            )

        try:

            if self.provider == "gemini":
                return self._think_gemini(user_message)

            return self._think_openai()

        except Exception as e:

            logger.exception("AI Error")

            return f"Error: {e}"
        
    def _think_gemini(self, prompt: str) -> str:
        """Generate response using Gemini."""

        response = self.client.models.generate_content(
            model=self.gemini_model,
            contents=prompt
        )

        reply = response.text.strip()

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        return reply

    def _think_openai(self) -> str:
        """Generate response using OpenAI."""

        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ] + self.conversation_history

        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        reply = response.choices[0].message.content.strip()

        self.conversation_history.append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        return reply    

    def clear_history(self):
        """Clear conversation history."""

        self.conversation_history = []

        logger.info("Conversation history cleared")

    def get_history_summary(self):

        if not self.conversation_history:
            return ""

        history = self.conversation_history[-4:]

        summary = ""

        for msg in history:

            role = msg["role"].capitalize()

            summary += f"{role}: {msg['content']}\n"

        return summary