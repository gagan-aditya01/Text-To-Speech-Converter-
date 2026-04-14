"""
conftest.py
-----------
Shared pytest fixtures for the full test suite.

Fixtures are scoped to avoid redundant setup/teardown and keep tests fast.
"""

import shutil
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Output directory fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_output_dir():
    """
    Create a fresh temporary output directory for each test.
    Guaranteed to be cleaned up after the test, even on failure.
    """
    dir_path = Path(tempfile.mkdtemp(prefix="tts_test_"))
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


# ---------------------------------------------------------------------------
# TTSRequest factory fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def make_tts_request():
    """
    Factory fixture: returns a callable that builds TTSRequest objects
    with sensible defaults, letting tests override only what they need.

    Usage:
        def test_something(make_tts_request):
            req = make_tts_request(text="Hello!", language_code="fr")
    """
    from app.services.base_tts import TTSRequest

    def _factory(
        text="Hello, this is a test.",
        language_code="en",
        voice_gender="female",
        mood="neutral",
        speed=1.0,
        voice_id=None,
    ) -> TTSRequest:
        return TTSRequest(
            text=text,
            language_code=language_code,
            voice_gender=voice_gender,
            mood=mood,
            speed=speed,
            voice_id=voice_id,
        )

    return _factory


# ---------------------------------------------------------------------------
# gTTS service fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def gtts_service():
    """
    Session-scoped GTTSService instance.
    Shared across all tests that need it — avoids repeated construction.
    """
    from app.services.gtts_service import GTTSService
    return GTTSService()
