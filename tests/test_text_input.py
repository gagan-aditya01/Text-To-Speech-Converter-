"""
test_text_input.py
------------------
Unit tests for the pure logic functions in app/components/text_input.py

Tests cover: validate_text, get_counter_color, count_words,
             is_rtl_language, get_placeholder_text, get_char_stats.

The render_text_input() Streamlit function is excluded from unit tests
(tested via the live app).
"""

import pytest

from app.components.text_input import (
    count_words,
    get_char_stats,
    get_counter_color,
    get_placeholder_text,
    is_rtl_language,
    validate_text,
)


# ---------------------------------------------------------------------------
# validate_text
# ---------------------------------------------------------------------------

class TestValidateText:
    def test_valid_text_returns_true(self):
        is_valid, msg = validate_text("Hello, world!", 5000)
        assert is_valid is True
        assert msg == ""

    def test_empty_string_is_invalid(self):
        is_valid, msg = validate_text("", 5000)
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_whitespace_only_is_invalid(self):
        is_valid, msg = validate_text("   \n\t  ", 5000)
        assert is_valid is False
        assert "empty" in msg.lower()

    def test_single_char_is_too_short(self):
        is_valid, msg = validate_text("a", 5000)
        assert is_valid is False
        assert "short" in msg.lower()

    def test_two_chars_is_valid(self):
        is_valid, msg = validate_text("hi", 5000)
        assert is_valid is True

    def test_text_exceeding_limit_is_invalid(self):
        long_text = "a" * 5001
        is_valid, msg = validate_text(long_text, 5000)
        assert is_valid is False
        assert "5,000" in msg or "5000" in msg

    def test_text_exactly_at_limit_is_valid(self):
        text = "a" * 5000
        is_valid, _ = validate_text(text, 5000)
        assert is_valid is True

    def test_custom_max_length(self):
        is_valid, msg = validate_text("Hello!", max_length=3)
        assert is_valid is False  # "Hello!" is 6 chars > 3

    def test_unicode_text_is_valid(self):
        is_valid, _ = validate_text("नमस्ते दुनिया", 5000)
        assert is_valid is True

    def test_hindi_text_is_valid(self):
        is_valid, _ = validate_text("हिन्दी में आवाज़ परीक्षण", 5000)
        assert is_valid is True


# ---------------------------------------------------------------------------
# get_counter_color
# ---------------------------------------------------------------------------

class TestGetCounterColor:
    def test_zero_chars_is_grey(self):
        assert get_counter_color(0, 5000) == "#94A3B8"

    def test_below_70_percent_is_grey(self):
        assert get_counter_color(3000, 5000) == "#94A3B8"  # 60%

    def test_just_above_70_percent_is_amber(self):
        # ratio > 0.7 (strict) — exactly 70% is still grey, 70.1% triggers amber
        assert get_counter_color(3501, 5000) == "#F59E0B"  # ~70.02%

    def test_between_70_and_90_is_amber(self):
        assert get_counter_color(4000, 5000) == "#F59E0B"  # 80%

    def test_above_90_percent_is_red(self):
        assert get_counter_color(4600, 5000) == "#EF4444"  # 92%

    def test_at_100_percent_is_red(self):
        assert get_counter_color(5000, 5000) == "#EF4444"

    def test_over_limit_is_red(self):
        assert get_counter_color(6000, 5000) == "#EF4444"

    def test_zero_max_length_returns_grey(self):
        # Guard against division by zero
        assert get_counter_color(100, 0) == "#94A3B8"


# ---------------------------------------------------------------------------
# count_words
# ---------------------------------------------------------------------------

