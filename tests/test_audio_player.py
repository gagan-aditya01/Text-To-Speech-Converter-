"""
test_audio_player.py
--------------------
Unit tests for pure logic functions in app/components/audio_player.py

Tests cover: format_file_size, estimate_duration, build_audio_metadata,
             add_to_session_history, get_session_history, truncate_label.
"""

import pytest

from app.components.audio_player import (
    MAX_HISTORY_ENTRIES,
    add_to_session_history,
    build_audio_metadata,
    estimate_duration,
    format_file_size,
    get_session_history,
    truncate_label,
)


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

def make_result_data(
    lang="English",
    flag="🇺🇸",
    chars=100,
    engine="gtts",
    mood="neutral",
    voice_gender="female",
    speed=1.0,
    audio_bytes=b"x" * 12288,  # ~12 KB
    file_name="tts_gtts_en_20240501.mp3",
    mime_type="audio/mpeg",
) -> dict:
    return {
        "lang": lang,
        "flag": flag,
        "chars": chars,
        "engine": engine,
        "mood": mood,
        "voice_gender": voice_gender,
        "speed": speed,
        "audio_bytes": audio_bytes,
        "file_name": file_name,
        "mime_type": mime_type,
    }


# ---------------------------------------------------------------------------
# format_file_size
# ---------------------------------------------------------------------------

class TestFormatFileSize:
    def test_zero_bytes(self):
        assert format_file_size(0) == "0 B"

    def test_negative_bytes_returns_zero(self):
        assert format_file_size(-100) == "0 B"

    def test_bytes_range(self):
        assert format_file_size(512) == "512 B"

    def test_kilobytes(self):
        result = format_file_size(1024)
        assert "KB" in result
        assert "1.0" in result

    def test_kilobytes_decimal(self):
        result = format_file_size(1536)  # 1.5 KB
        assert "1.5 KB" == result

    def test_megabytes(self):
        result = format_file_size(1024 * 1024)
        assert "MB" in result
        assert "1.00" in result

    def test_large_file(self):
        result = format_file_size(5 * 1024 * 1024)  # 5 MB
        assert "5.00 MB" == result

    def test_under_1kb(self):
        result = format_file_size(999)
        assert "B" in result
        assert "KB" not in result


# ---------------------------------------------------------------------------
# estimate_duration
# ---------------------------------------------------------------------------

class TestEstimateDuration:
    def test_zero_chars(self):
        assert estimate_duration(0) == "< 1 sec"

    def test_negative_chars(self):
        assert estimate_duration(-10) == "< 1 sec"

    def test_normal_speed_short_text(self):
        # 12 chars ÷ 12.5 chars/sec ≈ 1 sec
        result = estimate_duration(12, speed=1.0)
        assert "sec" in result

    def test_slow_speed_increases_duration(self):
        # Same chars, slower speed → longer duration
        fast = estimate_duration(100, speed=2.0)
        slow = estimate_duration(100, speed=0.5)
        # slow should show more seconds
        assert slow != fast

    def test_returns_minutes_for_long_text(self):
        # ~1000 chars at 1.0x → ~80 sec → "~1 min ..."
        result = estimate_duration(1000, speed=1.0)
        assert "min" in result

    def test_exactly_60_seconds(self):
        # 12.5 chars/sec × 60 sec = 750 chars
        result = estimate_duration(750, speed=1.0)
        assert "min" in result
        assert "0 sec" not in result  # "~1 min" not "~1 min 0 sec"

    def test_returns_string(self):
        assert isinstance(estimate_duration(100), str)

    def test_format_contains_tilde(self):
        assert "~" in estimate_duration(50)


# ---------------------------------------------------------------------------
# build_audio_metadata
# ---------------------------------------------------------------------------

class TestBuildAudioMetadata:
    def test_returns_dict(self):
        data = make_result_data()
        meta = build_audio_metadata(data)
        assert isinstance(meta, dict)

    def test_all_expected_keys(self):
        meta = build_audio_metadata(make_result_data())
        for key in ("lang", "flag", "engine", "chars", "file_name",
                    "file_size", "duration", "mood", "voice_gender", "speed"):
            assert key in meta, f"Missing key: {key}"

    def test_engine_uppercased(self):
        meta = build_audio_metadata(make_result_data(engine="gtts"))
        assert meta["engine"] == "GTTS"

    def test_mood_title_cased(self):
        meta = build_audio_metadata(make_result_data(mood="calm"))
        assert meta["mood"] == "Calm"

    def test_gender_title_cased(self):
        meta = build_audio_metadata(make_result_data(voice_gender="female"))
        assert meta["voice_gender"] == "Female"

    def test_file_size_formatted(self):
        meta = build_audio_metadata(make_result_data(audio_bytes=b"x" * 1024))
        assert "KB" in meta["file_size"] or "B" in meta["file_size"]

    def test_duration_present(self):
        meta = build_audio_metadata(make_result_data(chars=100))
        assert len(meta["duration"]) > 0

    def test_missing_fields_use_defaults(self):
        meta = build_audio_metadata({})
        assert meta["lang"] == "Unknown"
        assert meta["flag"] == "🌐"
        assert meta["engine"] == "GTTS"


# ---------------------------------------------------------------------------
# add_to_session_history / get_session_history
# ---------------------------------------------------------------------------

class TestSessionHistory:
    def test_empty_session_returns_empty_list(self):
        state = {}
        assert get_session_history(state) == []

    def test_add_single_entry(self):
        state = {}
        add_to_session_history(state, make_result_data())
        history = get_session_history(state)
        assert len(history) == 1

    def test_newest_entry_is_first(self):
        state = {}
        add_to_session_history(state, make_result_data(lang="English"))
        add_to_session_history(state, make_result_data(lang="Hindi"))
        history = get_session_history(state)
        assert history[0]["lang"] == "Hindi"

    def test_history_capped_at_max_entries(self):
        state = {}
        for i in range(MAX_HISTORY_ENTRIES + 5):
            add_to_session_history(state, make_result_data(lang=f"Lang{i}"))
        assert len(get_session_history(state)) == MAX_HISTORY_ENTRIES

    def test_audio_bytes_preserved_in_history(self):
        state = {}
        data = make_result_data(audio_bytes=b"real_audio")
        add_to_session_history(state, data)
        assert get_session_history(state)[0]["audio_bytes"] == b"real_audio"

    def test_multiple_entries_accumulate(self):
        state = {}
        for i in range(5):
            add_to_session_history(state, make_result_data(lang=f"Lang{i}"))
        assert len(get_session_history(state)) == 5

    def test_get_history_from_empty_dict(self):
        assert get_session_history({}) == []


# ---------------------------------------------------------------------------
# truncate_label
# ---------------------------------------------------------------------------

class TestTruncateLabel:
    def test_short_text_unchanged(self):
        assert truncate_label("Hello", 40) == "Hello"

    def test_exactly_at_limit_unchanged(self):
        text = "a" * 40
        assert truncate_label(text, 40) == text

    def test_over_limit_truncated_with_ellipsis(self):
        text = "a" * 50
        result = truncate_label(text, 40)
        assert result.endswith("…")
        assert len(result) == 41  # 40 chars + "…"

    def test_empty_string(self):
        assert truncate_label("", 40) == ""

    def test_custom_max_chars(self):
        result = truncate_label("Hello World", max_chars=5)
        assert result == "Hello…"
