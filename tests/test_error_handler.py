"""
test_error_handler.py
---------------------
Unit tests for app/utils/error_handler.py

Tests cover: classify_error, format_error_message, is_retryable,
             get_guidance, _sanitize_message, ErrorInfo dataclass structure.
"""

import pytest
import requests

from app.services.base_tts import TTSSynthesisError
from app.utils.error_handler import (
    ErrorCategory,
    ErrorInfo,
    _sanitize_message,
    classify_error,
    format_error_message,
    get_guidance,
    is_retryable,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_synthesis_error(reason: str) -> TTSSynthesisError:
    return TTSSynthesisError(engine="gtts", reason=reason)


def make_http_error(status_code: int) -> requests.exceptions.HTTPError:
    mock_response = requests.models.Response()
    mock_response.status_code = status_code
    return requests.exceptions.HTTPError(response=mock_response)


# ---------------------------------------------------------------------------
# classify_error
# ---------------------------------------------------------------------------

class TestClassifyError:
    # TTSSynthesisError variants
    def test_api_key_error_classified_as_auth(self):
        exc = make_synthesis_error("ELEVENLABS_API_KEY is not configured.")
        assert classify_error(exc) == ErrorCategory.AUTH

    def test_timeout_in_reason_classified_as_timeout(self):
        exc = make_synthesis_error("Request timed out after 30s.")
        assert classify_error(exc) == ErrorCategory.TIMEOUT

    def test_quota_in_reason_classified_as_rate_limit(self):
        exc = make_synthesis_error("API quota exceeded for this billing period.")
        assert classify_error(exc) == ErrorCategory.RATE_LIMIT

    def test_network_in_reason_classified_as_network(self):
        exc = make_synthesis_error("Network error: connection refused.")
        assert classify_error(exc) == ErrorCategory.NETWORK

    def test_api_error_in_reason_classified_as_api(self):
        exc = make_synthesis_error("API error 500: server error.")
        assert classify_error(exc) == ErrorCategory.API

    def test_generic_synthesis_error_classified_as_api(self):
        exc = make_synthesis_error("Something went wrong.")
        assert classify_error(exc) == ErrorCategory.API

    # ValueError variants
    def test_language_value_error_classified_as_language(self):
        exc = ValueError("Engine does not support language 'xx'.")
        assert classify_error(exc) == ErrorCategory.LANGUAGE

    def test_plain_value_error_classified_as_input(self):
        exc = ValueError("Text cannot be empty.")
        assert classify_error(exc) == ErrorCategory.INPUT

    # requests exceptions
    def test_timeout_exception_classified_as_timeout(self):
        exc = requests.exceptions.Timeout()
        assert classify_error(exc) == ErrorCategory.TIMEOUT

    def test_connection_error_classified_as_network(self):
        exc = requests.exceptions.ConnectionError("unreachable")
        assert classify_error(exc) == ErrorCategory.NETWORK

    def test_http_401_classified_as_auth(self):
        exc = make_http_error(401)
        assert classify_error(exc) == ErrorCategory.AUTH

    def test_http_403_classified_as_auth(self):
        exc = make_http_error(403)
        assert classify_error(exc) == ErrorCategory.AUTH

    def test_http_429_classified_as_rate_limit(self):
        exc = make_http_error(429)
        assert classify_error(exc) == ErrorCategory.RATE_LIMIT

    def test_http_500_classified_as_api(self):
        exc = make_http_error(500)
        assert classify_error(exc) == ErrorCategory.API

    def test_unknown_exception_classified_as_unknown(self):
        exc = RuntimeError("something random")
        assert classify_error(exc) == ErrorCategory.UNKNOWN


# ---------------------------------------------------------------------------
# format_error_message
# ---------------------------------------------------------------------------

class TestFormatErrorMessage:
    def test_returns_error_info(self):
        exc = make_synthesis_error("API error 500: server error.")
        info = format_error_message(exc, engine="gtts")
        assert isinstance(info, ErrorInfo)

    def test_info_has_all_fields(self):
        exc = make_synthesis_error("API error 500: server error.")
        info = format_error_message(exc, engine="gtts")
        for field in ("category", "title", "message", "guidance",
                      "icon", "severity", "is_retryable"):
            assert getattr(info, field) is not None

    def test_auth_error_title(self):
        exc = make_synthesis_error("ELEVENLABS_API_KEY is not configured.")
        info = format_error_message(exc)
        assert info.title == "API Key Not Configured"

    def test_language_error_not_retryable(self):
        exc = ValueError("Engine does not support language 'xx'.")
        info = format_error_message(exc)
        assert info.is_retryable is False

    def test_network_error_is_retryable(self):
        exc = requests.exceptions.ConnectionError("unreachable")
        info = format_error_message(exc)
        assert info.is_retryable is True

    def test_timeout_is_retryable(self):
        exc = requests.exceptions.Timeout()
        info = format_error_message(exc)
        assert info.is_retryable is True

    def test_raw_error_stored(self):
        exc = RuntimeError("unexpected")
        info = format_error_message(exc)
        assert info.raw_error is exc

    def test_severity_is_valid_string(self):
        exc = RuntimeError("x")
        info = format_error_message(exc)
        assert info.severity in ("error", "warning", "info")

    def test_ttssynthesis_reason_used_as_message(self):
        exc = make_synthesis_error("API error 429: rate limit hit.")
        info = format_error_message(exc)
        assert "rate limit" in info.message.lower() or "429" in info.message


# ---------------------------------------------------------------------------
# is_retryable
# ---------------------------------------------------------------------------

class TestIsRetryable:
    def test_network_error_is_retryable(self):
        assert is_retryable(requests.exceptions.ConnectionError()) is True

    def test_auth_error_is_not_retryable(self):
        exc = make_synthesis_error("ELEVENLABS_API_KEY is not configured.")
        assert is_retryable(exc) is False

    def test_rate_limit_is_not_retryable(self):
        exc = make_synthesis_error("API quota exceeded.")
        assert is_retryable(exc) is False

    def test_timeout_is_retryable(self):
        assert is_retryable(requests.exceptions.Timeout()) is True

    def test_unknown_is_retryable(self):
        assert is_retryable(RuntimeError("random")) is True


# ---------------------------------------------------------------------------
# get_guidance
# ---------------------------------------------------------------------------

class TestGetGuidance:
    def test_returns_string_for_all_categories(self):
        for category in ErrorCategory:
            guidance = get_guidance(category)
            assert isinstance(guidance, str)
            assert len(guidance) > 10

    def test_auth_guidance_mentions_api_key(self):
        guidance = get_guidance(ErrorCategory.AUTH)
        assert "API" in guidance or "key" in guidance.lower()

    def test_rate_limit_guidance_mentions_gtts(self):
        guidance = get_guidance(ErrorCategory.RATE_LIMIT)
        assert "gtts" in guidance.lower() or "quota" in guidance.lower()

    def test_language_guidance_mentions_gtts(self):
        guidance = get_guidance(ErrorCategory.LANGUAGE)
        assert "gtts" in guidance.lower() or "language" in guidance.lower()


# ---------------------------------------------------------------------------
# _sanitize_message
# ---------------------------------------------------------------------------

class TestSanitizeMessage:
    def test_empty_returns_fallback(self):
        result = _sanitize_message("")
        assert result == "An error occurred."

    def test_none_like_empty_string(self):
        result = _sanitize_message("")
        assert len(result) > 0

    def test_normal_message_unchanged(self):
        result = _sanitize_message("Connection refused.")
        assert "Connection refused" in result

    def test_traceback_stripped(self):
        msg = 'Traceback (most recent call last): File "main.py", line 42'
        result = _sanitize_message(msg)
        assert "Traceback" not in result
        assert "internal error" in result.lower()

    def test_long_message_truncated(self):
        long_msg = "x" * 500
        result = _sanitize_message(long_msg)
        assert len(result) <= 303  # 300 chars + "..."
        assert result.endswith("...")

    def test_short_message_not_truncated(self):
        short = "Short error."
        assert _sanitize_message(short) == short


# ---------------------------------------------------------------------------
# ErrorInfo dataclass
# ---------------------------------------------------------------------------

class TestErrorInfoDataclass:
    def test_raw_error_defaults_to_none(self):
        info = ErrorInfo(
            category=ErrorCategory.UNKNOWN,
            title="Test",
            message="msg",
            guidance="guidance",
            icon="❌",
            severity="error",
            is_retryable=True,
        )
        assert info.raw_error is None

    def test_all_fields_assignable(self):
        exc = RuntimeError("test")
        info = ErrorInfo(
            category=ErrorCategory.NETWORK,
            title="Network Error",
            message="Failed.",
            guidance="Check connection.",
            icon="🌐",
            severity="error",
            is_retryable=True,
            raw_error=exc,
        )
        assert info.raw_error is exc
        assert info.category == ErrorCategory.NETWORK
