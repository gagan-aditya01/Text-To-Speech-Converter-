"""
test_audio_utils.py
-------------------
Unit tests for app/utils/audio_utils.py

Uses pytest's `tmp_path` fixture for all filesystem operations —
no files are ever written to the real outputs/ directory.
"""

import time
from pathlib import Path

import pytest

from app.services.base_tts import TTSResult
from app.utils.audio_utils import (
    build_filename,
    cleanup_old_files,
    get_file_size_kb,
    get_mime_type,
    list_output_files,
    save_audio,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_result(
    audio_bytes: bytes = b"fake_mp3_data",
    language_code: str = "en",
    engine: str = "gtts",
    audio_format: str = "mp3",
) -> TTSResult:
    """Factory for TTSResult test instances."""
    return TTSResult(
        audio_bytes=audio_bytes,
        language_code=language_code,
        engine=engine,
        audio_format=audio_format,
    )


# ---------------------------------------------------------------------------
# build_filename tests
# ---------------------------------------------------------------------------

class TestBuildFilename:
    def test_returns_string(self):
        result = make_result()
        assert isinstance(build_filename(result), str)

    def test_contains_engine(self):
        result = make_result(engine="gtts")
        assert "gtts" in build_filename(result)

    def test_contains_language_code(self):
        result = make_result(language_code="hi")
        assert "hi" in build_filename(result)

    def test_hyphens_in_lang_code_replaced(self):
        result = make_result(language_code="zh-CN")
        name = build_filename(result)
        assert "-" not in name.split(".")[0]

    def test_has_correct_extension(self):
        result = make_result(audio_format="mp3")
        assert build_filename(result).endswith(".mp3")

    def test_different_content_produces_different_names(self):
        r1 = make_result(audio_bytes=b"audio_one")
        r2 = make_result(audio_bytes=b"audio_two")
        # Hash suffix should differ
        assert build_filename(r1) != build_filename(r2)

    def test_filename_has_timestamp_component(self):
        result = make_result()
        name = build_filename(result)
        # Timestamp format: YYYYMMDD_HHMMSS — 15 digits + underscore
        parts = name.split("_")
        # At least one part should be 8 digits (date) and one 6 digits (time)
        date_parts = [p for p in parts if p.isdigit() and len(p) == 8]
        assert len(date_parts) >= 1


# ---------------------------------------------------------------------------
# save_audio tests
# ---------------------------------------------------------------------------

class TestSaveAudio:
    def test_file_is_created(self, tmp_path):
        result = make_result()
        path = save_audio(result, output_dir=tmp_path)
        assert path.exists()

    def test_file_content_matches_bytes(self, tmp_path):
        content = b"expected_audio_bytes"
        result = make_result(audio_bytes=content)
        path = save_audio(result, output_dir=tmp_path)
        assert path.read_bytes() == content

    def test_output_dir_is_created_if_absent(self, tmp_path):
        new_dir = tmp_path / "nested" / "outputs"
        assert not new_dir.exists()
        result = make_result()
        save_audio(result, output_dir=new_dir)
        assert new_dir.exists()

    def test_returns_path_object(self, tmp_path):
        result = make_result()
        path = save_audio(result, output_dir=tmp_path)
        assert isinstance(path, Path)

    def test_custom_name_overrides_auto_name(self, tmp_path):
        result = make_result()
        path = save_audio(result, output_dir=tmp_path, custom_name="my_audio")
        assert path.name == "my_audio.mp3"

    def test_file_extension_matches_format(self, tmp_path):
        result = make_result(audio_format="wav")
        path = save_audio(result, output_dir=tmp_path)
        assert path.suffix == ".wav"


# ---------------------------------------------------------------------------
# get_mime_type tests
# ---------------------------------------------------------------------------

class TestGetMimeType:
    def test_mp3_mime(self):
        assert get_mime_type("mp3") == "audio/mpeg"

    def test_wav_mime(self):
        assert get_mime_type("wav") == "audio/wav"

    def test_ogg_mime(self):
        assert get_mime_type("ogg") == "audio/ogg"

    def test_case_insensitive(self):
        assert get_mime_type("MP3") == "audio/mpeg"
        assert get_mime_type("WAV") == "audio/wav"

    def test_unknown_format_fallback(self):
        assert get_mime_type("xyz_unknown") == "audio/mpeg"


# ---------------------------------------------------------------------------
# list_output_files tests
# ---------------------------------------------------------------------------

class TestListOutputFiles:
    def test_empty_dir_returns_empty_list(self, tmp_path):
        assert list_output_files(tmp_path) == []

    def test_nonexistent_dir_returns_empty_list(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        assert list_output_files(missing) == []

    def test_returns_only_audio_files(self, tmp_path):
        (tmp_path / "audio.mp3").write_bytes(b"x")
        (tmp_path / "readme.txt").write_bytes(b"y")
        files = list_output_files(tmp_path)
        assert all(f.suffix in {".mp3", ".wav", ".ogg"} for f in files)
        assert len(files) == 1

    def test_sorted_newest_first(self, tmp_path):
        old = tmp_path / "old.mp3"
        new = tmp_path / "new.mp3"
        old.write_bytes(b"old")
        time.sleep(0.05)  # ensure different mtime
        new.write_bytes(b"new")
        files = list_output_files(tmp_path)
        assert files[0].name == "new.mp3"
        assert files[1].name == "old.mp3"


# ---------------------------------------------------------------------------
# cleanup_old_files tests
# ---------------------------------------------------------------------------

class TestCleanupOldFiles:
    def _create_mp3_files(self, directory: Path, count: int) -> list[Path]:
        """Create `count` fake MP3 files with slight mtime spacing."""
        paths = []
        for i in range(count):
            p = directory / f"audio_{i:03d}.mp3"
            p.write_bytes(b"x" * (i + 1))
            time.sleep(0.01)
            paths.append(p)
        return paths

    def test_no_cleanup_when_under_limit(self, tmp_path):
        self._create_mp3_files(tmp_path, 5)
        deleted = cleanup_old_files(tmp_path, max_files=10)
        assert deleted == 0

    def test_deletes_excess_files(self, tmp_path):
        self._create_mp3_files(tmp_path, 10)
        deleted = cleanup_old_files(tmp_path, max_files=5)
        assert deleted == 5

    def test_retains_newest_files(self, tmp_path):
        files = self._create_mp3_files(tmp_path, 6)
        cleanup_old_files(tmp_path, max_files=3)
        remaining = list_output_files(tmp_path)
        remaining_names = {f.name for f in remaining}
        # Newest 3 should remain
        newest = {files[-1].name, files[-2].name, files[-3].name}
        assert newest == remaining_names

    def test_returns_zero_for_missing_dir(self, tmp_path):
        missing = tmp_path / "no_such_dir"
        assert cleanup_old_files(missing, max_files=5) == 0


# ---------------------------------------------------------------------------
# get_file_size_kb tests
# ---------------------------------------------------------------------------

class TestGetFileSizeKb:
    def test_returns_correct_size(self, tmp_path):
        f = tmp_path / "test.mp3"
        f.write_bytes(b"x" * 1024)
        assert get_file_size_kb(f) == 1.0

    def test_returns_zero_for_missing_file(self, tmp_path):
        missing = tmp_path / "ghost.mp3"
        assert get_file_size_kb(missing) == 0.0
