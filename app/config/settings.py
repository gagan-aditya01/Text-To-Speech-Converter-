"""
settings.py
-----------
Centralized application configuration.

Loads environment variables from a .env file (if present) and
exposes them as a typed, validated `Settings` dataclass.

All modules that need configuration should import the `settings`
singleton from this module — never call os.getenv() directly elsewhere.

Usage:
    from app.config.settings import settings

    engine = settings.TTS_ENGINE
    out_dir = settings.OUTPUT_DIR
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Resolve .env relative to project root (3 levels up from this file)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DOTENV_PATH = _PROJECT_ROOT / ".env"

# Load .env if it exists — silently skip if absent (e.g. in CI/CD)
# override=False means real environment variables always take precedence
load_dotenv(dotenv_path=_DOTENV_PATH, override=False)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid values — used for validation and UI dropdowns
# ---------------------------------------------------------------------------

VALID_TTS_ENGINES = frozenset({"gtts", "elevenlabs"})
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
VALID_VOICE_GENDERS = frozenset({"male", "female", "neutral"})
VALID_MOODS = frozenset({"neutral", "calm", "energetic", "formal"})


@dataclass
class Settings:
    """
    Application-wide configuration loaded from environment variables.

    All fields have safe defaults so the app runs out-of-the-box
    without a .env file (except for API-key-dependent features).

    Attributes:
        TTS_ENGINE:          Active TTS engine. "gtts" | "elevenlabs".
        DEFAULT_LANGUAGE:    Default BCP-47 language code shown in the UI.
        DEFAULT_GENDER:      Default voice gender preference.
        DEFAULT_MOOD:        Default mood/tone preference.
        OUTPUT_DIR:          Directory where generated audio files are saved.
        MAX_OUTPUT_FILES:    Maximum number of audio files to retain on disk.
        LOG_LEVEL:           Python logging level string.
        ELEVENLABS_API_KEY:  ElevenLabs API key (None if not configured).
        MAX_TEXT_LENGTH:     Maximum characters accepted in a single TTS request.
    """

    TTS_ENGINE: str = field(default_factory=lambda: os.getenv("TTS_ENGINE", "gtts").lower())
    DEFAULT_LANGUAGE: str = field(default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "en"))
    DEFAULT_GENDER: str = field(default_factory=lambda: os.getenv("DEFAULT_GENDER", "female").lower())
    DEFAULT_MOOD: str = field(default_factory=lambda: os.getenv("DEFAULT_MOOD", "neutral").lower())
    OUTPUT_DIR: Path = field(default_factory=lambda: Path(os.getenv("OUTPUT_DIR", "outputs")))
    MAX_OUTPUT_FILES: int = field(default_factory=lambda: int(os.getenv("MAX_OUTPUT_FILES", "50")))
    LOG_LEVEL: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())
    ELEVENLABS_API_KEY: Optional[str] = field(default_factory=lambda: os.getenv("ELEVENLABS_API_KEY"))
    MAX_TEXT_LENGTH: int = field(default_factory=lambda: int(os.getenv("MAX_TEXT_LENGTH", "5000")))

    def __post_init__(self):
        """Validate all settings immediately on construction."""
        if self.TTS_ENGINE not in VALID_TTS_ENGINES:
            raise ValueError(
                f"Invalid TTS_ENGINE '{self.TTS_ENGINE}'. "
                f"Must be one of: {sorted(VALID_TTS_ENGINES)}"
            )
        if self.LOG_LEVEL not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid LOG_LEVEL '{self.LOG_LEVEL}'. "
                f"Must be one of: {sorted(VALID_LOG_LEVELS)}"
            )
        if self.DEFAULT_GENDER not in VALID_VOICE_GENDERS:
            raise ValueError(
                f"Invalid DEFAULT_GENDER '{self.DEFAULT_GENDER}'. "
                f"Must be one of: {sorted(VALID_VOICE_GENDERS)}"
            )
        if self.DEFAULT_MOOD not in VALID_MOODS:
            raise ValueError(
                f"Invalid DEFAULT_MOOD '{self.DEFAULT_MOOD}'. "
                f"Must be one of: {sorted(VALID_MOODS)}"
            )
        if self.MAX_OUTPUT_FILES < 1:
            raise ValueError("MAX_OUTPUT_FILES must be at least 1.")
        if self.MAX_TEXT_LENGTH < 1:
            raise ValueError("MAX_TEXT_LENGTH must be at least 1.")

        # Warn (don't error) if premium engine is selected without an API key
        if self.TTS_ENGINE == "elevenlabs" and not self.ELEVENLABS_API_KEY:
            logger.warning(
                "TTS_ENGINE is set to 'elevenlabs' but ELEVENLABS_API_KEY is not configured. "
                "Synthesis calls will fail. Set the key in your .env file."
            )

    @property
    def elevenlabs_configured(self) -> bool:
        """True if ElevenLabs API key is present and non-empty."""
        return bool(self.ELEVENLABS_API_KEY)

    def __repr__(self) -> str:
        # Never expose the API key in repr/logs
        return (
            f"Settings(engine={self.TTS_ENGINE!r}, lang={self.DEFAULT_LANGUAGE!r}, "
            f"log={self.LOG_LEVEL!r}, elevenlabs_configured={self.elevenlabs_configured})"
        )


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere
# ---------------------------------------------------------------------------

settings = Settings()
