"""
language_data.py
----------------
Language registry loader and query interface.

Provides functions to load, search, and filter languages from the
central `languages.json` config file. All other modules should
consume languages through this interface — never read the JSON directly.
"""

import json
from pathlib import Path
from typing import Optional

# Resolve path relative to this file so it works from any working directory
_LANGUAGES_FILE = Path(__file__).parent.parent / "config" / "languages.json"


def load_languages() -> list[dict]:
    """
    Load the full language list from the JSON registry.

    Returns:
        List of language dicts, each containing:
            code, name, native, flag, region,
            gtts_supported, elevenlabs_supported
    """
    with open(_LANGUAGES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["languages"]


def get_all_languages(engine: Optional[str] = None) -> list[dict]:
    """
    Return all languages, optionally filtered by TTS engine support.

    Args:
        engine: "gtts" | "elevenlabs" | None (returns all)

    Returns:
        Filtered list of language dicts.
    """
    languages = load_languages()

    if engine == "gtts":
        return [lang for lang in languages if lang.get("gtts_supported")]
    elif engine == "elevenlabs":
        return [lang for lang in languages if lang.get("elevenlabs_supported")]

    return languages


def search_languages(query: str, engine: Optional[str] = None) -> list[dict]:
    """
    Search languages by name, native name, or language code.

    Args:
        query:  Search string (case-insensitive).
        engine: Optional engine filter ("gtts" | "elevenlabs").

    Returns:
        List of matching language dicts.
    """
    query = query.strip().lower()
    languages = get_all_languages(engine=engine)

    if not query:
        return languages

    return [
        lang for lang in languages
        if query in lang["name"].lower()
        or query in lang["native"].lower()
        or query in lang["code"].lower()
    ]


def get_language_by_code(code: str) -> Optional[dict]:
    """
    Fetch a single language entry by its BCP-47 code.

    Args:
        code: Language code e.g. "en", "hi", "zh-CN"

    Returns:
        Language dict if found, else None.
    """
    languages = load_languages()
    for lang in languages:
        if lang["code"].lower() == code.lower():
            return lang
    return None


def get_regions() -> list[str]:
    """
    Return a sorted, deduplicated list of all regions in the registry.
    Useful for building region-filter dropdowns in the UI.
    """
    languages = load_languages()
    regions = sorted({lang["region"] for lang in languages})
    return regions


def get_languages_by_region(region: str, engine: Optional[str] = None) -> list[dict]:
    """
    Return languages for a specific region, optionally filtered by engine.

    Args:
        region: Region name e.g. "Asia", "Europe".
        engine: Optional engine filter.

    Returns:
        Filtered list of language dicts.
    """
    languages = get_all_languages(engine=engine)
    return [lang for lang in languages if lang["region"] == region]


def format_display_label(lang: dict) -> str:
    """
    Format a language entry as a human-readable display label for UI dropdowns.

    Example: "🇮🇳 Hindi (हिन्दी)"

    Args:
        lang: A language dict from the registry.

    Returns:
        Formatted display string.
    """
    return f"{lang['flag']} {lang['name']} ({lang['native']})"
