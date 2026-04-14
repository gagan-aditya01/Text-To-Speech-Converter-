"""
main.py
-------
Streamlit application entry point for the Multi-Language TTS Converter.

Run with:
    streamlit run app/main.py

Architecture:
    This file wires together all service and utility layers built in Phases 1–7.
    Phase 8: language selection is now delegated to the reusable
    app/components/language_selector.py component.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `app.*` imports resolve
# regardless of the working directory Streamlit is launched from.
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
from app.utils.audio_utils import cleanup_old_files, get_mime_type, save_audio
from app.utils.logger import setup_logging

# ---------------------------------------------------------------------------
# Bootstrap — must happen before any st.* calls
# ---------------------------------------------------------------------------

setup_logging(log_level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="VoiceCraft — Multi-Language TTS",
    page_icon="🗣️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Cached resources — instantiated once per session
# ---------------------------------------------------------------------------

@st.cache_resource
def get_tts_service() -> BaseTTSService:
    """Return the active TTS engine, selected by settings.TTS_ENGINE."""
    return _get_engine()





# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
/* App background gradient */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(26, 26, 46, 0.95);
    border-right: 1px solid rgba(124, 58, 237, 0.3);
}

/* Primary button */
div.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #5B21B6);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 2rem;
    font-size: 1rem;
    font-weight: 600;
    width: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.4);
}
div.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.6);
}

/* Text area */
textarea {
    border-radius: 10px !important;
    border: 1px solid rgba(124, 58, 237, 0.4) !important;
    font-size: 1rem !important;
    background: rgba(15, 15, 26, 0.8) !important;
}

/* Success / error boxes */
.stAlert {
    border-radius: 10px !important;
}

/* Header gradient text */
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #A78BFA, #60A5FA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin-bottom: 0.2rem;
}
.hero-sub {
    color: #94A3B8;
    font-size: 1.05rem;
    margin-bottom: 2rem;
}
.stat-badge {
    display: inline-block;
    background: rgba(124, 58, 237, 0.15);
    border: 1px solid rgba(124, 58, 237, 0.4);
    border-radius: 20px;
    padding: 0.2rem 0.8rem;
    font-size: 0.8rem;
    color: #A78BFA;
    margin-right: 0.5rem;
}
.section-label {
    color: #A78BFA;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — Voice & Language options
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Voice Settings")
    st.divider()

    # Language selector — reusable component (Phase 8)
    selected_lang = render_language_selector(
        engine="gtts",
        key_prefix="sidebar",
        default_code=settings.DEFAULT_LANGUAGE,
    )

    # Voice selector — reusable component (Phase 11)
    voice_config = render_voice_selector(
        engine="gtts",
        key_prefix="sidebar",
        default_gender=settings.DEFAULT_GENDER,
        default_mood=settings.DEFAULT_MOOD,
        default_speed=1.0,
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------

# Hero header
st.markdown('<h1 class="hero-title">🗣️ VoiceCraft</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="hero-sub">Multi-Language AI Voice Synthesizer</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<span class="stat-badge">52 Languages</span>'
    '<span class="stat-badge">gTTS Engine</span>'
    '<span class="stat-badge">MP3 Output</span>',
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)

# Text input — reusable component (Phase 9)
text_input, text_is_valid = render_text_input(
    language_code=selected_lang["code"],
    max_length=settings.MAX_TEXT_LENGTH,
    key_prefix="main",
    height=180,
)

# Selected language display
st.info(
    f"**Selected:** {selected_lang['flag']} {selected_lang['name']} "
    f"· **Gender:** {voice_gender.title()} "
    f"· **Mood:** {mood.title()} "
    f"· **Speed:** {speed}x"
)

# Convert button
convert_clicked = st.button("🎙️ Convert to Speech", key="convert_btn", use_container_width=True)

# ---------------------------------------------------------------------------
# Conversion logic
# ---------------------------------------------------------------------------

if convert_clicked:
    if not text_is_valid:
        st.error("⚠️ Please enter valid text before converting.")
    else:
        with st.spinner("Synthesizing audio..."):
            try:
                service = get_tts_service()

                request = TTSRequest(
                    text=text_input.strip(),
                    language_code=selected_lang["code"],
                    voice_gender=voice_config["gender"],
                    mood=voice_config["mood"],
                    speed=voice_config["speed"],
                )

                result = service.synthesize(request)

                # Save to disk and clean up old files
                file_path = save_audio(result, output_dir=settings.OUTPUT_DIR)
                cleanup_old_files(
                    output_dir=settings.OUTPUT_DIR,
                    max_files=settings.MAX_OUTPUT_FILES,
                )

                logger.info(
                    "Conversion complete | lang=%s | chars=%d | file=%s",
                    selected_lang["code"], char_count, file_path.name,
                )

                # Build enriched result dict for session + component
                char_count = len(text_input.strip())
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

            except TTSSynthesisError as exc:
                st.error(f"❌ Synthesis failed: {exc.reason}")
                logger.error("Synthesis error: %s", exc)
            except ValueError as exc:
                st.error(f"❌ Invalid input: {exc}")
            except Exception as exc:
                st.error("❌ An unexpected error occurred. Please try again.")
                logger.exception("Unexpected error during conversion: %s", exc)

# Audio player — reusable component (Phase 10)
if "last_result" in st.session_state:
    render_audio_player(st.session_state["last_result"])

# Session history panel
render_history_panel(st.session_state)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    '<p style="text-align:center; color:#475569; font-size:0.78rem;">'
    f"VoiceCraft · Engine: {settings.TTS_ENGINE.upper()} · "
    "Phase 13 of 17</p>",
    unsafe_allow_html=True,
)
