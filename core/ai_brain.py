"""
core/ai_brain.py — AI Conversation Engine
──────────────────────────────────────────
This is Nova's "brain". It takes your text command,
sends it to the OpenAI API (with full conversation context),
and returns Nova's response.

MEMORY INTEGRATION:
The brain keeps a running list of messages (conversation_history).
This is the "context window" — it's what makes Nova remember
what you said earlier in a conversation.

FUNCTION CALLING (Phase 2):
In Phase 2, we'll add tool definitions so the AI can
decide which automation module to run (open app, search web, etc.)
For now, the automation module handles this via keyword matching.
"""

from openai import OpenAI
import logging
import json

logger = logging.getLogger(__name__)


class AIBrain:
    """Sends messages to OpenAI and maintains conversation history."""

    def __init__(self, config: dict):
        ai_cfg = config.get("ai", {})
        self.model = ai_cfg.get("model", "gpt-4o-mini")
        self.max_tokens = ai_cfg.get("max_tokens", 800)
        self.temperature = ai_cfg.get("temperature", 0.7)

        personality_cfg = config.get("personality", {})
        self.system_prompt = personality_cfg.get("system_prompt", 
            "You are Nova, a helpful AI assistant for macOS.")
        self.nova_name = personality_cfg.get("name", "Nova")

        memory_cfg = config.get("memory", {})
        self.max_context = memory_cfg.get("max_context_messages", 10)

        # ── Conversation history kept in memory ──────────────────────────
        # Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        self.conversation_history = []

        # ── OpenAI client ─────────────────────────────────────────────────
        # Reads OPENAI_API_KEY from environment automatically
        self.client = OpenAI()

    def think(self, user_message: str, extra_context: str = "") -> str:
        """
        Send a message to the AI and get a response.
        
        Args:
            user_message: What the user said
            extra_context: Optional extra info (e.g., "User asked about a file. 
                          File content: ...") — prepended to the user message.
        
        Returns:
            Nova's text response
        """
        # ── Build the full message content ───────────────────────────────
        content = user_message
        if extra_context:
            content = f"{extra_context}\n\nUser: {user_message}"

        # ── Add user message to history ───────────────────────────────────
        self.conversation_history.append({
            "role": "user",
            "content": content
        })

        # ── Trim history if too long ──────────────────────────────────────
        # Keep only the most recent N messages to avoid token overflow
        if len(self.conversation_history) > self.max_context * 2:
            self.conversation_history = self.conversation_history[-(self.max_context * 2):]

        # ── Build the messages list for the API call ──────────────────────
        # Always start with the system prompt
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history

        # ── Call the OpenAI API ───────────────────────────────────────────
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            reply = response.choices[0].message.content.strip()

            # ── Add Nova's response to history ────────────────────────────
            self.conversation_history.append({
                "role": "assistant",
                "content": reply
            })

            logger.info(f"Nova: '{reply[:80]}...' " if len(reply) > 80 else f"Nova: '{reply}'")
            return reply

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "I'm sorry, I had trouble connecting to my AI. Please check your API key."

    def clear_history(self):
        """Clear conversation history (start fresh)."""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history_summary(self) -> str:
        """Return a short summary of the conversation for memory storage."""
        if not self.conversation_history:
            return ""
        # Just return the last exchange
        recent = self.conversation_history[-2:] if len(self.conversation_history) >= 2 else self.conversation_history
        return json.dumps(recent)
