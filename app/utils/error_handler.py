"""
error_handler.py
----------------
Centralized error classification and user-facing message formatting.

Design goals:
  - Every error surfaces a clear, actionable message (not raw tracebacks)
  - Errors are classified by category so the UI can respond appropriately
  - Retryable errors show a "Try Again" prompt; permanent errors do not
  - All formatting logic is pure-function / testable without Streamlit

Usage:
    from app.utils.error_handler import classify_error, format_error_message

    try:
        result = service.synthesize(request)
    except Exception as exc:
        error_info = format_error_message(exc, engine="gtts")
        render_error_feedback(error_info)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error Categories
# ---------------------------------------------------------------------------

class ErrorCategory(Enum):
    """Semantic classification of TTS errors for UI routing."""
    NETWORK     = "network"      # Connection/DNS/timeout failures
    AUTH        = "auth"         # Missing or invalid API key
    API         = "api"          # HTTP 4xx/5xx from remote service
    INPUT       = "input"        # Bad text input (empty, too long, invalid chars)
    LANGUAGE    = "language"     # Unsupported language for the chosen engine
    TIMEOUT     = "timeout"      # Request exceeded time limit
    RATE_LIMIT  = "rate_limit"   # API quota exceeded
    UNKNOWN     = "unknown"      # Catch-all


# ---------------------------------------------------------------------------
# ErrorInfo — structured output
# ---------------------------------------------------------------------------

@dataclass
class ErrorInfo:
    """
    Fully resolved, display-ready error descriptor.

    Attributes:
        category:     Semantic category for UI routing decisions.
        title:        Short headline e.g. "Connection Failed".
        message:      One-sentence explanation of what went wrong.
        guidance:     Actionable step the user can take.
        icon:         Emoji icon for the error card.
        severity:     "error" | "warning" | "info" — maps to Streamlit's alert level.
        is_retryable: True if the user can reasonably try again immediately.
        raw_error:    Original exception for logging (not displayed to user).
    """
    category:     ErrorCategory
    title:        str
    message:      str
    guidance:     str
    icon:         str
    severity:     str
    is_retryable: bool
    raw_error:    Optional[Exception] = None


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

# Import lazily to avoid circular imports
def _get_synthesis_error_class():
    from app.services.base_tts import TTSSynthesisError
    return TTSSynthesisError


def classify_error(exc: Exception) -> ErrorCategory:
    """
    Classify an exception into a semantic ErrorCategory.

    Checks in priority order: specific service errors first, then
    network/HTTP errors, then generic Python exceptions.

    Args:
        exc: Any raised exception.

    Returns:
        The most specific matching ErrorCategory.
    """
    exc_str = str(exc).lower()
    exc_type = type(exc).__name__

    # Check TTSSynthesisError reason field
    TTSSynthesisError = _get_synthesis_error_class()
    if isinstance(exc, TTSSynthesisError):
        reason = exc.reason.lower() if hasattr(exc, "reason") else ""
        if "api_key" in reason or "not configured" in reason or "api key" in reason:
            return ErrorCategory.AUTH
        if "timed out" in reason or "timeout" in reason:
            return ErrorCategory.TIMEOUT
        if "quota" in reason or "rate" in reason or "limit" in reason:
            return ErrorCategory.RATE_LIMIT
        if "network" in reason or "connection" in reason:
            return ErrorCategory.NETWORK
        if "api error" in reason:
            return ErrorCategory.API
        return ErrorCategory.API  # Default for TTSSynthesisError

    # ValueError from text validation or language check
    if isinstance(exc, ValueError):
        if "support" in exc_str or "language" in exc_str:
            return ErrorCategory.LANGUAGE
        return ErrorCategory.INPUT

    # requests exceptions (imported lazily)
    try:
        import requests
        if isinstance(exc, requests.exceptions.Timeout):
            return ErrorCategory.TIMEOUT
        if isinstance(exc, requests.exceptions.ConnectionError):
            return ErrorCategory.NETWORK
        if isinstance(exc, requests.exceptions.HTTPError):
            status = getattr(exc.response, "status_code", 0)
            if status in (401, 403):
                return ErrorCategory.AUTH
            if status == 429:
                return ErrorCategory.RATE_LIMIT
            return ErrorCategory.API
        if isinstance(exc, requests.exceptions.RequestException):
            return ErrorCategory.NETWORK
    except ImportError:
        pass

    return ErrorCategory.UNKNOWN


# ---------------------------------------------------------------------------
# Per-category content
# ---------------------------------------------------------------------------

_CATEGORY_CONTENT: dict[ErrorCategory, dict] = {
    ErrorCategory.NETWORK: {
        "title":        "Connection Failed",
        "icon":         "🌐",
        "severity":     "error",
        "is_retryable": True,
        "guidance":     (
            "Check your internet connection and try again. "
            "If the problem persists, the TTS service may be temporarily unavailable."
        ),
    },
    ErrorCategory.AUTH: {
        "title":        "API Key Not Configured",
        "icon":         "🔑",
        "severity":     "warning",
        "is_retryable": False,
        "guidance":     (
            "Add your API key to the .env file:\n"
            "  ELEVENLABS_API_KEY=your_key_here\n"
            "Then restart the app. Get a free key at elevenlabs.io."
        ),
    },
    ErrorCategory.API: {
        "title":        "Service Error",
        "icon":         "⚠️",
        "severity":     "error",
        "is_retryable": True,
        "guidance":     (
            "The TTS service returned an error. "
            "Wait a moment and try again, or switch to the gTTS engine in your .env."
        ),
    },
    ErrorCategory.INPUT: {
        "title":        "Invalid Input",
        "icon":         "📝",
        "severity":     "warning",
        "is_retryable": False,
        "guidance":     (
            "Check your text: it must be non-empty, at least 2 characters, "
            "and within the character limit."
        ),
    },
    ErrorCategory.LANGUAGE: {
        "title":        "Language Not Supported",
        "icon":         "🌍",
        "severity":     "warning",
        "is_retryable": False,
        "guidance":     (
            "This language is not supported by the selected engine. "
            "Try switching to gTTS (supports 52 languages) in your .env, "
            "or choose a different language."
        ),
    },
    ErrorCategory.TIMEOUT: {
        "title":        "Request Timed Out",
        "icon":         "⏱️",
        "severity":     "error",
        "is_retryable": True,
        "guidance":     (
            "The synthesis took too long. "
            "Try with shorter text, or check your connection speed."
        ),
    },
    ErrorCategory.RATE_LIMIT: {
        "title":        "API Quota Exceeded",
        "icon":         "📊",
        "severity":     "warning",
        "is_retryable": False,
        "guidance":     (
            "You've reached your ElevenLabs usage limit for this period. "
            "Switch to TTS_ENGINE=gtts (no quota) or upgrade your ElevenLabs plan."
        ),
    },
    ErrorCategory.UNKNOWN: {
        "title":        "Unexpected Error",
        "icon":         "❌",
        "severity":     "error",
        "is_retryable": True,
        "guidance":     (
            "An unexpected error occurred. "
            "Check the application logs for details, or try again."
        ),
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def format_error_message(
    exc: Exception,
    engine: str = "unknown",
) -> ErrorInfo:
    """
    Convert any exception into a fully resolved, display-ready ErrorInfo.

    Args:
        exc:    The exception to classify and format.
        engine: Active engine name for log context ("gtts" | "elevenlabs").

    Returns:
        ErrorInfo with all display fields populated.
    """
    category = classify_error(exc)
    content = _CATEGORY_CONTENT[category]

    # Build the user-facing message from exception details
    exc_str = str(exc)
    if hasattr(exc, "reason"):
        exc_str = exc.reason  # TTSSynthesisError carries a clean reason
    message = _sanitize_message(exc_str)

    logger.error(
        "TTS error [engine=%s, category=%s]: %s",
        engine, category.value, str(exc)
    )

    return ErrorInfo(
        category=category,
        title=content["title"],
        message=message,
        guidance=content["guidance"],
        icon=content["icon"],
        severity=content["severity"],
        is_retryable=content["is_retryable"],
        raw_error=exc,
    )


def is_retryable(exc: Exception) -> bool:
    """
    Quick check: should the user be offered a retry for this error?

    Args:
        exc: Any exception.

    Returns:
        True if the error is transient and worth retrying.
    """
    category = classify_error(exc)
    return _CATEGORY_CONTENT[category]["is_retryable"]


def get_guidance(category: ErrorCategory) -> str:
    """
    Return the guidance string for a given error category.

    Args:
        category: An ErrorCategory enum value.

    Returns:
        Actionable guidance string.
    """
    return _CATEGORY_CONTENT.get(category, _CATEGORY_CONTENT[ErrorCategory.UNKNOWN])["guidance"]


# ---------------------------------------------------------------------------
# Streamlit render function
# ---------------------------------------------------------------------------

def render_error_feedback(error_info: ErrorInfo) -> None:
    """
    Render a styled error card in the current Streamlit context.

    Displays: icon + title + message + guidance + optional retry note.

    Args:
        error_info: Resolved ErrorInfo from format_error_message().
    """
    import streamlit as st

    severity_fn = {
        "error":   st.error,
        "warning": st.warning,
        "info":    st.info,
    }.get(error_info.severity, st.error)

    severity_fn(
        f"{error_info.icon} **{error_info.title}**\n\n"
        f"{error_info.message}"
    )

    if error_info.guidance:
        with st.expander("💡 How to fix this", expanded=True):
            st.markdown(error_info.guidance)

    if error_info.is_retryable:
        st.caption("ℹ️ This error may be temporary — try submitting again.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sanitize_message(raw: str) -> str:
    """
    Clean an exception message string for safe display in the UI.

    Strips API keys, URLs, and stack frames that shouldn't reach users.

    Args:
        raw: Raw exception string.

    Returns:
        Cleaned, user-safe string.
    """
    if not raw:
        return "An error occurred."

    # Truncate very long messages
    if len(raw) > 300:
        raw = raw[:297] + "..."

    # Remove common noise strings
    noise = ["Traceback (most recent call last)", "File \"", "line "]
    for n in noise:
        if n in raw:
            return "An internal error occurred. See logs for details."

    return raw
