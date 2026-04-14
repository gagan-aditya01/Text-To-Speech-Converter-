"""
audio_player.py
---------------
Reusable Streamlit component for audio playback, download, and history.

Two-layer pattern:
  1. Pure logic functions  — format_file_size, estimate_duration,
                             build_audio_metadata, add_to_session_history,
                             get_session_history
                             → independently testable, no Streamlit dependency
  2. Render function       — render_audio_player()
                             → thin Streamlit wrapper

Usage:
    from app.components.audio_player import render_audio_player, add_to_session_history
    import streamlit as st

    # After synthesis:
    result_data = {
        "audio_bytes": result.audio_bytes,
        "mime_type": "audio/mpeg",
        "file_name": "tts_gtts_en_20240501.mp3",
        "lang": "English",
        "flag": "🇺🇸",
        "chars": 42,
        "engine": "gtts",
        "file_size_kb": 12.4,
        "mood": "neutral",
        "voice_gender": "female",
        "speed": 1.0,
    }
    add_to_session_history(st.session_state, result_data)
    render_audio_player(result_data)
"""

from typing import Optional
import streamlit as st

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Estimated characters per second at 1.0x speed
# Based on average speech rate ~150 words/min, ~5 chars/word = 12.5 chars/sec
_CHARS_PER_SECOND_NORMAL = 12.5

# Maximum number of history entries to retain per session
MAX_HISTORY_ENTRIES = 10

_SESSION_HISTORY_KEY = "audio_history"
_SESSION_LAST_RESULT_KEY = "last_result"


# ---------------------------------------------------------------------------
# Pure Logic Functions
# ---------------------------------------------------------------------------

def format_file_size(size_bytes: int) -> str:
    """
    Format a byte count as a human-readable file size string.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Formatted string e.g. "12.4 KB", "1.2 MB", "512 B".
    """
    if size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 ** 2):.2f} MB"


def estimate_duration(char_count: int, speed: float = 1.0) -> str:
    """
    Estimate playback duration from character count and speed.

    Uses a rough average of 12.5 characters per second at 1.0x speed.
    Not suitable for precise timing — intended as a quick UI hint.

    Args:
        char_count: Number of characters in the synthesized text.
        speed:      Playback speed multiplier (0.5–2.0).

    Returns:
        Human-readable duration string e.g. "~5 sec", "~1 min 20 sec".
    """
    if char_count <= 0:
        return "< 1 sec"

    effective_speed = max(speed, 0.1)  # Guard against zero/negative
    total_seconds = char_count / (_CHARS_PER_SECOND_NORMAL * effective_speed)
    total_seconds = round(total_seconds)

    if total_seconds < 60:
        return f"~{total_seconds} sec"

    minutes = total_seconds // 60
    seconds = total_seconds % 60
    if seconds == 0:
        return f"~{minutes} min"
    return f"~{minutes} min {seconds} sec"


def build_audio_metadata(result_data: dict) -> dict:
    """
    Build a display-ready metadata dict from a raw result_data dict.

    Computes derived fields (duration, formatted size) alongside
    the raw fields needed by the UI.

    Args:
        result_data: Dict with keys: audio_bytes, lang, flag, chars,
                     engine, file_name, mood, voice_gender, speed.

    Returns:
        Metadata dict with all display fields resolved.
    """
    audio_bytes = result_data.get("audio_bytes", b"")
    char_count = result_data.get("chars", 0)
    speed = result_data.get("speed", 1.0)

    return {
        "lang": result_data.get("lang", "Unknown"),
        "flag": result_data.get("flag", "🌐"),
        "engine": result_data.get("engine", "gtts").upper(),
        "chars": char_count,
        "file_name": result_data.get("file_name", "audio.mp3"),
        "file_size": format_file_size(len(audio_bytes)),
        "duration": estimate_duration(char_count, speed),
        "mood": result_data.get("mood", "neutral").title(),
        "voice_gender": result_data.get("voice_gender", "female").title(),
        "speed": speed,
    }


