"""
core/memory.py — Persistent Memory System
──────────────────────────────────────────
Stores Nova's memories in a SQLite database so she can
remember things across conversations and sessions.

WHAT GETS STORED:
- Conversation history (recent exchanges)
- User preferences ("I prefer dark mode", "My name is Rahul")
- Frequently used apps and commands
- Study subjects and notes

SQLite is perfect here because:
- It's built into Python (no server needed)
- Fast for small/medium datasets
- The database is just a single file
"""

import sqlite3
import json
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


class Memory:
    """Persistent memory for Nova using SQLite."""

    def __init__(self, config: dict):
        memory_cfg = config.get("memory", {})
        db_path = memory_cfg.get("db_path", "data/nova_memory.db")

        # Create the data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._init_database()
        logger.info(f"Memory initialized at: {db_path}")

    def _init_database(self):
        """Create database tables if they don't exist yet."""
        with self._connect() as conn:
            conn.executescript("""
                -- Conversation history table
                -- Stores each message Nova sends and receives
                CREATE TABLE IF NOT EXISTS conversations (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    role        TEXT NOT NULL,      -- "user" or "assistant"
                    content     TEXT NOT NULL,
                    timestamp   TEXT NOT NULL,
                    session_id  TEXT
                );

                -- User preferences table  
                -- Stores key-value facts about the user
                CREATE TABLE IF NOT EXISTS preferences (
                    key         TEXT PRIMARY KEY,
                    value       TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                );

                -- App usage tracking
                -- Nova learns which apps you use most often
                CREATE TABLE IF NOT EXISTS app_usage (
                    app_name    TEXT PRIMARY KEY,
                    open_count  INTEGER DEFAULT 1,
                    last_used   TEXT NOT NULL
                );

                -- General facts and notes
                CREATE TABLE IF NOT EXISTS facts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    category    TEXT NOT NULL,  -- e.g., "study", "reminder", "preference"
                    content     TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                );
            """)
        logger.debug("Database tables initialized")

    def _connect(self):
        """Create and return a database connection."""
        return sqlite3.connect(self.db_path)

    # ────────────────────────────────────────────────────────────────────────
    # Conversation History
    # ────────────────────────────────────────────────────────────────────────

    def save_message(self, role: str, content: str, session_id: str = "default"):
        """Save a single message (user or Nova) to the database."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO conversations (role, content, timestamp, session_id) VALUES (?, ?, ?, ?)",
                (role, content, datetime.now().isoformat(), session_id)
            )

    def get_recent_messages(self, limit: int = 10, session_id: str = None) -> List[Dict]:
        """
        Get the most recent messages from the database.
        Returns them in the format OpenAI expects.
        """
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT role, content FROM conversations WHERE session_id=? ORDER BY id DESC LIMIT ?",
                    (session_id, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT role, content FROM conversations ORDER BY id DESC LIMIT ?",
                    (limit,)
                ).fetchall()

        # Reverse so they're in chronological order
        rows.reverse()
        return [{"role": row[0], "content": row[1]} for row in rows]

    # ────────────────────────────────────────────────────────────────────────
    # User Preferences
    # ────────────────────────────────────────────────────────────────────────

    def set_preference(self, key: str, value: str):
        """Store a user preference (e.g., 'name' = 'Rahul')."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO preferences (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )

    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get a stored preference by key."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM preferences WHERE key=?", (key,)
            ).fetchone()
        return row[0] if row else default

    def get_all_preferences(self) -> Dict[str, str]:
        """Get all stored preferences as a dictionary."""
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM preferences").fetchall()
        return {row[0]: row[1] for row in rows}

    # ────────────────────────────────────────────────────────────────────────
    # App Usage Tracking
    # ────────────────────────────────────────────────────────────────────────

    def record_app_open(self, app_name: str):
        """Track that the user opened an app."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO app_usage (app_name, open_count, last_used)
                VALUES (?, 1, ?)
                ON CONFLICT(app_name) DO UPDATE SET
                    open_count = open_count + 1,
                    last_used = excluded.last_used
            """, (app_name, datetime.now().isoformat()))

    def get_frequent_apps(self, limit: int = 5) -> List[str]:
        """Get the most frequently opened apps."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT app_name FROM app_usage ORDER BY open_count DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [row[0] for row in rows]

    # ────────────────────────────────────────────────────────────────────────
    # General Facts
    # ────────────────────────────────────────────────────────────────────────

    def save_fact(self, category: str, content: str):
        """Save a general fact or note."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO facts (category, content, created_at) VALUES (?, ?, ?)",
                (category, content, datetime.now().isoformat())
            )

    def get_facts(self, category: str = None, limit: int = 10) -> List[str]:
        """Get stored facts, optionally filtered by category."""
        with self._connect() as conn:
            if category:
                rows = conn.execute(
                    "SELECT content FROM facts WHERE category=? ORDER BY id DESC LIMIT ?",
                    (category, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT content FROM facts ORDER BY id DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [row[0] for row in rows]
