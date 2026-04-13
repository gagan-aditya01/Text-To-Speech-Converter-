"""
test_settings.py
----------------
Unit tests for app/config/settings.py and app/utils/logger.py

Uses monkeypatch to safely override environment variables per-test
without polluting the process environment for other tests.
"""

import logging
from pathlib import Path

import pytest

from app.config.settings import (
    VALID_LOG_LEVELS,
    VALID_MOODS,
    VALID_TTS_ENGINES,
    VALID_VOICE_GENDERS,
    Settings,
)
from app.utils.logger import get_logger, setup_logging


# ---------------------------------------------------------------------------
# Helper: build Settings with specific env overrides
# ---------------------------------------------------------------------------

def make_settings(monkeypatch, overrides: dict) -> Settings:
    """
    Construct a fresh Settings instance after applying environment overrides.

    We patch os.getenv at the Settings field level by setting real
    environment variables via monkeypatch.
    """
    for key, value in overrides.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, str(value))
    return Settings()


# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------

class TestSettingsDefaults:
    def test_default_engine_is_gtts(self, monkeypatch):
        monkeypatch.delenv("TTS_ENGINE", raising=False)
        s = Settings()
        assert s.TTS_ENGINE == "gtts"

    def test_default_language_is_english(self, monkeypatch):
        monkeypatch.delenv("DEFAULT_LANGUAGE", raising=False)
        s = Settings()
        assert s.DEFAULT_LANGUAGE == "en"

    def test_default_gender_is_female(self, monkeypatch):
        monkeypatch.delenv("DEFAULT_GENDER", raising=False)
        s = Settings()
        assert s.DEFAULT_GENDER == "female"

    def test_default_mood_is_neutral(self, monkeypatch):
        monkeypatch.delenv("DEFAULT_MOOD", raising=False)
        s = Settings()
        assert s.DEFAULT_MOOD == "neutral"

    def test_default_log_level_is_info(self, monkeypatch):
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        s = Settings()
        assert s.LOG_LEVEL == "INFO"

    def test_default_output_dir_is_outputs(self, monkeypatch):
        monkeypatch.delenv("OUTPUT_DIR", raising=False)
        s = Settings()
        assert s.OUTPUT_DIR == Path("outputs")

    def test_default_max_output_files(self, monkeypatch):
        monkeypatch.delenv("MAX_OUTPUT_FILES", raising=False)
        s = Settings()
        assert s.MAX_OUTPUT_FILES == 50

    def test_default_max_text_length(self, monkeypatch):
        monkeypatch.delenv("MAX_TEXT_LENGTH", raising=False)
        s = Settings()
        assert s.MAX_TEXT_LENGTH == 5000

    def test_elevenlabs_key_none_by_default(self, monkeypatch):
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        s = Settings()
        assert s.ELEVENLABS_API_KEY is None


# ---------------------------------------------------------------------------
# Env var overrides
# ---------------------------------------------------------------------------

class TestSettingsEnvOverrides:
    def test_engine_set_from_env(self, monkeypatch):
        s = make_settings(monkeypatch, {"TTS_ENGINE": "elevenlabs",
                                        "ELEVENLABS_API_KEY": "key_abc"})
        assert s.TTS_ENGINE == "elevenlabs"

    def test_engine_is_lowercased(self, monkeypatch):
        s = make_settings(monkeypatch, {"TTS_ENGINE": "GTTS"})
        assert s.TTS_ENGINE == "gtts"

    def test_log_level_is_uppercased(self, monkeypatch):
        s = make_settings(monkeypatch, {"LOG_LEVEL": "debug"})
        assert s.LOG_LEVEL == "DEBUG"

    def test_output_dir_from_env(self, monkeypatch):
        s = make_settings(monkeypatch, {"OUTPUT_DIR": "/tmp/audio_out"})
        assert s.OUTPUT_DIR == Path("/tmp/audio_out")

    def test_elevenlabs_key_from_env(self, monkeypatch):
        s = make_settings(monkeypatch, {"ELEVENLABS_API_KEY": "el_key_xyz"})
        assert s.ELEVENLABS_API_KEY == "el_key_xyz"

    def test_max_output_files_from_env(self, monkeypatch):
        s = make_settings(monkeypatch, {"MAX_OUTPUT_FILES": "100"})
        assert s.MAX_OUTPUT_FILES == 100


# ---------------------------------------------------------------------------
# Validation — invalid values should raise
# ---------------------------------------------------------------------------

class TestSettingsValidation:
    def test_invalid_engine_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="TTS_ENGINE"):
            make_settings(monkeypatch, {"TTS_ENGINE": "invalid_engine"})

    def test_invalid_log_level_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="LOG_LEVEL"):
            make_settings(monkeypatch, {"LOG_LEVEL": "VERBOSE"})

    def test_invalid_gender_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="DEFAULT_GENDER"):
            make_settings(monkeypatch, {"DEFAULT_GENDER": "robot"})

    def test_invalid_mood_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="DEFAULT_MOOD"):
            make_settings(monkeypatch, {"DEFAULT_MOOD": "angry"})

    def test_max_output_files_zero_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="MAX_OUTPUT_FILES"):
            make_settings(monkeypatch, {"MAX_OUTPUT_FILES": "0"})

    def test_max_text_length_zero_raises(self, monkeypatch):
        with pytest.raises(ValueError, match="MAX_TEXT_LENGTH"):
            make_settings(monkeypatch, {"MAX_TEXT_LENGTH": "0"})


# ---------------------------------------------------------------------------
# Properties & repr
# ---------------------------------------------------------------------------

class TestSettingsProperties:
    def test_elevenlabs_configured_true(self, monkeypatch):
        s = make_settings(monkeypatch, {
            "TTS_ENGINE": "elevenlabs",
            "ELEVENLABS_API_KEY": "real_key",
        })
        assert s.elevenlabs_configured is True

    def test_elevenlabs_configured_false(self, monkeypatch):
        monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
        s = Settings()
        assert s.elevenlabs_configured is False

    def test_repr_does_not_expose_api_key(self, monkeypatch):
        s = make_settings(monkeypatch, {
            "TTS_ENGINE": "elevenlabs",
            "ELEVENLABS_API_KEY": "super_secret_key_12345",
        })
        assert "super_secret_key_12345" not in repr(s)

    def test_repr_shows_engine_and_level(self, monkeypatch):
        s = Settings()
        r = repr(s)
        assert "gtts" in r
        assert "INFO" in r


# ---------------------------------------------------------------------------
# Valid constant sets
# ---------------------------------------------------------------------------

class TestValidConstants:
    def test_valid_engines(self):
        assert "gtts" in VALID_TTS_ENGINES
        assert "elevenlabs" in VALID_TTS_ENGINES

    def test_valid_log_levels(self):
        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            assert level in VALID_LOG_LEVELS

    def test_valid_moods(self):
        for mood in ("neutral", "calm", "energetic", "formal"):
            assert mood in VALID_MOODS

    def test_valid_genders(self):
        for gender in ("male", "female", "neutral"):
            assert gender in VALID_VOICE_GENDERS


# ---------------------------------------------------------------------------
# Logger utility
# ---------------------------------------------------------------------------

class TestLogger:
    def test_setup_logging_sets_level(self):
        setup_logging(log_level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_setup_logging_info_level(self):
        setup_logging(log_level="INFO")
        assert logging.getLogger().level == logging.INFO

    def test_get_logger_returns_logger(self):
        log = get_logger("test.module")
        assert isinstance(log, logging.Logger)
        assert log.name == "test.module"
