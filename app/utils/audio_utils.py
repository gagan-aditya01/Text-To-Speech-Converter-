"""
audio_utils.py
--------------
Audio file I/O utilities for the TTS application.

Responsibilities:
    - Save TTSResult audio bytes to the outputs directory
    - Generate timestamped, collision-safe filenames
    - Provide MIME type lookup for Streamlit's audio player
    - Clean up old output files to prevent disk bloat
    - List output files sorted by recency

Architecture note:
    The service layer (GTTSService, ElevenLabsService) is intentionally
    stateless — it never touches the filesystem. This module is the single
    point responsible for all audio file I/O.
"""

import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services.base_tts import TTSResult

logger = logging.getLogger(__name__)

# Default output directory — relative to project root.
# Can be overridden by callers or config (Phase 6).
DEFAULT_OUTPUT_DIR = Path("outputs")

# Supported audio formats and their MIME types
_MIME_TYPE_MAP: dict[str, str] = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "aac": "audio/aac",
    "flac": "audio/flac",
}


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_audio(
    result: TTSResult,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    custom_name: Optional[str] = None,
) -> Path:
    """
    Persist TTS audio bytes to disk and return the file path.

    Args:
        result:      TTSResult from any TTS engine.
        output_dir:  Directory to write the file into (created if absent).
        custom_name: Optional filename stem override (without extension).
                     If omitted, a timestamped name is auto-generated.

    Returns:
        Path to the saved audio file.

    Raises:
        OSError: If the file cannot be written.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{custom_name}.{result.audio_format}"
        if custom_name
        else build_filename(result)
    )
    file_path = output_dir / filename

    file_path.write_bytes(result.audio_bytes)

    logger.info("Audio saved | path=%s | bytes=%d", file_path, len(result.audio_bytes))
    return file_path


# ---------------------------------------------------------------------------
# Filename generation
# ---------------------------------------------------------------------------

def build_filename(result: TTSResult) -> str:
    """
    Generate a unique, human-readable filename for a TTS result.

    Format: tts_<engine>_<lang>_<YYYYMMDD_HHMMSS>_<hash4>.<format>
    Example: tts_gtts_hi_20240501_143022_a3f1.mp3

    The 4-char hash suffix prevents collisions from rapid successive calls.

    Args:
        result: The TTSResult to name.

    Returns:
        Filename string including extension.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Short hash of audio content for uniqueness
    content_hash = hashlib.md5(result.audio_bytes).hexdigest()[:4]
    lang_safe = result.language_code.replace("-", "_").lower()

    return f"tts_{result.engine}_{lang_safe}_{timestamp}_{content_hash}.{result.audio_format}"


# ---------------------------------------------------------------------------
# MIME type
# ---------------------------------------------------------------------------

def get_mime_type(audio_format: str) -> str:
    """
    Return the MIME type string for a given audio format.

    Used by Streamlit's `st.audio()` and download buttons.

    Args:
        audio_format: Format string e.g. "mp3", "wav", "ogg".

    Returns:
        MIME type string. Falls back to "audio/mpeg" for unknown formats.
    """
    return _MIME_TYPE_MAP.get(audio_format.lower(), "audio/mpeg")


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def cleanup_old_files(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    max_files: int = 50,
) -> int:
    """
    Delete the oldest audio files when the output directory exceeds max_files.

    Files are ranked by modification time — oldest are removed first.
    Safe to call frequently (e.g. on every conversion).

    Args:
        output_dir: Directory to clean up.
        max_files:  Maximum number of audio files to retain.

    Returns:
        Number of files deleted. 0 if no cleanup was needed.
    """
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return 0

    audio_files = _list_audio_files(output_dir)  # newest-first

    excess = len(audio_files) - max_files
    if excess <= 0:
        return 0

    # Files to delete = the tail (oldest, since list is newest-first)
    to_delete = audio_files[max_files:]
    deleted = 0
    for file_path in to_delete:
        try:
            file_path.unlink()
            deleted += 1
            logger.debug("Deleted old audio file: %s", file_path)
        except OSError as exc:
            logger.warning("Could not delete %s: %s", file_path, exc)

    logger.info("Cleanup complete | deleted=%d | retained=%d", deleted, max_files)
    return deleted


# ---------------------------------------------------------------------------
# Directory listing
# ---------------------------------------------------------------------------

def list_output_files(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[Path]:
    """
    Return all audio files in the output directory, newest first.

    Args:
        output_dir: Directory to scan.

    Returns:
        List of Path objects sorted by modification time (descending).
        Empty list if the directory doesn't exist or has no audio files.
    """
    output_dir = Path(output_dir)
    if not output_dir.exists():
        return []
    return _list_audio_files(output_dir)


def get_file_size_kb(file_path: Path) -> float:
    """
    Return the size of a file in kilobytes, rounded to 2 decimal places.

    Args:
        file_path: Path to the file.

    Returns:
        File size in KB. Returns 0.0 if file does not exist.
    """
    try:
        return round(os.path.getsize(file_path) / 1024, 2)
    except OSError:
        return 0.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _list_audio_files(directory: Path) -> list[Path]:
    """
    Return audio files in a directory, sorted newest-first by mtime.
    Only includes files with extensions present in the MIME type map.
    """
    extensions = {f".{ext}" for ext in _MIME_TYPE_MAP}
    files = [
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in extensions
    ]
    # Sort by modification time, descending (newest first)
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)