def add_to_session_history(session_state: dict, result_data: dict) -> None:
    """
    Prepend a result entry to the in-session audio history.

    Keeps only the most recent MAX_HISTORY_ENTRIES entries and
    strips the raw audio_bytes to keep memory usage low.

    Args:
        session_state: Streamlit's st.session_state (or any dict in tests).
        result_data:   The result dict to store.
    """
    if _SESSION_HISTORY_KEY not in session_state:
        session_state[_SESSION_HISTORY_KEY] = []

    # Store a lightweight copy (no raw audio bytes in history)
    entry = {k: v for k, v in result_data.items() if k != "audio_bytes"}
    entry["audio_bytes"] = result_data.get("audio_bytes", b"")  # keep for replay

    history: list = session_state[_SESSION_HISTORY_KEY]
    history.insert(0, entry)

    # Trim to limit
    session_state[_SESSION_HISTORY_KEY] = history[:MAX_HISTORY_ENTRIES]


def get_session_history(session_state: dict) -> list[dict]:
    """
    Return the current in-session audio history list.

    Args:
        session_state: Streamlit's st.session_state (or any dict in tests).

    Returns:
        List of result dicts, newest first. Empty list if no history.
    """
    return session_state.get(_SESSION_HISTORY_KEY, [])


def truncate_label(text: str, max_chars: int = 40) -> str:
    """
    Truncate a string for display in compact history items.

    Args:
        text:      Input string.
        max_chars: Maximum length before truncation.

    Returns:
        Original string, or truncated with "…" appended.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "…"


# ---------------------------------------------------------------------------
# Streamlit Render Function
# ---------------------------------------------------------------------------

def render_audio_player(result_data: dict) -> None:
    """
    Render the audio player, metadata panel, and download button.

    Args:
        result_data: Output dict from the conversion pipeline, containing:
                     audio_bytes, mime_type, file_name, lang, flag,
                     chars, engine, mood, voice_gender, speed.
    """
    meta = build_audio_metadata(result_data)

    st.divider()
    st.markdown("### 🎧 Generated Audio")

    # Metadata ribbon
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Language", f"{meta['flag']} {meta['lang']}")
    with col2:
        st.metric("Duration", meta["duration"])
    with col3:
        st.metric("File Size", meta["file_size"])
    with col4:
        st.metric("Engine", meta["engine"])

    # Secondary metadata row
    st.markdown(
        f'<p style="color:#64748B; font-size:0.78rem; margin-top:-10px;">'
        f"Voice: {meta['voice_gender']} · Mood: {meta['mood']} · "
        f"Speed: {meta['speed']}x · {meta['chars']:,} characters</p>",
        unsafe_allow_html=True,
    )

    # Audio player
    st.audio(
        result_data["audio_bytes"],
        format=result_data.get("mime_type", "audio/mpeg"),
    )

    # Download button
    st.download_button(
        label="⬇️ Download MP3",
        data=result_data["audio_bytes"],
        file_name=meta["file_name"],
        mime=result_data.get("mime_type", "audio/mpeg"),
        key="audio_download_btn",
        use_container_width=True,
    )


def render_history_panel(session_state: dict) -> None:
    """
    Render a collapsible recent conversion history panel.

    Shows language, timestamp (from filename), file size and a
    replay button for each past conversion in the session.

    Args:
        session_state: Streamlit's st.session_state.
    """
    history = get_session_history(session_state)
    if not history:
        return

    st.divider()
    with st.expander(f"📜 Recent Conversions ({len(history)})", expanded=False):
        for i, entry in enumerate(history):
            meta = build_audio_metadata(entry)
            cols = st.columns([1, 3, 1, 1])
            with cols[0]:
                st.markdown(f"**{meta['flag']}**")
            with cols[1]:
                st.markdown(
                    f"<small>{meta['lang']} · {meta['chars']:,} chars · "
                    f"{meta['file_size']}</small>",
                    unsafe_allow_html=True,
                )
            with cols[2]:
                st.markdown(f"<small>{meta['duration']}</small>", unsafe_allow_html=True)
            with cols[3]:
                if st.button("▶", key=f"replay_{i}", help="Replay this audio"):
                    st.session_state[_SESSION_LAST_RESULT_KEY] = entry
            st.audio(entry["audio_bytes"], format=entry.get("mime_type", "audio/mpeg"))
