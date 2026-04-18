"""
edgetts_service.py
------------------
Concrete TTS implementation using the Edge TTS engine.

Capabilities:
    - Native male/female distinct voices.
    - Highly refined neural voice models (equivalent to ElevenLabs).
    - Free tier without API keys.
"""

import asyncio
import io
import logging

import edge_tts

from app.services.base_tts import BaseTTSService, TTSRequest, TTSResult, TTSSynthesisError
from app.utils.language_data import get_all_languages

logger = logging.getLogger(__name__)

# Cache for edge-tts voices to avoid querying every time
_EDGE_VOICES_CACHE = []

async def _get_best_voice(lang_code: str, gender: str) -> str:
    """Finds the best Microsoft neural voice ID for a given language code and gender."""
    global _EDGE_VOICES_CACHE
    if not _EDGE_VOICES_CACHE:
        try:
            _EDGE_VOICES_CACHE = await edge_tts.list_voices()
        except getattr(edge_tts, "NoNetworkError", Exception) as e:
             logger.warning("Could not fetch edge_tts voices, fallback to defaults: %s", e)
             return "en-US-GuyNeural" if gender == "male" else "en-US-AriaNeural"
             
    # Try to find an exact locale match
    # language_code might be 'zh-CN', 'en', 'fr', etc.
    target_locale_prefix = lang_code.split("-")[0].lower()
    target_gender = "Male" if gender == "male" else "Female"
    
    # Heuristic matching: try to match full locale first (if lang_code is e.g. en-US)
    # Then fallback to prefix matching (e.g. en-*)
    
    candidates = []
    for v in _EDGE_VOICES_CACHE:
        if v["Gender"] == target_gender:
            v_locale = v["Locale"].lower()
            if lang_code.lower() == v_locale:
               return v["Name"]
            if v_locale.startswith(target_locale_prefix):
               candidates.append(v["Name"])
               
    if candidates:
        return candidates[0]
        
    # Ultimate fallback if no matching language is found
    logger.warning("No edge-tts voice found for lang=%s gender=%s. Falling back to en-US.", lang_code, target_gender)
    return "en-US-GuyNeural" if target_gender == "Male" else "en-US-AriaNeural"


async def _synthesize_async(request: TTSRequest) -> tuple[bytes, str]:
    """Async workflow to grab the voice ID and stream the TTS audio."""
    voice_id = await _get_best_voice(request.language_code, request.voice_gender)
    
    # Adjust speed rate (pitch/rate strings for edge-tts: +0%, -50%, etc.)
    # 0.5x = -50%, 1.0x = +0%, 2.0x = +100%
    rate_pct = int((request.speed - 1.0) * 100)
    rate_str = f"+{rate_pct}%" if rate_pct >= 0 else f"{rate_pct}%"
    
    communicate = edge_tts.Communicate(request.text, voice_id, rate=rate_str)
    
    audio_buffer = io.BytesIO()
    
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_buffer.write(chunk["data"])
            
    return audio_buffer.getvalue(), voice_id


class EdgeTTSService(BaseTTSService):
    """
    TTS engine backed by Microsoft Edge Neural Voices.
    """

    @property
    def engine_name(self) -> str:
        return "edgetts"

    def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Convert text to MP3 audio bytes using edge-tts.
        """
        # Guard: check language support before hitting the network
        self.validate_request(request)

        logger.info(
            "Synthesizing via EdgeTTS | lang=%s | gender=%s | chars=%d",
            request.language_code,
            request.voice_gender,
            len(request.text),
        )

        try:
            # We run the async flow completely blocking so Streamlit just waits for completion.
            audio_bytes, resolved_voice_id = asyncio.run(_synthesize_async(request))

        except Exception as exc:
            # Catch-all: network timeouts, unexpected API changes, etc.
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason=f"Unexpected error during EdgeTTS synthesis: {exc}",
            ) from exc

        if not audio_bytes:
            raise TTSSynthesisError(
                engine=self.engine_name,
                reason="EdgeTTS returned empty audio data.",
            )

        logger.info(
            "Synthesis complete | voice=%s | bytes=%d", resolved_voice_id, len(audio_bytes)
        )

        return TTSResult(
            audio_bytes=audio_bytes,
            language_code=request.language_code,
            engine=self.engine_name,
            audio_format="mp3",
            metadata={
                "mood": request.mood,
                "voice_gender": request.voice_gender,
                "voice_id": resolved_voice_id,
                "speed": request.speed,
                "char_count": len(request.text),
            },
        )

    def get_supported_language_codes(self) -> list[str]:
        """
        Return BCP-47 codes. We will gracefully map gtts supported languages,
        as edge-tts supports virtually all of them.
        """
        return [
            lang["code"]
            for lang in get_all_languages(engine="gtts")
            # We piggyback off gtts registry for simplicity since Edge supports 80+ locales
        ]
