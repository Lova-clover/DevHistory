"""Configuration utilities."""
import os


def get_settings():
    """Get common settings from environment variables."""
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    }
