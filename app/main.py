"""
main.py
-------
VoiceCraft — Multi-Language TTS Converter
Streamlit application entry point.

Run with:
    streamlit run app/main.py
    # or:
    make run

Architecture (Phases 7–16):
    Phase 7  — Entry point scaffold
    Phase 8  — render_language_selector() component
    Phase 9  — render_text_input() component
    Phase 10 — render_audio_player() + render_history_panel()
    Phase 11 — render_voice_selector() component
    Phase 12 — ElevenLabs engine
    Phase 13 — Engine router (config-driven engine selection)
    Phase 14 — Centralized error handler
    Phase 15 — Integration tests
    Phase 16 — UI polish & final styling (this file)
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of CWD
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging

import streamlit as st

from app.components.audio_player import (
    add_to_session_history,
    render_audio_player,
    render_history_panel,
)
from app.components.language_selector import render_language_selector
from app.components.text_input import render_text_input
from app.components.voice_selector import render_voice_selector
from app.config.settings import settings
from app.services.base_tts import BaseTTSService, TTSRequest, TTSSynthesisError
from app.services.engine_router import get_tts_service as _get_engine
from app.services.translation_service import translate_text
from app.styles.css import get_full_css
from app.utils.audio_utils import cleanup_old_files, get_mime_type, save_audio
from app.utils.error_handler import format_error_message, render_error_feedback
from app.utils.logger import setup_logging

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

setup_logging(log_level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="VoiceCraft — Multi-Language TTS",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/gagan-aditya01/Text-To-Speech-Converter-",
        "Report a bug": "https://github.com/gagan-aditya01/Text-To-Speech-Converter-/issues",
        "About": "VoiceCraft — Multi-Language TTS Converter · Built with gTTS + Streamlit",
    },
)

# Inject full design system CSS + Google Fonts
st.markdown(get_full_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached resources
# ---------------------------------------------------------------------------

@st.cache_resource
def get_tts_service() -> BaseTTSService:
    """Return the active TTS engine — cached per session, config-driven."""
    return _get_engine()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    # Header row: title + engine badge
    engine = settings.TTS_ENGINE.lower()
    badge_class = f"engine-badge-{engine}"
    dot_class = f"engine-dot engine-dot-{engine}"
    st.markdown(
        "## ⚙️ Voice Settings",
        unsafe_allow_html=True,
    )
    st.divider()

    # Language selector (Phase 8)
    selected_lang = render_language_selector(
        engine=engine,
        key_prefix="sidebar",
        default_code=settings.DEFAULT_LANGUAGE,
    )

    st.divider()

    # Voice selector (Phase 11)
    voice_config = render_voice_selector(
        engine=engine,
        key_prefix="sidebar",
        default_gender=settings.DEFAULT_GENDER,
        default_speed=1.0,
    )

    st.divider()

    # Quick stats
    st.markdown(
        '<p style="color:#475569; font-size:0.72rem; text-align:center; '
        'padding-top:0.5rem;">'
        "52 Languages · MP3 Output · Session History</p>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main — Hero
# ---------------------------------------------------------------------------

st.markdown(
    '<h1 class="hero-title">🗣️ VoiceCraft</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="hero-sub">Multi-Language AI Voice Synthesizer</p>',
    unsafe_allow_html=True,
)

# Stat badges row
if engine == "gtts":
    active_engine_label = "gTTS Engine"
elif engine == "edgetts":
    active_engine_label = "EdgeTTS Neural"
else:
    active_engine_label = "ElevenLabs Engine"
    
st.markdown(
    f'<span class="stat-badge">🌐 52 Languages</span>'
    f'<span class="stat-badge">⚡ {active_engine_label}</span>'
    f'<span class="stat-badge">🎵 MP3 Output</span>'
    f'<span class="stat-badge">📜 Session History</span>',
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Main — Text Input (Phase 9)
# ---------------------------------------------------------------------------

text_input, text_is_valid = render_text_input(
    language_code=selected_lang["code"],
    max_length=settings.MAX_TEXT_LENGTH,
    key_prefix="main",
    height=185,
)

# Config summary bar
st.info(
    f"**{selected_lang['flag']} {selected_lang['name']}** · "
    f"**{voice_config['gender']}** voice · "
    f"**{voice_config['speed']}x** {voice_config['speed_label']}"
)

# Convert button
convert_clicked = st.button(
    "🎙️ Convert to Speech",
    key="convert_btn",
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Conversion logic
# ---------------------------------------------------------------------------

if convert_clicked:
    if not text_is_valid:
        st.error("⚠️ Please enter valid text before converting.")
    else:
        try:
            with st.spinner(f"🌍 Translating to {selected_lang['name']}..."):
                translated_text = translate_text(text_input.strip(), selected_lang["code"])

            if translated_text.lower() != text_input.strip().lower():
                st.info(f"**Translated Text ({selected_lang['name']}):**\n\n{translated_text}")

            with st.spinner("✨ Synthesizing audio..."):
                service = get_tts_service()

                request = TTSRequest(
                    text=translated_text,
                    language_code=selected_lang["code"],
                    voice_gender=voice_config["gender"],
                    mood=voice_config["mood"],
                    speed=voice_config["speed"],
                )

                result = service.synthesize(request)

                file_path = save_audio(result, output_dir=settings.OUTPUT_DIR)
                cleanup_old_files(
                    output_dir=settings.OUTPUT_DIR,
                    max_files=settings.MAX_OUTPUT_FILES,
                )

                char_count = len(text_input.strip())
                logger.info(
                    "Synthesis complete | engine=%s | lang=%s | chars=%d | file=%s",
                    engine, selected_lang["code"], char_count, file_path.name,
                )

                result_data = {
                    "audio_bytes": result.audio_bytes,
                    "mime_type": get_mime_type(result.audio_format),
                    "file_name": file_path.name,
                    "lang": selected_lang["name"],
                    "flag": selected_lang["flag"],
                    "chars": char_count,
                    "engine": result.engine,
                    "mood": voice_config["mood"],
                    "voice_gender": voice_config["gender"],
                    "speed": voice_config["speed"],
                    "file_size_kb": round(len(result.audio_bytes) / 1024, 2),
                }
                st.session_state["last_result"] = result_data
                add_to_session_history(st.session_state, result_data)

                # Celebrate first-time synthesis
                if st.session_state.get("synthesis_count", 0) == 0:
                    st.balloons()
                st.session_state["synthesis_count"] = (
                    st.session_state.get("synthesis_count", 0) + 1
                )
                st.success(
                    f"✅ Audio ready! "
                    f"{selected_lang['flag']} {selected_lang['name']} · "
                    f"{char_count:,} characters"
                )

        except Exception as exc:
            error_info = format_error_message(exc, engine=engine)
            render_error_feedback(error_info)

# ---------------------------------------------------------------------------
# Audio player (Phase 10) + History (Phase 10)
# ---------------------------------------------------------------------------

if "last_result" in st.session_state:
    render_audio_player(st.session_state["last_result"])

render_history_panel(st.session_state)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    '<div class="app-footer">'
    "VoiceCraft &nbsp;·&nbsp; "
    f"Engine: <strong>{engine.upper()}</strong> &nbsp;·&nbsp; "
    "Built with gTTS + Streamlit &nbsp;·&nbsp; "
    "Phase 16 of 17 &nbsp;·&nbsp; "
    '<a href="https://github.com/gagan-aditya01/Text-To-Speech-Converter-" '
    'target="_blank">GitHub</a>'
    "</div>",
    unsafe_allow_html=True,
)
