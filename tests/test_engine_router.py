"""
test_engine_router.py
---------------------
Unit tests for app/services/engine_router.py

Tests cover: get_available_engines, validate_engine, resolve_engine_name,
             and get_tts_service (with settings mock to avoid real API calls).
"""

from unittest.mock import patch

import pytest

from app.services.engine_router import (
    get_available_engines,
    get_tts_service,
    resolve_engine_name,
    validate_engine,
)
from app.services.gtts_service import GTTSService


# ---------------------------------------------------------------------------
# get_available_engines
# ---------------------------------------------------------------------------

class TestGetAvailableEngines:
    def test_returns_list(self):
        engines = get_available_engines()
        assert isinstance(engines, list)

    def test_gtts_in_list(self):
        assert "gtts" in get_available_engines()

    def test_elevenlabs_in_list(self):
        assert "elevenlabs" in get_available_engines()

    def test_list_is_sorted(self):
        engines = get_available_engines()
        assert engines == sorted(engines)

    def test_at_least_two_engines(self):
        assert len(get_available_engines()) >= 2


# ---------------------------------------------------------------------------
# validate_engine
# ---------------------------------------------------------------------------

class TestValidateEngine:
    def test_gtts_is_valid(self):
        assert validate_engine("gtts") is True

    def test_elevenlabs_is_valid(self):
        assert validate_engine("elevenlabs") is True

    def test_unknown_is_invalid(self):
        assert validate_engine("unknown_engine") is False

    def test_empty_string_is_invalid(self):
        assert validate_engine("") is False

    def test_case_insensitive(self):
        assert validate_engine("GTTS") is True
        assert validate_engine("ElevenLabs") is True


# ---------------------------------------------------------------------------
# resolve_engine_name
# ---------------------------------------------------------------------------

class TestResolveEngineName:
    def test_explicit_gtts(self):
        assert resolve_engine_name("gtts") == "gtts"

    def test_explicit_elevenlabs(self):
        assert resolve_engine_name("elevenlabs") == "elevenlabs"

    def test_uppercase_normalized(self):
        assert resolve_engine_name("GTTS") == "gtts"

    def test_none_falls_back_to_settings(self):
        with patch("app.services.engine_router.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            assert resolve_engine_name(None) == "gtts"

    def test_unknown_engine_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            resolve_engine_name("openai_tts")

    def test_error_message_lists_available_engines(self):
        with pytest.raises(ValueError) as exc_info:
            resolve_engine_name("bogus")
        assert "gtts" in str(exc_info.value)
        assert "elevenlabs" in str(exc_info.value)


# ---------------------------------------------------------------------------
# get_tts_service
# ---------------------------------------------------------------------------

class TestGetTtsService:
    def test_gtts_engine_returns_gtts_service(self):
        service = get_tts_service(engine="gtts")
        assert isinstance(service, GTTSService)

    def test_gtts_engine_name_property(self):
        service = get_tts_service(engine="gtts")
        assert service.engine_name == "gtts"

    def test_elevenlabs_engine_returns_elevenlabs_service(self):
        from app.services.elevenlabs_service import ElevenLabsService
        service = get_tts_service(engine="elevenlabs")
        assert isinstance(service, ElevenLabsService)

    def test_elevenlabs_engine_name_property(self):
        service = get_tts_service(engine="elevenlabs")
        assert service.engine_name == "elevenlabs"

    def test_returns_base_tts_service_instance(self):
        from app.services.base_tts import BaseTTSService
        service = get_tts_service(engine="gtts")
        assert isinstance(service, BaseTTSService)

    def test_none_engine_uses_settings(self):
        with patch("app.services.engine_router.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            service = get_tts_service(engine=None)
            assert isinstance(service, GTTSService)

    def test_unknown_engine_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown TTS engine"):
            get_tts_service(engine="nonexistent_engine")

    def test_gtts_service_has_supported_languages(self):
        service = get_tts_service(engine="gtts")
        codes = service.get_supported_language_codes()
        assert "en" in codes
        assert len(codes) > 10

    def test_elevenlabs_service_has_supported_languages(self):
        service = get_tts_service(engine="elevenlabs")
        codes = service.get_supported_language_codes()
        assert "en" in codes
