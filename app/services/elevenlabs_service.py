"""
elevenlabs_service.py
---------------------
Concrete TTS implementation using the ElevenLabs API.

Capabilities:
    - High-quality neural voices with gender selection
    - Mood/tone control via voice_settings (stability, style, similarity_boost)
    - Multilingual support for 30+ languages via eleven_multilingual_v2 model
    - Returns raw MP3 bytes (same interface as GTTSService)

Prerequisites:
    - Set ELEVENLABS_API_KEY in .env
    - TTS_ENGINE=elevenlabs in .env

Architecture note:
    Implements BaseTTSService identically to GTTSService — the Streamlit UI
    and all components remain unchanged regardless of which engine is active.
    Engine selection happens via settings.TTS_ENGINE at app startup.

Limitations vs gTTS:
    - Requires an API key and internet connection
    - Consumes API credits per character
    - ElevenLabs free tier: 10,000 chars/month
"""

import logging
from typing import Optional

import requests

from app.config.settings import settings
from app.services.base_tts import (
    BaseTTSService,
    TTSRequest,
    TTSResult,
    TTSSynthesisError,
)
from app.utils.language_data import get_all_languages

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Voice & Mood Registries
# ---------------------------------------------------------------------------

# ElevenLabs pre-made voice IDs by gender.
# These are stable, publicly available voices from ElevenLabs' default library.
_DEFAULT_VOICE_IDS: dict[str, str] = {
    "female":  "EXAVITQu4vr4xnSDxMaL",   # Bella — warm, natural female voice
    "male":    "AZnzlk1XvdvUeBnXmlld",    # Domi  — clear, expressive male voice
    "neutral": "pNInz6obpgDQGcFmaJgB",    # Adam  — balanced, neutral voice
}

# Mood → ElevenLabs voice_settings mapping.
# stability:        0.0 (expressive) → 1.0 (consistent/monotone)
# similarity_boost: voice clarity/closeness to original voice (0.0–1.0)
# style:            expressiveness multiplier — only works on v2 models (0.0–1.0)
_MOOD_VOICE_SETTINGS: dict[str, dict] = {
    "neutral": {
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True,
    },
    "calm": {
        "stability": 0.8,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True,
    },
    "formal": {
        "stability": 0.9,
        "similarity_boost": 0.80,
        "style": 0.0,
        "use_speaker_boost": True,
    },
    "energetic": {
        "stability": 0.3,
        "similarity_boost": 0.70,
        "style": 0.5,
        "use_speaker_boost": True,
    },
}

# ElevenLabs API constants
_API_BASE_URL = "https://api.elevenlabs.io/v1"
_MODEL_ID = "eleven_multilingual_v2"   # Supports 30+ languages
_TIMEOUT_SECONDS = 30


# ---------------------------------------------------------------------------
# Pure helper functions (testable without network)
# ---------------------------------------------------------------------------

def get_voice_id(gender: str, voice_id_override: Optional[str] = None) -> str:
    """
    Resolve the ElevenLabs voice ID for a given gender preference.

    Args:
        gender:             "male" | "female" | "neutral"
        voice_id_override:  If provided, use this voice ID directly.
                            (Support for custom/cloned voices in future phases.)

    Returns:
        ElevenLabs voice ID string.
    """
    if voice_id_override:
        return voice_id_override
    return _DEFAULT_VOICE_IDS.get(gender, _DEFAULT_VOICE_IDS["neutral"])


def get_voice_settings(mood: str) -> dict:
    """
    Return ElevenLabs voice_settings dict for a given mood.

    Args:
        mood: "neutral" | "calm" | "formal" | "energetic"

    Returns:
        Dict with stability, similarity_boost, style, use_speaker_boost.
        Falls back to "neutral" settings for unknown moods.
    """
    return _MOOD_VOICE_SETTINGS.get(mood, _MOOD_VOICE_SETTINGS["neutral"])


