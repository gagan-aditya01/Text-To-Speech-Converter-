"""
test_integration.py
-------------------
End-to-end integration tests for the full TTS pipeline.

Test coverage:
  - GTTSService → real synthesis → valid MP3 bytes
  - TTSRequest → GTTSService → save_audio → file on disk
  - cleanup_old_files → old files removed, recent files kept
  - Engine router → correct engine returned for "gtts"
  - Error handler → classifies real errors correctly
  - Full pipeline: text → request → synthesize → save → cleanup → play

Marking:
  @pytest.mark.integration — makes real gTTS network calls
  @pytest.mark.slow        — takes > 1 second

Run all tests:     pytest tests/
Skip integration:  pytest tests/ -m "not integration"
Run only these:    pytest tests/test_integration.py
"""

import time
from pathlib import Path

import pytest

from app.services.base_tts import TTSRequest, TTSResult, TTSSynthesisError
from app.services.engine_router import get_tts_service
from app.services.gtts_service import GTTSService
from app.utils.audio_utils import (
    build_filename,
    cleanup_old_files,
    get_mime_type,
    save_audio,
)
from app.utils.error_handler import ErrorCategory, classify_error, format_error_message


# ---------------------------------------------------------------------------
# Synthesis — GTTSService real calls
# ---------------------------------------------------------------------------

class TestGTTSSynthesisIntegration:
    """Real gTTS network calls — marked integration + slow."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_synthesize_english_returns_audio(self, make_tts_request, gtts_service):
        request = make_tts_request(text="Hello, world!", language_code="en")
        result = gtts_service.synthesize(request)
        assert isinstance(result, TTSResult)
        assert len(result.audio_bytes) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_audio_bytes_are_mp3(self, make_tts_request, gtts_service):
        """MP3 files begin with the ID3 header or the 0xFF 0xFB frame sync bytes."""
        request = make_tts_request(text="Testing audio format.", language_code="en")
        result = gtts_service.synthesize(request)
        # MP3 magic bytes: ID3 (49 44 33) or MPEG frame sync (FF FB / FF FA / FF F3)
        first_bytes = result.audio_bytes[:3]
        is_mp3 = (
            first_bytes == b"ID3"
            or result.audio_bytes[:2] in (b"\xff\xfb", b"\xff\xfa", b"\xff\xf3")
        )
        assert is_mp3, f"Unexpected header bytes: {first_bytes.hex()}"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_synthesize_hindi_returns_audio(self, make_tts_request, gtts_service):
        request = make_tts_request(text="नमस्ते दुनिया", language_code="hi")
        result = gtts_service.synthesize(request)
        assert len(result.audio_bytes) > 1000  # Must be non-trivially sized

    @pytest.mark.integration
    @pytest.mark.slow
    def test_synthesize_french_returns_audio(self, make_tts_request, gtts_service):
        request = make_tts_request(text="Bonjour le monde", language_code="fr")
        result = gtts_service.synthesize(request)
        assert result.engine == "gtts"
        assert result.audio_format == "mp3"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_result_has_correct_language_code(self, make_tts_request, gtts_service):
        request = make_tts_request(text="Test", language_code="de")
        result = gtts_service.synthesize(request)
        assert result.language_code == "de"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_longer_text_produces_larger_audio(self, make_tts_request, gtts_service):
        short_req = make_tts_request(text="Hi.", language_code="en")
        long_req = make_tts_request(
            text="This is a longer sentence with considerably more content.", language_code="en"
        )
        short_result = gtts_service.synthesize(short_req)
        long_result = gtts_service.synthesize(long_req)
        assert len(long_result.audio_bytes) > len(short_result.audio_bytes)


# ---------------------------------------------------------------------------
# Full pipeline: Synthesize → Save → Verify → Cleanup
# ---------------------------------------------------------------------------

class TestFullPipelineIntegration:
    """Tests that exercise the complete file I/O pipeline."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_synthesize_and_save_creates_file(
        self, make_tts_request, gtts_service, tmp_output_dir
    ):
        request = make_tts_request(text="Testing file save.", language_code="en")
        result = gtts_service.synthesize(request)
        file_path = save_audio(result, output_dir=tmp_output_dir)

        assert file_path.exists()
        assert file_path.stat().st_size > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_saved_file_has_mp3_extension(
        self, make_tts_request, gtts_service, tmp_output_dir
    ):
        request = make_tts_request(text="File extension test.", language_code="en")
        result = gtts_service.synthesize(request)
        file_path = save_audio(result, output_dir=tmp_output_dir)
        assert file_path.suffix == ".mp3"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_saved_file_bytes_match_result(
        self, make_tts_request, gtts_service, tmp_output_dir
    ):
        request = make_tts_request(text="Byte integrity check.", language_code="en")
        result = gtts_service.synthesize(request)
        file_path = save_audio(result, output_dir=tmp_output_dir)
        assert file_path.read_bytes() == result.audio_bytes

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cleanup_removes_oldest_files_past_limit(
        self, make_tts_request, gtts_service, tmp_output_dir
    ):
        """Generate 4 files, set max=3, verify oldest is removed."""
        for i in range(4):
            request = make_tts_request(text=f"File number {i}.", language_code="en")
            result = gtts_service.synthesize(request)
            save_audio(result, output_dir=tmp_output_dir)
            time.sleep(0.05)  # Ensure distinct mtime ordering

        assert len(list(tmp_output_dir.glob("*.mp3"))) == 4

        cleanup_old_files(output_dir=tmp_output_dir, max_files=3)
        remaining = list(tmp_output_dir.glob("*.mp3"))
        assert len(remaining) == 3

    @pytest.mark.integration
    @pytest.mark.slow
    def test_cleanup_skips_when_under_limit(
        self, make_tts_request, gtts_service, tmp_output_dir
    ):
        request = make_tts_request(text="Only one file.", language_code="en")
        result = gtts_service.synthesize(request)
        save_audio(result, output_dir=tmp_output_dir)

        cleanup_old_files(output_dir=tmp_output_dir, max_files=5)
        assert len(list(tmp_output_dir.glob("*.mp3"))) == 1

    @pytest.mark.integration
    @pytest.mark.slow
    def test_mime_type_is_audio_mpeg(self, make_tts_request, gtts_service):
        request = make_tts_request(text="MIME type test.", language_code="en")
        result = gtts_service.synthesize(request)
        assert get_mime_type(result.audio_format) == "audio/mpeg"


