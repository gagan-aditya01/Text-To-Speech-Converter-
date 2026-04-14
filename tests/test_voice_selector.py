"""
test_voice_selector.py
----------------------
Unit tests for pure logic functions in app/components/voice_selector.py

Tests cover: get_all_moods, filter_moods, get_speed_label, get_mood_emoji,
             build_voice_config, validate_voice_config,
             get_mood_display_options, resolve_mood_from_display.
"""

import pytest

from app.components.voice_selector import (
    build_voice_config,
    filter_moods,
    get_all_moods,
    get_mood_display_options,
    get_mood_emoji,
    get_speed_label,
    resolve_mood_from_display,
    validate_voice_config,
)


# ---------------------------------------------------------------------------
# get_all_moods
# ---------------------------------------------------------------------------

class TestGetAllMoods:
    def test_returns_list(self):
        moods = get_all_moods()
        assert isinstance(moods, list)
        assert len(moods) > 0

    def test_gtts_moods_returned_by_default(self):
        moods = get_all_moods(engine="gtts")
        assert all("gtts" in m["engines"] for m in moods)

    def test_elevenlabs_moods(self):
        moods = get_all_moods(engine="elevenlabs")
        assert all("elevenlabs" in m["engines"] for m in moods)

    def test_all_engine_returns_all(self):
        all_moods = get_all_moods(engine="all")
        assert len(all_moods) >= 4  # neutral, calm, formal, energetic

    def test_each_mood_has_required_keys(self):
        for mood in get_all_moods():
            for key in ("id", "label", "emoji", "description", "engines"):
                assert key in mood

    def test_known_moods_present(self):
        ids = [m["id"] for m in get_all_moods()]
        for expected in ("neutral", "calm", "formal", "energetic"):
            assert expected in ids


# ---------------------------------------------------------------------------
# filter_moods
# ---------------------------------------------------------------------------

class TestFilterMoods:
    def setup_method(self):
        self.moods = get_all_moods()

    def test_empty_query_returns_all(self):
        result = filter_moods(self.moods, "")
        assert result == self.moods

    def test_whitespace_returns_all(self):
        result = filter_moods(self.moods, "   ")
        assert result == self.moods

    def test_match_by_label(self):
        result = filter_moods(self.moods, "calm")
        assert any(m["id"] == "calm" for m in result)

    def test_match_by_description(self):
        result = filter_moods(self.moods, "meditation")
        assert any(m["id"] == "calm" for m in result)

    def test_match_by_id(self):
        result = filter_moods(self.moods, "energetic")
        assert any(m["id"] == "energetic" for m in result)

    def test_case_insensitive(self):
        lower = filter_moods(self.moods, "calm")
        upper = filter_moods(self.moods, "CALM")
        assert len(lower) == len(upper)

    def test_no_match_falls_back_to_full_list(self):
        result = filter_moods(self.moods, "xyzzy_no_match")
        assert result == self.moods

    def test_partial_match(self):
        result = filter_moods(self.moods, "ner")  # matches "energetic"
        assert len(result) >= 1


# ---------------------------------------------------------------------------
# get_speed_label
# ---------------------------------------------------------------------------

class TestGetSpeedLabel:
    def test_half_speed_is_slow(self):
        label = get_speed_label(0.5)
        assert "Slow" in label or "🐢" in label

    def test_normal_speed(self):
        label = get_speed_label(1.0)
        assert "Normal" in label or "▶️" in label

    def test_fast_speed(self):
        label = get_speed_label(1.5)
        assert "Fast" in label or "🐇" in label

    def test_max_speed(self):
        label = get_speed_label(2.0)
        assert len(label) > 0

    def test_below_1_returns_slow_label(self):
        label = get_speed_label(0.7)
        assert "Slow" in label or "🐢" in label

    def test_above_1_returns_fast_label(self):
        label = get_speed_label(1.8)
        assert "Fast" in label or "🐇" in label

    def test_returns_string(self):
        assert isinstance(get_speed_label(1.0), str)


# ---------------------------------------------------------------------------
# get_mood_emoji
# ---------------------------------------------------------------------------

