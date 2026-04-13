"""
base_tts.py
-----------
Abstract base class and shared data models for all TTS engine implementations.

Architecture note:
    Every TTS engine (gTTS, ElevenLabs, OpenAI, etc.) MUST subclass BaseTTSService
    and implement its abstract methods. This guarantees that:
      - The UI layer never depends on a specific engine
      - Engines can be swapped by changing a single config value
      - New engines can be added without touching any existing code
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Shared Data Models
# ---------------------------------------------------------------------------

@dataclass
class TTSRequest:
    """
    Encapsulates all parameters for a single TTS conversion request.

    Attributes:
        text:           The input text to synthesize.
        language_code:  BCP-47 language code e.g. "en", "hi", "zh-CN".
        voice_gender:   Preferred voice gender — "male" | "female" | "neutral".
        mood:           Desired tone/mood — "neutral" | "calm" | "energetic" | "formal".
        speed:          Playback speed multiplier. 1.0 = normal, 0.5 = slow, 1.5 = fast.
        voice_id:       Optional engine-specific voice ID (used by ElevenLabs).
    """
    text: str
    language_code: str
    voice_gender: str = "female"
    mood: str = "neutral"
    speed: float = 1.0
    voice_id: Optional[str] = None

    def __post_init__(self):
        """Validate fields immediately on construction."""
        if not self.text or not self.text.strip():
            raise ValueError("TTSRequest.text must not be empty.")
        if not self.language_code or not self.language_code.strip():
            raise ValueError("TTSRequest.language_code must not be empty.")
        if self.voice_gender not in ("male", "female", "neutral"):
            raise ValueError(
                f"Invalid voice_gender '{self.voice_gender}'. "
                "Must be 'male', 'female', or 'neutral'."
            )
        if self.mood not in ("neutral", "calm", "energetic", "formal"):
            raise ValueError(
                f"Invalid mood '{self.mood}'. "
                "Must be 'neutral', 'calm', 'energetic', or 'formal'."
            )
        if not (0.5 <= self.speed <= 2.0):
            raise ValueError(
                f"Invalid speed '{self.speed}'. Must be between 0.5 and 2.0."
            )


@dataclass
class TTSResult:
    """
    Encapsulates the output from a successful TTS synthesis.

    Attributes:
        audio_bytes:    Raw audio data as bytes (ready to write to file or stream).
        language_code:  Language code used in the request.
        engine:         Name of the engine that produced this result.
        audio_format:   File format of the audio bytes — "mp3" | "wav" | "ogg".
        metadata:       Optional dict for engine-specific extra info.
    """
    audio_bytes: bytes
    language_code: str
    engine: str
    audio_format: str = "mp3"
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Abstract Base Class
# ---------------------------------------------------------------------------

class BaseTTSService(ABC):
    """
    Abstract interface that all TTS engine implementations must satisfy.

    Subclasses implement:
        - engine_name:                 Read-only identifier for the engine.
        - synthesize(request):         Core method — converts text to audio bytes.
        - get_supported_language_codes: Returns BCP-47 codes this engine handles.

    Subclasses inherit for free:
        - is_language_supported(code): Convenience checker.
        - validate_request(request):   Shared pre-synthesis guard.
    """

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """
        Human-readable, lowercase engine identifier.
        Examples: "gtts", "elevenlabs", "openai"
        """
        ...

    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResult:
        """
        Convert text to audio according to the given request parameters.

        Args:
            request: A validated TTSRequest instance.

        Returns:
            TTSResult containing audio bytes and metadata.

        Raises:
            TTSSynthesisError: If synthesis fails for any reason.
            ValueError:        If request parameters are invalid for this engine.
        """
        ...

    @abstractmethod
    def get_supported_language_codes(self) -> list[str]:
        """
        Return a list of BCP-47 language codes supported by this engine.

        Returns:
            e.g. ["en", "hi", "fr", "de", ...]
        """
        ...

    # ------------------------------------------------------------------
    # Concrete helpers — available to all subclasses at no extra cost
    # ------------------------------------------------------------------

    def is_language_supported(self, language_code: str) -> bool:
        """
        Check whether a given BCP-47 code is supported by this engine.

        Args:
            language_code: e.g. "hi"

        Returns:
            True if supported, False otherwise.
        """
        return language_code.lower() in [
            code.lower() for code in self.get_supported_language_codes()
        ]

    def validate_request(self, request: TTSRequest) -> None:
        """
        Shared pre-synthesis validation. Raises if the engine cannot
        handle the language in the given request.

        Args:
            request: The TTSRequest to validate.

        Raises:
            ValueError: If the language is not supported by this engine.
        """
        if not self.is_language_supported(request.language_code):
            raise ValueError(
                f"Engine '{self.engine_name}' does not support "
                f"language code '{request.language_code}'."
            )

    def __repr__(self) -> str:
        return f"<TTSService engine='{self.engine_name}'>"


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class TTSSynthesisError(Exception):
    """
    Raised when a TTS engine fails to synthesize audio.

    Wrap engine-specific errors (API timeouts, quota limits, etc.)
    in this exception so the UI layer handles one error type consistently.
    """
    def __init__(self, engine: str, reason: str):
        self.engine = engine
        self.reason = reason
        super().__init__(f"[{engine}] TTS synthesis failed: {reason}")
