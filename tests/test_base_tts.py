"""
test_base_tts.py
----------------
Unit tests for app/services/base_tts.py

Tests the data models (TTSRequest, TTSResult), the abstract contract
(BaseTTSService), and the custom exception (TTSSynthesisError).

A minimal concrete stub (StubTTSService) is defined here to exercise
the abstract class without depending on any real TTS engine.
"""

import pytest
from app.services.base_tts import (
    TTSRequest,
    TTSResult,
    BaseTTSService,
    TTSSynthesisError,
)


# ---------------------------------------------------------------------------
# Concrete stub — implements the minimum required to satisfy BaseTTSService
# ---------------------------------------------------------------------------

class StubTTSService(BaseTTSService):
    """Minimal concrete TTS implementation used only in tests."""

    SUPPORTED_CODES = ["en", "hi", "fr"]

    @property
    def engine_name(self) -> str:
        return "stub"

    def synthesize(self, request: TTSRequest) -> TTSResult:
        self.validate_request(request)
        return TTSResult(
            audio_bytes=b"fake_audio_data",
            language_code=request.language_code,
            engine=self.engine_name,
        )

    def get_supported_language_codes(self) -> list[str]:
        return self.SUPPORTED_CODES


# ---------------------------------------------------------------------------
# TTSRequest tests
# ---------------------------------------------------------------------------

class TestTTSRequest:
    def test_valid_defaults(self):
        req = TTSRequest(text="Hello", language_code="en")
        assert req.voice_gender == "female"
        assert req.mood == "neutral"
        assert req.speed == 1.0
        assert req.voice_id is None

    def test_custom_fields(self):
        req = TTSRequest(
            text="Bonjour",
            language_code="fr",
            voice_gender="male",
            mood="formal",
            speed=1.5,
            voice_id="voice_abc",
        )
        assert req.voice_gender == "male"
        assert req.mood == "formal"
        assert req.speed == 1.5
        assert req.voice_id == "voice_abc"

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            TTSRequest(text="", language_code="en")

    def test_whitespace_only_text_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            TTSRequest(text="   ", language_code="en")

    def test_empty_language_code_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            TTSRequest(text="Hello", language_code="")

    def test_invalid_voice_gender_raises(self):
        with pytest.raises(ValueError, match="Invalid voice_gender"):
            TTSRequest(text="Hello", language_code="en", voice_gender="robot")

    def test_invalid_mood_raises(self):
        with pytest.raises(ValueError, match="Invalid mood"):
            TTSRequest(text="Hello", language_code="en", mood="angry")

    def test_speed_too_low_raises(self):
        with pytest.raises(ValueError, match="Invalid speed"):
            TTSRequest(text="Hello", language_code="en", speed=0.1)

    def test_speed_too_high_raises(self):
        with pytest.raises(ValueError, match="Invalid speed"):
            TTSRequest(text="Hello", language_code="en", speed=3.0)

    def test_boundary_speed_values_are_valid(self):
        # 0.5 and 2.0 are both valid boundary values
        req_slow = TTSRequest(text="Hello", language_code="en", speed=0.5)
        req_fast = TTSRequest(text="Hello", language_code="en", speed=2.0)
        assert req_slow.speed == 0.5
        assert req_fast.speed == 2.0


# ---------------------------------------------------------------------------
# TTSResult tests
# ---------------------------------------------------------------------------

class TestTTSResult:
    def test_default_format_is_mp3(self):
        result = TTSResult(
            audio_bytes=b"data",
            language_code="en",
            engine="stub",
        )
        assert result.audio_format == "mp3"

    def test_metadata_defaults_to_empty_dict(self):
        result = TTSResult(audio_bytes=b"data", language_code="en", engine="stub")
        assert result.metadata == {}

    def test_custom_format_and_metadata(self):
        result = TTSResult(
            audio_bytes=b"data",
            language_code="hi",
            engine="elevenlabs",
            audio_format="wav",
            metadata={"voice_id": "xyz"},
        )
        assert result.audio_format == "wav"
        assert result.metadata["voice_id"] == "xyz"


# ---------------------------------------------------------------------------
# BaseTTSService (via StubTTSService) tests
# ---------------------------------------------------------------------------

class TestBaseTTSService:
    def setup_method(self):
        self.service = StubTTSService()

    def test_engine_name(self):
        assert self.service.engine_name == "stub"

    def test_repr(self):
        assert "stub" in repr(self.service)

    def test_synthesize_returns_tts_result(self):
        req = TTSRequest(text="Hello", language_code="en")
        result = self.service.synthesize(req)
        assert isinstance(result, TTSResult)
        assert result.audio_bytes == b"fake_audio_data"

    def test_is_language_supported_true(self):
        assert self.service.is_language_supported("en") is True
        assert self.service.is_language_supported("hi") is True

    def test_is_language_supported_false(self):
        assert self.service.is_language_supported("ja") is False

    def test_is_language_supported_case_insensitive(self):
        assert self.service.is_language_supported("EN") is True
        assert self.service.is_language_supported("Fr") is True

    def test_validate_request_passes_for_supported_language(self):
        req = TTSRequest(text="Hello", language_code="en")
        # Should not raise
        self.service.validate_request(req)

    def test_validate_request_raises_for_unsupported_language(self):
        req = TTSRequest(text="こんにちは", language_code="ja")
        with pytest.raises(ValueError, match="does not support"):
            self.service.validate_request(req)

    def test_cannot_instantiate_abstract_class_directly(self):
        with pytest.raises(TypeError):
            BaseTTSService()  # type: ignore


# ---------------------------------------------------------------------------
# TTSSynthesisError tests
# ---------------------------------------------------------------------------

class TestTTSSynthesisError:
    def test_message_format(self):
        err = TTSSynthesisError(engine="gtts", reason="network timeout")
        assert "gtts" in str(err)
        assert "network timeout" in str(err)

    def test_attributes(self):
        err = TTSSynthesisError(engine="elevenlabs", reason="quota exceeded")
        assert err.engine == "elevenlabs"
        assert err.reason == "quota exceeded"

    def test_is_exception_subclass(self):
        err = TTSSynthesisError(engine="stub", reason="test")
        assert isinstance(err, Exception)