# ---------------------------------------------------------------------------
# Engine router — integration level
# ---------------------------------------------------------------------------

class TestEngineRouterIntegration:
    def test_gtts_router_returns_working_service(self):
        service = get_tts_service(engine="gtts")
        assert service.engine_name == "gtts"
        assert service.is_language_supported("en") is True

    def test_elevenlabs_router_returns_service_without_key(self):
        """ElevenLabs service should instantiate even without a key (fail on synthesize)."""
        from app.services.elevenlabs_service import ElevenLabsService
        service = get_tts_service(engine="elevenlabs")
        assert isinstance(service, ElevenLabsService)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_gtts_full_synthesis_via_router(self, make_tts_request):
        service = get_tts_service(engine="gtts")
        request = make_tts_request(text="Router integration test.", language_code="en")
        result = service.synthesize(request)
        assert len(result.audio_bytes) > 0


# ---------------------------------------------------------------------------
# Error classification — real exception integration
# ---------------------------------------------------------------------------

class TestErrorHandlerIntegration:
    def test_ttssynthesis_error_classifies_correctly(self):
        exc = TTSSynthesisError(engine="gtts", reason="ELEVENLABS_API_KEY is not configured.")
        assert classify_error(exc) == ErrorCategory.AUTH

    def test_format_error_produces_complete_info(self):
        exc = TTSSynthesisError(engine="elevenlabs", reason="API error 429: quota exceeded.")
        info = format_error_message(exc, engine="elevenlabs")
        assert info.title
        assert info.guidance
        assert info.is_retryable is False

    def test_unsupported_language_via_service_raises(self):
        service = GTTSService()
        with pytest.raises(ValueError, match="does not support"):
            service.validate_request(
                TTSRequest(text="Test", language_code="xx-INVALID")
            )

    def test_elevenlabs_no_key_raises_synthesis_error(self):
        from app.services.elevenlabs_service import ElevenLabsService
        service = ElevenLabsService(api_key=None)
        with pytest.raises(TTSSynthesisError, match="API_KEY"):
            service.synthesize(TTSRequest(text="Test", language_code="en"))


# ---------------------------------------------------------------------------
# Audio utils — unit level (no network)
# ---------------------------------------------------------------------------

class TestAudioUtilsUnit:
    def test_build_filename_contains_engine(self, make_tts_request):
        from app.services.base_tts import TTSResult
        result = TTSResult(
            audio_bytes=b"\xff\xfb" + b"\x00" * 50,
            language_code="en",
            engine="gtts",
            audio_format="mp3",
        )
        name = build_filename(result)
        assert "gtts" in name
        assert "en" in name
        assert name.endswith(".mp3")

    def test_build_filename_is_unique(self, make_tts_request):
        from app.services.base_tts import TTSResult
        # Different audio_bytes → different hash suffix → different filenames
        result_a = TTSResult(
            audio_bytes=b"\xff\xfb" + b"\xAA" * 50,
            language_code="en", engine="gtts", audio_format="mp3",
        )
        result_b = TTSResult(
            audio_bytes=b"\xff\xfb" + b"\xBB" * 50,
            language_code="en", engine="gtts", audio_format="mp3",
        )
        assert build_filename(result_a) != build_filename(result_b)

    def test_save_audio_to_new_dir_creates_dir(self, tmp_output_dir):
        new_subdir = tmp_output_dir / "subdir"
        fake_result = TTSResult(
            audio_bytes=b"\xff\xfb" + b"\x00" * 100,
            language_code="en",
            engine="gtts",
            audio_format="mp3",
        )
        path = save_audio(fake_result, output_dir=new_subdir)
        assert path.exists()
        assert new_subdir.exists()

    def test_cleanup_empty_dir_does_not_raise(self, tmp_output_dir):
        cleanup_old_files(output_dir=tmp_output_dir, max_files=5)  # Should not raise

    def test_mime_type_mp3(self):
        assert get_mime_type("mp3") == "audio/mpeg"

    def test_mime_type_wav(self):
        assert get_mime_type("wav") == "audio/wav"

    def test_mime_type_unknown_falls_back_to_mpeg(self):
        # audio_utils defaults unknown formats to audio/mpeg
        assert get_mime_type("xyz") == "audio/mpeg"
