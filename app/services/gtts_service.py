"""
gtts_service.py
---------------
Concrete TTS implementation using Google Text-to-Speech (gTTS).

Capabilities:
    - 50+ languages (pulled from our language registry)
    - Slow/normal speed control
    - Stateless synthesis — returns raw MP3 bytes via in-memory buffer

Limitations (documented intentionally):
    - No native male/female voice differentiation (gTTS produces one voice per language)
    - No mood/tone control — these fields are stored in metadata for future engine use
    - Speed is binary: slow (< 1.0x) or normal (>= 1.0x) — gTTS API constraint
    → Full voice/mood support arrives in Phase 12 via ElevenLabs

Architecture note:
    This class knows nothing about files, Streamlit, or the UI.
    It accepts a TTSRequest, returns a TTSResult. That's its entire job.
"""

import io
import logging

from gtts import gTTS
from gtts.tts import gTTSError

from app.services.base_tts import BaseTTSService, TTSRequest, TTSResult, TTSSynthesisError
from app.utils.language_data import get_all_languages

logger = logging.getLogger(__name__)


class GTTSService(BaseTTSService):
    """
    TTS engine backed by Google Text-to-Speech (gTTS).

    Usage:
        service = GTTSService()
        request = TTSRequest(text="Hello, world!", language_code="en")
        result  = service.synthesize(request)
        # result.audio_bytes → raw MP3 bytes ready to play or save
    """

    @property
    def engine_name(self) -> str:
        return "gtts"

    # ------------------------------------------------------------------
    # Core synthesis
    # ------------------------------------------------------------------

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Convert text to MP3 audio bytes using gTTS.

        Args:
            request: Validated TTSRequest instance.

        Returns:
            TTSResult with raw MP3 bytes.

        Raises:
            TTSSynthesisError: Wraps any gTTS or network-level error.
        """
        # Guard: check language support before hitting the network
        self.validate_request(request)

        # gTTS only has two speed modes — map float speed to boolean
        slow_mode = request.speed < 1.0

        logger.info(
            "Synthesizing via gTTS | lang=%s | slow=%s | chars=%d",
            request.language_code,
            slow_mode,
            len(request.text),
        )

        try:
            tts = gTTS(
                text=request.text,
                lang=request.language_code,
                slow=slow_mode,
            )

            # Write audio to an in-memory buffer — no temp files needed
            buffer = io.BytesIO()
            tts.write_to_fp(buffer)
            buffer.seek(0)
            audio_bytes = buffer.read()

        except gTTSError as exc:
            # gTTS-specific errors (bad lang code, empty response, etc.)
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"gTTS engine error: {exc}",
            ) from exc
        except Exception as exc:
            # Catch-all: network timeouts, unexpected API changes, etc.
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"Unexpected error during synthesis: {exc}",
            ) from exc

        logger.info(
            "Synthesis complete | bytes=%d", len(audio_bytes)
        )

        return TTSResult(
            audio_bytes=audio_bytes,
            language_code=request.language_code,
            engine=self.engine_name,
            audio_format="mp3",
            metadata={
                "slow_mode": slow_mode,
                # mood/voice_gender stored here for future engine use
                "mood": request.mood,
                "voice_gender": request.voice_gender,
                "char_count": len(request.text),
            },
        )

    # ------------------------------------------------------------------
    # Language support
    # ------------------------------------------------------------------

    def get_supported_language_codes(self) -> list[str]:
        """
        Return BCP-47 codes for all languages marked gtts_supported in
        the language registry. Truth lives in languages.json — not here.
        """
        return [
            lang["code"]
            for lang in get_all_languages(engine="gtts")
        ]
