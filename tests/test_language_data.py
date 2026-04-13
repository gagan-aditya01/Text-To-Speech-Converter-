"""
test_language_data.py
---------------------
Unit tests for app/utils/language_data.py
"""

import pytest
from app.utils.language_data import (
    load_languages,
    get_all_languages,
    search_languages,
    get_language_by_code,
    get_regions,
    get_languages_by_region,
    format_display_label,
)


class TestLoadLanguages:
    def test_returns_non_empty_list(self):
        languages = load_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0

    def test_each_entry_has_required_keys(self):
        required_keys = {"code", "name", "native", "flag", "region",
                         "gtts_supported", "elevenlabs_supported"}
        for lang in load_languages():
            assert required_keys.issubset(lang.keys()), (
                f"Language entry missing keys: {lang}"
            )


class TestGetAllLanguages:
    def test_no_filter_returns_all(self):
        all_langs = get_all_languages()
        assert len(all_langs) >= 50

    def test_gtts_filter_only_returns_supported(self):
        langs = get_all_languages(engine="gtts")
        assert all(lang["gtts_supported"] for lang in langs)

    def test_elevenlabs_filter_only_returns_supported(self):
        langs = get_all_languages(engine="elevenlabs")
        assert all(lang["elevenlabs_supported"] for lang in langs)

    def test_unknown_engine_returns_empty_or_all(self):
        # Unknown engine should not raise — returns all
        langs = get_all_languages(engine=None)
        assert len(langs) > 0


class TestSearchLanguages:
    def test_exact_name_match(self):
        results = search_languages("Hindi")
        codes = [r["code"] for r in results]
        assert "hi" in codes

    def test_partial_name_match(self):
        results = search_languages("eng")
        assert len(results) > 0

    def test_native_name_match(self):
        results = search_languages("हिन्दी")
        assert any(r["code"] == "hi" for r in results)

    def test_code_match(self):
        results = search_languages("zh-CN")
        assert any(r["code"] == "zh-CN" for r in results)

    def test_empty_query_returns_all(self):
        all_langs = get_all_languages()
        results = search_languages("")
        assert len(results) == len(all_langs)

    def test_no_match_returns_empty(self):
        results = search_languages("xxxxxx_no_match")
        assert results == []

    def test_case_insensitive(self):
        lower = search_languages("french")
        upper = search_languages("FRENCH")
        assert len(lower) == len(upper)


class TestGetLanguageByCode:
    def test_known_code_returns_dict(self):
        lang = get_language_by_code("en")
        assert lang is not None
        assert lang["name"] == "English"

    def test_case_insensitive_lookup(self):
        lang = get_language_by_code("HI")
        assert lang is not None
        assert lang["code"] == "hi"

    def test_unknown_code_returns_none(self):
        lang = get_language_by_code("xx-INVALID")
        assert lang is None


class TestGetRegions:
    def test_returns_sorted_list(self):
        regions = get_regions()
        assert regions == sorted(regions)

    def test_contains_expected_regions(self):
        regions = get_regions()
        for expected in ["Asia", "Europe", "Americas"]:
            assert expected in regions


class TestGetLanguagesByRegion:
    def test_asia_returns_indian_languages(self):
        langs = get_languages_by_region("Asia")
        codes = [l["code"] for l in langs]
        assert "hi" in codes
        assert "ja" in codes

    def test_unknown_region_returns_empty(self):
        langs = get_languages_by_region("Atlantis")
        assert langs == []


class TestFormatDisplayLabel:
    def test_format_contains_flag_name_and_native(self):
        lang = get_language_by_code("hi")
        label = format_display_label(lang)
        assert "🇮🇳" in label
        assert "Hindi" in label
        assert "हिन्दी" in label
