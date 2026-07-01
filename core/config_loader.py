"""
core/config_loader.py — Configuration Loader
─────────────────────────────────────────────
Loads config.yaml and makes all settings available
as a clean Python dictionary throughout the app.
"""

import yaml
import os


def load_config(config_path: str) -> dict:
    """
    Load and return the configuration from a YAML file.
    Also sets the OpenAI API key as an environment variable
    so the openai library picks it up automatically.
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # ── Set API key as environment variable ──────────────────────────────
    # The openai Python library automatically reads OPENAI_API_KEY
    api_key = config.get("ai", {}).get("openai_api_key", "")
    if api_key and api_key != "sk-YOUR-KEY-HERE":
        os.environ["OPENAI_API_KEY"] = api_key

    elevenlabs_key = config.get("voice", {}).get("elevenlabs_api_key", "")
    if elevenlabs_key:
        os.environ["ELEVENLABS_API_KEY"] = elevenlabs_key

    return config


def get(config: dict, *keys, default=None):
    """
    Safely get a nested config value.
    Example: get(config, "ai", "model") → "gpt-4o-mini"
    """
    val = config
    for key in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(key, default)
        if val is None:
            return default
    return val
