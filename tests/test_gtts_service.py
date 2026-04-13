"""
test_gtts_service.py
--------------------
Unit tests for app/services/gtts_service.py

All gTTS network calls are mocked — tests run fully offline.
"""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.services.base_tts import TTSRequest, TTSResult, TTSSynthesisError
from app.services.gtts_service import GTTSService
from gtts.tts import gTTSError


# Reusable fake audio payload
FAKE_MP3_BYTES = b"\xff\xfb\x90\x00" + b"\x00" * 100  # minimal fake MP3 header


def _make_gtts_mock(audio_bytes: bytes = FAKE_MP3_BYTES):
    """
    Return a MagicMock that behaves like a gTTS instance.
    write_to_fp() writes fake audio bytes into the buffer.
    """
    mock_tts = MagicMock()

    def fake_write_to_fp(fp):
        fp.write(audio_bytes)

    mock_tts.write_to_fp.side_effect = fake_write_to_fp
    return mock_tts


# ---------------------------------------------------------------------------
# Basic contract tests
# ---------------------------------------------------------------------------

class TestGTTSServiceContract:
    def setup_method(self):
        self.service = GTTSService()

    def test_engine_name(self):
        assert self.service.engine_name == "gtts"

    def test_repr_contains_engine_name(self):
        assert "gtts" in repr(self.service)

    def test_get_supported_language_codes_returns_list(self):
        codes = self.service.get_supported_language_codes()
        assert isinstance(codes, list)
        assert len(codes) > 0

    def test_known_languages_are_supported(self):
        for code in ["en", "hi", "fr", "de", "ja"]:
            assert self.service.is_language_supported(code), (
                f"Expected '{code}' to be supported by gTTS"
            )

    def test_unsupported_language_returns_false(self):
        # "xx-FAKE" is not in our registry
        assert self.service.is_language_supported("xx-FAKE") is False


# ---------------------------------------------------------------------------
# Synthesis — happy path
# ---------------------------------------------------------------------------

class TestGTTSSynthesisSuccess:
    def setup_method(self):
        self.service = GTTSService()

    @patch("app.services.gtts_service.gTTS")
    def test_synthesize_returns_tts_result(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello, world!", language_code="en")
        result = self.service.synthesize(req)
        assert isinstance(result, TTSResult)

    @patch("app.services.gtts_service.gTTS")
    def test_result_has_mp3_format(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en")
        result = self.service.synthesize(req)
        assert result.audio_format == "mp3"

    @patch("app.services.gtts_service.gTTS")
    def test_result_audio_bytes_are_non_empty(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en")
        result = self.service.synthesize(req)
        assert len(result.audio_bytes) > 0

    @patch("app.services.gtts_service.gTTS")
    def test_result_engine_field(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en")
        result = self.service.synthesize(req)
        assert result.engine == "gtts"

    @patch("app.services.gtts_service.gTTS")
    def test_result_language_code_matches_request(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="नमस्ते", language_code="hi")
        result = self.service.synthesize(req)
        assert result.language_code == "hi"

    @patch("app.services.gtts_service.gTTS")
    def test_metadata_contains_expected_keys(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en", mood="calm")
        result = self.service.synthesize(req)
        assert "slow_mode" in result.metadata
        assert "mood" in result.metadata
        assert "voice_gender" in result.metadata
        assert "char_count" in result.metadata

    @patch("app.services.gtts_service.gTTS")
    def test_char_count_in_metadata(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        text = "Hello, world!"
        req = TTSRequest(text=text, language_code="en")
        result = self.service.synthesize(req)
        assert result.metadata["char_count"] == len(text)


# ---------------------------------------------------------------------------
# Speed → slow_mode mapping
# ---------------------------------------------------------------------------

class TestGTTSSpeedMapping:
    def setup_method(self):
        self.service = GTTSService()

    @patch("app.services.gtts_service.gTTS")
    def test_speed_below_1_sets_slow_true(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en", speed=0.5)
        result = self.service.synthesize(req)
        # slow_mode should be True
        assert result.metadata["slow_mode"] is True
        _, call_kwargs = mock_gtts_cls.call_args
        assert call_kwargs["slow"] is True

    @patch("app.services.gtts_service.gTTS")
    def test_speed_1_sets_slow_false(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en", speed=1.0)
        result = self.service.synthesize(req)
        assert result.metadata["slow_mode"] is False

    @patch("app.services.gtts_service.gTTS")
    def test_speed_above_1_sets_slow_false(self, mock_gtts_cls):
        mock_gtts_cls.return_value = _make_gtts_mock()
        req = TTSRequest(text="Hello", language_code="en", speed=1.5)
        result = self.service.synthesize(req)
        assert result.metadata["slow_mode"] is False


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestGTTSSynthesisErrors:
    def setup_method(self):
        self.service = GTTSService()

    def test_unsupported_language_raises_value_error(self):
        req = TTSRequest(text="Hello", language_code="xx-FAKE")
        with pytest.raises(ValueError, match="does not support"):
            self.service.synthesize(req)

    @patch("app.services.gtts_service.gTTS")
    def test_gtts_error_raises_synthesis_error(self, mock_gtts_cls):
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = gTTSError("API error")
        mock_gtts_cls.return_value = mock_instance

        req = TTSRequest(text="Hello", language_code="en")
        with pytest.raises(TTSSynthesisError) as exc_info:
            self.service.synthesize(req)
        assert "gtts" in str(exc_info.value)

    @patch("app.services.gtts_service.gTTS")
    def test_unexpected_error_raises_synthesis_error(self, mock_gtts_cls):
        mock_instance = MagicMock()
        mock_instance.write_to_fp.side_effect = ConnectionError("timeout")
        mock_gtts_cls.return_value = mock_instance

        req = TTSRequest(text="Hello", language_code="en")
        with pytest.raises(TTSSynthesisError):
            self.service.synthesize(req)