class TestCountWords:
    def test_empty_string_returns_zero(self):
        assert count_words("") == 0

    def test_whitespace_only_returns_zero(self):
        assert count_words("   ") == 0

    def test_single_word(self):
        assert count_words("Hello") == 1

    def test_multiple_words(self):
        assert count_words("Hello world foo bar") == 4

    def test_extra_spaces_are_ignored(self):
        assert count_words("Hello   world") == 2

    def test_newlines_count_as_separators(self):
        assert count_words("Hello\nworld\nfoo") == 3

    def test_hindi_text(self):
        assert count_words("नमस्ते दुनिया") == 2

    def test_mixed_languages(self):
        assert count_words("Hello नमस्ते Bonjour") == 3


# ---------------------------------------------------------------------------
# is_rtl_language
# ---------------------------------------------------------------------------

class TestIsRtlLanguage:
    def test_arabic_is_rtl(self):
        assert is_rtl_language("ar") is True

    def test_hebrew_iw_is_rtl(self):
        assert is_rtl_language("iw") is True

    def test_hebrew_he_is_rtl(self):
        assert is_rtl_language("he") is True

    def test_persian_is_rtl(self):
        assert is_rtl_language("fa") is True

    def test_urdu_is_rtl(self):
        assert is_rtl_language("ur") is True

    def test_english_is_not_rtl(self):
        assert is_rtl_language("en") is False

    def test_hindi_is_not_rtl(self):
        assert is_rtl_language("hi") is False

    def test_french_is_not_rtl(self):
        assert is_rtl_language("fr") is False

    def test_japanese_is_not_rtl(self):
        assert is_rtl_language("ja") is False

    def test_uppercase_code_handled(self):
        assert is_rtl_language("AR") is True

    def test_unknown_code_is_not_rtl(self):
        assert is_rtl_language("xx-UNKNOWN") is False


# ---------------------------------------------------------------------------
# get_placeholder_text
# ---------------------------------------------------------------------------

class TestGetPlaceholderText:
    def test_english_placeholder(self):
        placeholder = get_placeholder_text("en")
        assert "Type" in placeholder or "paste" in placeholder.lower()

    def test_hindi_placeholder_is_non_empty(self):
        placeholder = get_placeholder_text("hi")
        assert len(placeholder) > 0
        # Should contain Devanagari characters
        assert any("\u0900" <= c <= "\u097F" for c in placeholder)

    def test_arabic_placeholder_is_non_empty(self):
        placeholder = get_placeholder_text("ar")
        assert len(placeholder) > 0

    def test_unknown_lang_returns_default(self):
        placeholder = get_placeholder_text("xx-UNKNOWN")
        assert "Type" in placeholder or "paste" in placeholder.lower()

    def test_japanese_placeholder(self):
        placeholder = get_placeholder_text("ja")
        assert len(placeholder) > 0

    def test_returns_string(self):
        assert isinstance(get_placeholder_text("fr"), str)


# ---------------------------------------------------------------------------
# get_char_stats
# ---------------------------------------------------------------------------

class TestGetCharStats:
    def test_empty_text_stats(self):
        stats = get_char_stats("", 5000)
        assert stats["char_count"] == 0
        assert stats["word_count"] == 0
        assert stats["remaining"] == 5000
        assert stats["pct_used"] == 0.0

    def test_char_count_matches_text_length(self):
        text = "Hello world"
        stats = get_char_stats(text, 5000)
        assert stats["char_count"] == len(text)

    def test_word_count_computed(self):
        stats = get_char_stats("Hello world foo", 5000)
        assert stats["word_count"] == 3

    def test_remaining_computed(self):
        stats = get_char_stats("Hello", 5000)
        assert stats["remaining"] == 4995

    def test_color_reflects_usage(self):
        # Under 70% → grey
        stats = get_char_stats("a" * 100, 5000)
        assert stats["color"] == "#94A3B8"

    def test_pct_used_computed(self):
        stats = get_char_stats("a" * 2500, 5000)
        assert stats["pct_used"] == 50.0

    def test_all_expected_keys_present(self):
        stats = get_char_stats("test", 5000)
        for key in ("char_count", "word_count", "remaining", "color", "pct_used"):
            assert key in stats