class TestGetMoodEmoji:
    def test_neutral_emoji(self):
        assert get_mood_emoji("neutral") == "😐"

    def test_calm_emoji(self):
        assert get_mood_emoji("calm") == "😌"

    def test_formal_emoji(self):
        assert get_mood_emoji("formal") == "🎩"

    def test_energetic_emoji(self):
        assert get_mood_emoji("energetic") == "⚡"

    def test_unknown_returns_default(self):
        assert get_mood_emoji("unknown_mood") == "😐"


# ---------------------------------------------------------------------------
# build_voice_config
# ---------------------------------------------------------------------------

class TestBuildVoiceConfig:
    def test_valid_config_returns_dict(self):
        config = build_voice_config("female", "neutral", 1.0)
        assert isinstance(config, dict)

    def test_all_expected_keys(self):
        config = build_voice_config("male", "calm", 0.75)
        for key in ("gender", "mood", "speed", "speed_label", "mood_emoji", "is_slow"):
            assert key in config

    def test_slow_flag_for_low_speed(self):
        config = build_voice_config("female", "neutral", 0.5)
        assert config["is_slow"] is True

    def test_not_slow_for_normal_speed(self):
        config = build_voice_config("female", "neutral", 1.0)
        assert config["is_slow"] is False

    def test_gender_stored(self):
        config = build_voice_config("male", "formal", 1.0)
        assert config["gender"] == "male"

    def test_mood_stored(self):
        config = build_voice_config("female", "energetic", 1.0)
        assert config["mood"] == "energetic"

    def test_speed_stored(self):
        config = build_voice_config("neutral", "neutral", 1.25)
        assert config["speed"] == 1.25

    def test_invalid_gender_raises(self):
        with pytest.raises(ValueError, match="gender"):
            build_voice_config("robot", "neutral", 1.0)

    def test_invalid_mood_raises(self):
        with pytest.raises(ValueError, match="mood"):
            build_voice_config("female", "angry", 1.0)

    def test_speed_too_low_raises(self):
        with pytest.raises(ValueError, match="speed"):
            build_voice_config("female", "neutral", 0.1)

    def test_speed_too_high_raises(self):
        with pytest.raises(ValueError, match="speed"):
            build_voice_config("female", "neutral", 3.0)

    def test_boundary_speed_05_valid(self):
        config = build_voice_config("female", "neutral", 0.5)
        assert config["speed"] == 0.5

    def test_boundary_speed_20_valid(self):
        config = build_voice_config("female", "neutral", 2.0)
        assert config["speed"] == 2.0


# ---------------------------------------------------------------------------
# validate_voice_config
# ---------------------------------------------------------------------------

class TestValidateVoiceConfig:
    def test_valid_config(self):
        is_valid, msg = validate_voice_config(
            {"gender": "female", "mood": "neutral", "speed": 1.0}
        )
        assert is_valid is True
        assert msg == ""

    def test_invalid_gender(self):
        is_valid, msg = validate_voice_config(
            {"gender": "alien", "mood": "neutral", "speed": 1.0}
        )
        assert is_valid is False
        assert len(msg) > 0

    def test_invalid_mood(self):
        is_valid, msg = validate_voice_config(
            {"gender": "male", "mood": "grumpy", "speed": 1.0}
        )
        assert is_valid is False

    def test_invalid_speed(self):
        is_valid, msg = validate_voice_config(
            {"gender": "female", "mood": "calm", "speed": 99.0}
        )
        assert is_valid is False

    def test_empty_config_is_invalid(self):
        is_valid, msg = validate_voice_config({})
        assert is_valid is False


# ---------------------------------------------------------------------------
# get_mood_display_options / resolve_mood_from_display
# ---------------------------------------------------------------------------

class TestMoodDisplayRoundtrip:
    def setup_method(self):
        self.moods = get_all_moods()

    def test_display_options_count_matches_moods(self):
        options = get_mood_display_options(self.moods)
        assert len(options) == len(self.moods)

    def test_each_option_contains_emoji_and_label(self):
        options = get_mood_display_options(self.moods)
        for option, mood in zip(options, self.moods):
            assert mood["emoji"] in option
            assert mood["label"] in option

    def test_roundtrip_all_moods(self):
        options = get_mood_display_options(self.moods)
        for option, mood in zip(options, self.moods):
            resolved = resolve_mood_from_display(option, self.moods)
            assert resolved == mood["id"]

    def test_unknown_display_returns_neutral(self):
        result = resolve_mood_from_display("🤖 Robot Mode", self.moods)
        assert result == "neutral"
