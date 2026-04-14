"""
test_language_selector.py
--------------------------
Unit tests for the pure logic functions in
app/components/language_selector.py

Only the non-Streamlit functions are tested here:
  - filter_languages
  - build_display_options
  - find_default_index
  - get_language_from_label

The render_language_selector() function is tested via the running app.
"""

import pytest

from app.components.language_selector import (
    build_display_options,
    filter_languages,
    find_default_index,
    get_language_from_label,
)
from app.utils.language_data import get_all_languages, format_display_label


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def all_langs():
    """Full list of gTTS-supported languages from registry."""
    return get_all_languages(engine="gtts")


@pytest.fixture
def sample_langs():
    """Small deterministic list for focused testing."""
    return [
        {"code": "en", "name": "English", "native": "English", "flag": "🇺🇸", "region": "Americas"},
        {"code": "hi", "name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳", "region": "Asia"},
        {"code": "fr", "name": "French", "native": "Français", "flag": "🇫🇷", "region": "Europe"},
        {"code": "ja", "name": "Japanese", "native": "日本語", "flag": "🇯🇵", "region": "Asia"},
        {"code": "zh-CN", "name": "Chinese (Simplified)", "native": "中文(简体)", "flag": "🇨🇳", "region": "Asia"},
    ]


# ---------------------------------------------------------------------------
# filter_languages
# ---------------------------------------------------------------------------

class TestFilterLanguages:
    def test_empty_query_returns_all(self, sample_langs):
        result = filter_languages(sample_langs, "")
        assert result == sample_langs

    def test_whitespace_query_returns_all(self, sample_langs):
        result = filter_languages(sample_langs, "   ")
        assert result == sample_langs

    def test_match_by_name(self, sample_langs):
        result = filter_languages(sample_langs, "French")
        assert len(result) == 1
        assert result[0]["code"] == "fr"

    def test_match_by_native_name(self, sample_langs):
        result = filter_languages(sample_langs, "हिन्दी")
        assert any(l["code"] == "hi" for l in result)

    def test_match_by_code(self, sample_langs):
        result = filter_languages(sample_langs, "zh-CN")
        assert any(l["code"] == "zh-CN" for l in result)

    def test_case_insensitive_match(self, sample_langs):
        result_lower = filter_languages(sample_langs, "french")
        result_upper = filter_languages(sample_langs, "FRENCH")
        assert len(result_lower) == len(result_upper)

    def test_partial_match(self, sample_langs):
        result = filter_languages(sample_langs, "eng")
        assert any(l["code"] == "en" for l in result)

    def test_no_match_falls_back_to_full_list(self, sample_langs):
        result = filter_languages(sample_langs, "xyzzy_no_match")
        # Fallback: returns full list instead of empty
        assert result == sample_langs

    def test_multi_match(self, sample_langs):
        # "a" matches English, French, Japanese, Chinese
        result = filter_languages(sample_langs, "a")
        assert len(result) > 1

    def test_full_registry_filters_correctly(self, all_langs):
        result = filter_languages(all_langs, "hindi")
        assert any(l["code"] == "hi" for l in result)


# ---------------------------------------------------------------------------
# build_display_options
# ---------------------------------------------------------------------------

class TestBuildDisplayOptions:
    def test_returns_list_of_strings(self, sample_langs):
        options = build_display_options(sample_langs)
        assert all(isinstance(o, str) for o in options)

    def test_same_length_as_input(self, sample_langs):
        options = build_display_options(sample_langs)
        assert len(options) == len(sample_langs)

    def test_contains_flag_name_and_native(self, sample_langs):
        options = build_display_options(sample_langs)
        hindi_option = next(o for o in options if "Hindi" in o)
        assert "🇮🇳" in hindi_option
        assert "हिन्दी" in hindi_option

    def test_empty_list_returns_empty(self):
        assert build_display_options([]) == []

    def test_matches_format_display_label(self, sample_langs):
        options = build_display_options(sample_langs)
        for lang, option in zip(sample_langs, options):
            assert option == format_display_label(lang)


# ---------------------------------------------------------------------------
# find_default_index
# ---------------------------------------------------------------------------

class TestFindDefaultIndex:
    def test_finds_correct_index(self, sample_langs):
        idx = find_default_index(sample_langs, "hi")
        assert idx == 1

    def test_case_insensitive(self, sample_langs):
        idx = find_default_index(sample_langs, "HI")
        assert idx == 1

    def test_first_item_index(self, sample_langs):
        idx = find_default_index(sample_langs, "en")
        assert idx == 0

    def test_last_item_index(self, sample_langs):
        idx = find_default_index(sample_langs, "zh-CN")
        assert idx == 4

    def test_missing_code_returns_zero(self, sample_langs):
        idx = find_default_index(sample_langs, "xx-NOTFOUND")
        assert idx == 0

    def test_empty_list_returns_zero(self):
        idx = find_default_index([], "en")
        assert idx == 0


# ---------------------------------------------------------------------------
# get_language_from_label
# ---------------------------------------------------------------------------

class TestGetLanguageFromLabel:
    def test_resolves_label_to_dict(self, sample_langs):
        label = format_display_label(sample_langs[0])  # English
        result = get_language_from_label(label, sample_langs)
        assert result is not None
        assert result["code"] == "en"

    def test_resolves_hindi_label(self, sample_langs):
        hi = next(l for l in sample_langs if l["code"] == "hi")
        label = format_display_label(hi)
        result = get_language_from_label(label, sample_langs)
        assert result["code"] == "hi"

    def test_unknown_label_returns_none(self, sample_langs):
        result = get_language_from_label("🏴 Klingon (tlhIngan Hol)", sample_langs)
        assert result is None

    def test_roundtrip_all_languages(self, sample_langs):
        """Every label built from the list must resolve back to the correct dict."""
        for lang in sample_langs:
            label = format_display_label(lang)
            resolved = get_language_from_label(label, sample_langs)
            assert resolved is not None
            assert resolved["code"] == lang["code"]
