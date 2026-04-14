"""
test_elevenlabs_service.py
--------------------------
Unit tests for app/services/elevenlabs_service.py

All HTTP calls are mocked — tests run fully offline.
Pure helper functions are tested directly without mocking.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.services.base_tts import TTSRequest, TTSResult, TTSSynthesisError
from app.services.elevenlabs_service import (
    ElevenLabsService,
    _DEFAULT_VOICE_IDS,
    _MOOD_VOICE_SETTINGS,
    _parse_api_error,
    build_request_payload,
    get_elevenlabs_supported_codes,
    get_voice_id,
    get_voice_settings,
)

FAKE_API_KEY = "el_test_key_abc123"
FAKE_AUDIO = b"\xff\xfb\x90\x00" + b"\x00" * 200  # fake MP3 header


def make_request(**kwargs) -> TTSRequest:
    defaults = {
        "text": "Hello, ElevenLabs!",
        "language_code": "en",
        "voice_gender": "female",
        "mood": "neutral",
        "speed": 1.0,
    }
    defaults.update(kwargs)
    return TTSRequest(**defaults)


def make_mock_response(status_code=200, content=FAKE_AUDIO, json_body=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.content = content
    mock.raise_for_status = MagicMock()
    if status_code >= 400:
        http_error = requests.exceptions.HTTPError(response=mock)
        mock.raise_for_status.side_effect = http_error
    if json_body is not None:
        mock.json.return_value = json_body
    else:
        mock.json.side_effect = Exception("No JSON")
    mock.text = "Error text"
    return mock


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

class TestGetVoiceId:
    def test_female_returns_female_voice(self):
        vid = get_voice_id("female")
        assert vid == _DEFAULT_VOICE_IDS["female"]

    def test_male_returns_male_voice(self):
        vid = get_voice_id("male")
        assert vid == _DEFAULT_VOICE_IDS["male"]

    def test_neutral_returns_neutral_voice(self):
        vid = get_voice_id("neutral")
        assert vid == _DEFAULT_VOICE_IDS["neutral"]

    def test_unknown_gender_falls_back_to_neutral(self):
        vid = get_voice_id("robot")
        assert vid == _DEFAULT_VOICE_IDS["neutral"]

    def test_override_takes_precedence(self):
        custom_id = "custom_voice_xyz"
        assert get_voice_id("female", voice_id_override=custom_id) == custom_id

    def test_none_override_uses_gender(self):
        assert get_voice_id("male", voice_id_override=None) == _DEFAULT_VOICE_IDS["male"]


class TestGetVoiceSettings:
    def test_neutral_settings(self):
        s = get_voice_settings("neutral")
        assert "stability" in s
        assert "similarity_boost" in s

    def test_calm_has_high_stability(self):
        calm = get_voice_settings("calm")
        neutral = get_voice_settings("neutral")
        assert calm["stability"] > neutral["stability"]

    def test_formal_has_highest_stability(self):
        formal = get_voice_settings("formal")
        calm = get_voice_settings("calm")
        assert formal["stability"] >= calm["stability"]

    def test_energetic_has_low_stability(self):
        energetic = get_voice_settings("energetic")
        neutral = get_voice_settings("neutral")
        assert energetic["stability"] < neutral["stability"]

    def test_energetic_has_higher_style(self):
        energetic = get_voice_settings("energetic")
        calm = get_voice_settings("calm")
        assert energetic["style"] > calm["style"]

    def test_unknown_mood_falls_back_to_neutral(self):
        s = get_voice_settings("angry")
        assert s == _MOOD_VOICE_SETTINGS["neutral"]

    def test_all_required_keys_present(self):
        for mood in ("neutral", "calm", "formal", "energetic"):
            s = get_voice_settings(mood)
            for key in ("stability", "similarity_boost", "style", "use_speaker_boost"):
                assert key in s, f"Missing '{key}' in settings for mood '{mood}'"


class TestBuildRequestPayload:
    def test_returns_dict(self):
        req = make_request()
        payload = build_request_payload(req)
        assert isinstance(payload, dict)

    def test_text_in_payload(self):
        req = make_request(text="Test text")
        payload = build_request_payload(req)
        assert payload["text"] == "Test text"

    def test_model_id_present(self):
        payload = build_request_payload(make_request())
        assert "model_id" in payload

    def test_voice_settings_present(self):
        payload = build_request_payload(make_request())
        assert "voice_settings" in payload

    def test_mood_reflected_in_settings(self):
        calm_req = make_request(mood="calm")
        neutral_req = make_request(mood="neutral")
        calm_payload = build_request_payload(calm_req)
        neutral_payload = build_request_payload(neutral_req)
        assert calm_payload["voice_settings"]["stability"] != \
               neutral_payload["voice_settings"]["stability"]


class TestGetElevenLabsSupportedCodes:
    def test_returns_list(self):
        codes = get_elevenlabs_supported_codes()
        assert isinstance(codes, list)

    def test_english_is_supported(self):
        assert "en" in get_elevenlabs_supported_codes()

    def test_no_gtts_only_languages(self):
        # Languages marked only gtts_supported should NOT be in EL codes
        codes = get_elevenlabs_supported_codes()
        # Bengali is gtts-only in our registry
        assert "bn" not in codes


# ---------------------------------------------------------------------------
# ElevenLabsService — contract
# ---------------------------------------------------------------------------

class TestElevenLabsServiceContract:
    def test_engine_name(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        assert svc.engine_name == "elevenlabs"

    def test_repr(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        assert "elevenlabs" in repr(svc)

    def test_supported_codes_non_empty(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        assert len(svc.get_supported_language_codes()) > 0

    def test_is_language_supported_english(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        assert svc.is_language_supported("en") is True

    def test_is_language_not_supported(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        assert svc.is_language_supported("bn") is False


# ---------------------------------------------------------------------------
# Synthesis — success path
# ---------------------------------------------------------------------------

class TestElevenLabsSynthesisSuccess:
    @patch("app.services.elevenlabs_service.requests.post")
    def test_returns_tts_result(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        result = svc.synthesize(make_request())
        assert isinstance(result, TTSResult)

    @patch("app.services.elevenlabs_service.requests.post")
    def test_audio_bytes_non_empty(self, mock_post):
        mock_post.return_value = make_mock_response(200, content=FAKE_AUDIO)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        result = svc.synthesize(make_request())
        assert result.audio_bytes == FAKE_AUDIO

    @patch("app.services.elevenlabs_service.requests.post")
    def test_result_format_is_mp3(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        result = svc.synthesize(make_request())
        assert result.audio_format == "mp3"

    @patch("app.services.elevenlabs_service.requests.post")
    def test_result_engine_is_elevenlabs(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        result = svc.synthesize(make_request())
        assert result.engine == "elevenlabs"

    @patch("app.services.elevenlabs_service.requests.post")
    def test_metadata_has_expected_keys(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        result = svc.synthesize(make_request())
        for key in ("voice_id", "mood", "voice_gender", "char_count", "voice_settings"):
            assert key in result.metadata

    @patch("app.services.elevenlabs_service.requests.post")
    def test_api_key_sent_in_header(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        svc.synthesize(make_request())
        _, call_kwargs = mock_post.call_args
        assert call_kwargs["headers"]["xi-api-key"] == FAKE_API_KEY

    @patch("app.services.elevenlabs_service.requests.post")
    def test_voice_id_in_url(self, mock_post):
        mock_post.return_value = make_mock_response(200)
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        svc.synthesize(make_request(voice_gender="female"))
        call_url = mock_post.call_args[0][0]
        assert _DEFAULT_VOICE_IDS["female"] in call_url


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestElevenLabsErrors:
    def test_no_api_key_raises_synthesis_error(self):
        svc = ElevenLabsService(api_key=None)
        with pytest.raises(TTSSynthesisError, match="API_KEY"):
            svc.synthesize(make_request())

    def test_unsupported_language_raises_value_error(self):
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        req = make_request(language_code="bn")  # Bengali not EL-supported
        with pytest.raises(ValueError, match="does not support"):
            svc.synthesize(req)

    @patch("app.services.elevenlabs_service.requests.post")
    def test_http_401_raises_synthesis_error(self, mock_post):
        mock_post.return_value = make_mock_response(401)
        svc = ElevenLabsService(api_key="bad_key")
        with pytest.raises(TTSSynthesisError):
            svc.synthesize(make_request())

    @patch("app.services.elevenlabs_service.requests.post")
    def test_timeout_raises_synthesis_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.Timeout()
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        with pytest.raises(TTSSynthesisError, match="timed out"):
            svc.synthesize(make_request())

    @patch("app.services.elevenlabs_service.requests.post")
    def test_network_error_raises_synthesis_error(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError("unreachable")
        svc = ElevenLabsService(api_key=FAKE_API_KEY)
        with pytest.raises(TTSSynthesisError, match="Network"):
            svc.synthesize(make_request())


# ---------------------------------------------------------------------------
# _parse_api_error
# ---------------------------------------------------------------------------

class TestParseApiError:
    def test_none_response_returns_fallback(self):
        result = _parse_api_error(None)
        assert "No response" in result

    def test_json_body_with_detail_message(self):
        mock = MagicMock()
        mock.json.return_value = {"detail": {"message": "quota exceeded"}}
        result = _parse_api_error(mock)
        assert "quota exceeded" in result

    def test_json_parse_failure_returns_text(self):
        mock = MagicMock()
        mock.json.side_effect = Exception("bad json")
        mock.text = "Internal Server Error"
        mock.status_code = 500
        result = _parse_api_error(mock)
        assert "Internal Server Error" in result or "500" in result
