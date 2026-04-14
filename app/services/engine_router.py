"""
engine_router.py
----------------
Factory module for TTS engine selection.

Decouples the Streamlit UI and all components from concrete engine classes.
The engine is selected via settings.TTS_ENGINE (or .env), never hardcoded.

Usage:
    from app.services.engine_router import get_tts_service

    service = get_tts_service()                  # uses settings.TTS_ENGINE
    service = get_tts_service(engine="elevenlabs") # explicit override (e.g. tests)

Adding a new engine:
    1. Create app/services/my_engine_service.py implementing BaseTTSService.
    2. Add it to _ENGINE_REGISTRY below.
    That's it — the UI, router, and tests all pick it up automatically.
"""

import logging
from typing import Optional

from app.config.settings import settings
from app.services.base_tts import BaseTTSService
from app.services.gtts_service import GTTSService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine Registry
# ---------------------------------------------------------------------------

# Lazily imported to avoid hard dependency on elevenlabs when not configured.
# Each value is a zero-argument factory that returns a BaseTTSService instance.
# This pattern keeps the registry lightweight — engines are only instantiated
# on first call to get_tts_service().

def _make_gtts() -> GTTSService:
    return GTTSService()


def _make_elevenlabs() -> "ElevenLabsService":           # noqa: F821 — lazy import
    from app.services.elevenlabs_service import ElevenLabsService
    return ElevenLabsService()


# Registry: engine_name → factory function
_ENGINE_REGISTRY: dict[str, callable] = {
    "gtts":       _make_gtts,
    "elevenlabs": _make_elevenlabs,
}


# ---------------------------------------------------------------------------
# Pure helpers (testable without Streamlit)
# ---------------------------------------------------------------------------

def get_available_engines() -> list[str]:
    """
    Return the list of all registered engine names.

    Engine availability does NOT mean the engine is configured — e.g.
    ElevenLabs is listed here even if no API key is set.

    Returns:
        Sorted list of engine identifiers e.g. ["elevenlabs", "gtts"].
    """
    return sorted(_ENGINE_REGISTRY.keys())


def validate_engine(engine: str) -> bool:
    """
    Check whether an engine name is in the registry.

    Args:
        engine: Engine name string (case-insensitive).

    Returns:
        True if the engine is registered, False otherwise.
    """
    return engine.lower() in _ENGINE_REGISTRY


def resolve_engine_name(engine: Optional[str]) -> str:
    """
    Resolve the engine name to use, falling back to settings.

    Args:
        engine: Explicit engine override string, or None.

    Returns:
        Canonical lowercase engine name.

    Raises:
        ValueError: If the resolved name is not in the registry.
    """
    name = (engine or settings.TTS_ENGINE).strip().lower()
    if not validate_engine(name):
        raise ValueError(
            f"Unknown TTS engine '{name}'. "
            f"Available: {get_available_engines()}"
        )
    return name


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def get_tts_service(engine: Optional[str] = None) -> BaseTTSService:
    """
    Instantiate and return the correct TTS engine.

    Args:
        engine: Override the engine name. If None, uses settings.TTS_ENGINE.
                Accepted values: "gtts", "elevenlabs".

    Returns:
        A concrete BaseTTSService instance.

    Raises:
        ValueError: If the engine name is unknown.

    Examples:
        service = get_tts_service()               # from settings
        service = get_tts_service("gtts")         # explicit
        service = get_tts_service("elevenlabs")   # requires ELEVENLABS_API_KEY
    """
    name = resolve_engine_name(engine)
    factory = _ENGINE_REGISTRY[name]

    logger.info("Initialising TTS engine: %s", name)
    return factory()
