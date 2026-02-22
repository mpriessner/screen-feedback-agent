"""Configuration management."""

import os
from pathlib import Path

import yaml


CONFIG_DIR = Path.home() / ".config" / "sfa"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def get_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def set_config(key: str, value: str) -> None:
    """Set a configuration value."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    
    config = get_config()
    config[key] = value
    
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f)
    
    # Also set as environment variable for current session
    os.environ[key.upper()] = value


def get_api_key() -> str | None:
    """Get Gemini API key from config or environment."""
    # Environment takes precedence
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    
    # Fall back to config file
    config = get_config()
    return config.get("gemini_api_key")