def build_request_payload(request: TTSRequest) -> dict:
    """
    Build the JSON payload for the ElevenLabs TTS API endpoint.

    Args:
        request: Validated TTSRequest.

    Returns:
        Dict ready to send as JSON body.
    """
    return {
        "text": request.text,
        "model_id": _MODEL_ID,
        "voice_settings": get_voice_settings(request.mood),
    }


def get_elevenlabs_supported_codes() -> list[str]:
    """
    Return BCP-47 codes for languages marked elevenlabs_supported in the registry.
    """
    return [
        lang["code"]
        for lang in get_all_languages(engine="elevenlabs")
    ]


# ---------------------------------------------------------------------------
# ElevenLabs Service
# ---------------------------------------------------------------------------

class ElevenLabsService(BaseTTSService):
    """
    TTS engine backed by ElevenLabs API.

    Usage:
        service = ElevenLabsService()                    # uses settings
        service = ElevenLabsService(api_key="el_xxx")   # explicit key (testing)

        request = TTSRequest(
            text="Hello, world!",
            language_code="en",
            voice_gender="female",
            mood="calm",
        )
        result = service.synthesize(request)
        # result.audio_bytes → raw MP3 bytes
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise the ElevenLabs service.

        Args:
            api_key: API key override. Falls back to settings.ELEVENLABS_API_KEY.
        """
        self._api_key = api_key or settings.ELEVENLABS_API_KEY
        if not self._api_key:
            logger.warning(
                "ElevenLabsService initialised without an API key. "
                "Synthesis calls will fail. Set ELEVENLABS_API_KEY in .env."
            )

    # ------------------------------------------------------------------
    # BaseTTSService contract
    # ------------------------------------------------------------------

    @property
    def engine_name(self) -> str:
        return "elevenlabs"

    def get_supported_language_codes(self) -> list[str]:
        """Languages marked elevenlabs_supported=true in languages.json."""
        return get_elevenlabs_supported_codes()

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Convert text to high-quality MP3 audio via ElevenLabs API.

        Args:
            request: Validated TTSRequest.

        Returns:
            TTSResult with raw MP3 bytes.

        Raises:
            TTSSynthesisError: On missing API key, HTTP error, or network issues.
        """
        # Guard: API key must be present
        if not self._api_key:
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=(
                    "ELEVENLABS_API_KEY is not configured. "
                    "Add it to your .env file and restart the app."
                ),
            )

        # Guard: language must be supported
        self.validate_request(request)

        voice_id = get_voice_id(
            gender=request.voice_gender,
            voice_id_override=request.voice_id,
        )
        payload = build_request_payload(request)

        url = f"{_API_BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

        logger.info(
            "Synthesizing via ElevenLabs | lang=%s | voice=%s | mood=%s | chars=%d",
            request.language_code,
            voice_id,
            request.mood,
            len(request.text),
        )

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"Request timed out after {_TIMEOUT_SECONDS}s. Check your connection.",
            )
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            detail = _parse_api_error(exc.response)
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"API error {status}: {detail}",
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"Network error: {exc}",
            ) from exc

        audio_bytes = response.content
        logger.info("ElevenLabs synthesis complete | bytes=%d", len(audio_bytes))

        return TTSResult(
            audio_bytes=audio_bytes,
            language_code=request.language_code,
            engine=self.engine_name,
            audio_format="mp3",
            metadata={
                "voice_id": voice_id,
                "model_id": _MODEL_ID,
                "mood": request.mood,
                "voice_gender": request.voice_gender,
                "char_count": len(request.text),
                "voice_settings": get_voice_settings(request.mood),
            },
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_api_error(response: Optional[requests.Response]) -> str:
    """
    Extract a human-readable error message from an ElevenLabs error response.

    Args:
        response: The HTTP response object (may be None).

    Returns:
        Error detail string.
    """
    if response is None:
        return "No response received."
    try:
        body = response.json()
        return body.get("detail", {}).get("message", response.text)
    except Exception:
        return response.text or f"HTTP {response.status_code}"
