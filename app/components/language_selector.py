"""
language_selector.py
--------------------
Reusable Streamlit component for searchable language selection.

Architecture:
    This module follows a two-layer pattern:
      1. Pure logic functions  — filter_languages, build_display_options,
                                 find_default_index
                                 → independently testable, no Streamlit dependency
      2. Render function       — render_language_selector()
                                 → thin Streamlit wrapper around the pure functions

    main.py calls only render_language_selector() and receives a language dict.
    It never needs to know about search logic, label formatting, or fallback handling.

Usage:
    from app.components.language_selector import render_language_selector

    selected_lang = render_language_selector(engine="gtts", key_prefix="main")
    # Returns e.g. {"code": "hi", "name": "Hindi", "flag": "🇮🇳", ...}
"""

import logging
from typing import Optional

import streamlit as st

from app.utils.language_data import format_display_label, get_all_languages

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure Logic Functions (testable without Streamlit)
# ---------------------------------------------------------------------------

def filter_languages(languages: list[dict], query: str) -> list[dict]:
    """
    Filter a list of language dicts by a search query.

    Matches against: name, native name, and language code (all case-insensitive).
    Returns the full list unchanged if query is empty or whitespace.

    Args:
        languages: Full list of language dicts from the registry.
        query:     User search input string.

    Returns:
        Filtered list. Never empty — falls back to full list if no matches.
    """
    query = query.strip().lower()
    if not query:
        return languages

    matched = [
        lang for lang in languages
        if query in lang["name"].lower()
        or query in lang["native"].lower()
        or query in lang["code"].lower()
    ]

    # Fallback: if nothing matches, return full list to avoid a broken UI
    return matched if matched else languages


def build_display_options(languages: list[dict]) -> list[str]:
    """
    Build formatted display strings for each language in the list.

    Delegates to format_display_label() for consistent formatting across
    all components: "🇮🇳 Hindi (हिन्दी)"

    Args:
        languages: List of language dicts.

    Returns:
        List of formatted display strings, same order as input.
    """
    return [format_display_label(lang) for lang in languages]


def find_default_index(languages: list[dict], default_code: str) -> int:
    """
    Find the index of the default language code in a filtered list.

    If the default code isn't in the filtered list (e.g. user searched
    for something that excludes the default), returns 0 safely.

    Args:
        languages:    Current (possibly filtered) language list.
        default_code: BCP-47 code to look for e.g. "en", "hi".

    Returns:
        Index of the matching language, or 0 if not found.
    """
    for i, lang in enumerate(languages):
        if lang["code"].lower() == default_code.lower():
            return i
    return 0


def get_language_from_label(label: str, languages: list[dict]) -> Optional[dict]:
    """
    Reverse-lookup: given a display label, find the original language dict.

    Args:
        label:     A formatted display string e.g. "🇮🇳 Hindi (हिन्दी)".
        languages: The list of language dicts the label was built from.

    Returns:
        Matching language dict, or None if not found.
    """
    for lang in languages:
        if format_display_label(lang) == label:
            return lang
    return None


# ---------------------------------------------------------------------------
# Streamlit Render Function
# ---------------------------------------------------------------------------

def render_language_selector(
    engine: str = "gtts",
    key_prefix: str = "",
    default_code: str = "en",
    show_region_filter: bool = False,
) -> dict:
    """
    Render a searchable language selector inside the current Streamlit context.

    Displays:
      - A live search text input
      - A match count badge
      - A formatted selectbox with flag + name + native name

    Args:
        engine:            TTS engine to filter by — "gtts" | "elevenlabs".
        key_prefix:        Unique prefix for widget keys (avoids key conflicts
                           when multiple selectors are on the same page).
        default_code:      BCP-47 code pre-selected on first render.
        show_region_filter: If True, adds a region filter dropdown above the search.

    Returns:
        The selected language dict e.g.
        {"code": "hi", "name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳", ...}
    """
    all_languages = get_all_languages(engine=engine)

    # Optional region filter
    if show_region_filter:
        regions = sorted({lang["region"] for lang in all_languages})
        selected_region = st.selectbox(
            "Filter by region",
            options=["All Regions"] + regions,
            key=f"{key_prefix}_region_filter",
            label_visibility="collapsed",
        )
        if selected_region != "All Regions":
            all_languages = [l for l in all_languages if l["region"] == selected_region]

    # Search input
    st.markdown(
        '<p style="color:#A78BFA; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "🌐 Language</p>",
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "Search language",
        placeholder="Search by name, code e.g. 'Hindi', 'fr', '日本語'...",
        key=f"{key_prefix}_lang_search",
        label_visibility="collapsed",
    )

    # Apply filter
    filtered = filter_languages(all_languages, search_query)

    # Match count feedback
    total = len(all_languages)
    matched = len(filtered)
    if search_query.strip():
        badge_color = "#10B981" if matched > 0 else "#EF4444"
        st.markdown(
            f'<p style="color:{badge_color}; font-size:0.75rem; margin-top:-8px;">'
            f"{'✓' if matched > 0 else '✗'} {matched} of {total} languages matched</p>",
            unsafe_allow_html=True,
        )

    # Build display options and find default
    display_options = build_display_options(filtered)
    default_idx = find_default_index(filtered, default_code)

    selected_label = st.selectbox(
        "Select Language",
        options=display_options,
        index=default_idx,
        key=f"{key_prefix}_lang_select",
        label_visibility="collapsed",
    )

    # Resolve label back to the language dict
    selected_lang = get_language_from_label(selected_label, filtered)

    # Defensive fallback — should never be None in practice
    if selected_lang is None:
        logger.warning(
            "Could not resolve label '%s' to a language. Falling back to first.",
            selected_label,
        )
        selected_lang = filtered[0]

    return selected_lang
