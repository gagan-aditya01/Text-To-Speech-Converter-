"""
main.py
-------
Streamlit application entry point for the Multi-Language TTS Converter.

Run with:
    streamlit run app/main.py

Architecture:
    This file wires together all service and utility layers built in Phases 1–6.
    UI components (language selector, voice selector, audio player) will be
    extracted into app/components/ in Phases 8–10. For now all widget logic
    lives here for a clean, testable proof of concept.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path so `app.*` imports resolve
# regardless of the working directory Streamlit is launched from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import logging

import streamlit as st

from app.config.settings import settings
from app.services.base_tts import TTSRequest, TTSSynthesisError
from app.services.gtts_service import GTTSService
from app.utils.audio_utils import cleanup_old_files, get_mime_type, save_audio
from app.utils.language_data import format_display_label, get_all_languages
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
def get_tts_service() -> GTTSService:
    """Return a shared GTTSService instance (not re-created on every rerun)."""
    return GTTSService()


@st.cache_data
def get_language_options() -> list[dict]:
    """Return gTTS-supported languages, cached for the session."""
    return get_all_languages(engine="gtts")


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

    languages = get_language_options()
    lang_labels = [format_display_label(l) for l in languages]

    # Language search — filter the selectbox options dynamically
    st.markdown('<p class="section-label">🌐 Language</p>', unsafe_allow_html=True)
    lang_search = st.text_input(
        "Search language",
        placeholder="e.g. Hindi, French, zh...",
        label_visibility="collapsed",
        key="lang_search",
    )

    filtered_langs = (
        [l for l in languages if lang_search.lower() in l["name"].lower()
         or lang_search.lower() in l["native"].lower()
         or lang_search.lower() in l["code"].lower()]
        if lang_search
        else languages
    )

    if not filtered_langs:
        st.warning("No matching languages found.")
        filtered_langs = languages  # Fallback to full list

    filtered_labels = [format_display_label(l) for l in filtered_langs]

    # Find default index
    default_code = settings.DEFAULT_LANGUAGE
    default_idx = next(
        (i for i, l in enumerate(filtered_langs) if l["code"] == default_code), 0
    )

    selected_label = st.selectbox(
        "Select Language",
        options=filtered_labels,
        index=default_idx,
        label_visibility="collapsed",
        key="lang_select",
    )
    selected_lang = filtered_langs[filtered_labels.index(selected_label)]

    st.divider()

    # Voice gender
    st.markdown('<p class="section-label">🎙️ Voice Gender</p>', unsafe_allow_html=True)
    voice_gender = st.radio(
        "Voice Gender",
        options=["female", "male"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        key="voice_gender",
    )

    st.divider()

    # Tone / Mood
    st.markdown('<p class="section-label">🎭 Tone / Mood</p>', unsafe_allow_html=True)
    mood = st.select_slider(
        "Mood",
        options=["calm", "neutral", "formal", "energetic"],
        value="neutral",
        label_visibility="collapsed",
        key="mood",
    )

    st.divider()

    # Speed
    st.markdown('<p class="section-label">⚡ Speed</p>', unsafe_allow_html=True)
    speed = st.slider(
        "Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.25,
        label_visibility="collapsed",
        key="speed",
    )
    speed_label = "🐢 Slow" if speed < 1.0 else ("🐇 Fast" if speed > 1.0 else "▶️ Normal")
    st.caption(f"{speed_label} ({speed}x)")

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

# Text input
st.markdown('<p class="section-label">📝 Enter Text</p>', unsafe_allow_html=True)
text_input = st.text_area(
    "Text to convert",
    placeholder="Type or paste your text here...",
    height=160,
    max_chars=settings.MAX_TEXT_LENGTH,
    label_visibility="collapsed",
    key="text_input",
)

# Character counter
char_count = len(text_input)
counter_color = "#EF4444" if char_count > settings.MAX_TEXT_LENGTH * 0.9 else "#94A3B8"
st.markdown(
    f'<p style="text-align:right; color:{counter_color}; font-size:0.8rem;">'
    f'{char_count} / {settings.MAX_TEXT_LENGTH} characters</p>',
    unsafe_allow_html=True,
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
    if not text_input.strip():
        st.error("⚠️ Please enter some text before converting.")
    else:
        with st.spinner("Synthesizing audio..."):
            try:
                service = get_tts_service()

                request = TTSRequest(
                    text=text_input.strip(),
                    language_code=selected_lang["code"],
                    voice_gender=voice_gender,
                    mood=mood,
                    speed=speed,
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

                # Store result in session state for display
                st.session_state["last_result"] = {
                    "audio_bytes": result.audio_bytes,
                    "mime_type": get_mime_type(result.audio_format),
                    "file_name": file_path.name,
                    "lang": selected_lang["name"],
                    "flag": selected_lang["flag"],
                    "chars": char_count,
                }

            except TTSSynthesisError as exc:
                st.error(f"❌ Synthesis failed: {exc.reason}")
                logger.error("Synthesis error: %s", exc)
            except ValueError as exc:
                st.error(f"❌ Invalid input: {exc}")
            except Exception as exc:
                st.error("❌ An unexpected error occurred. Please try again.")
                logger.exception("Unexpected error during conversion: %s", exc)

# ---------------------------------------------------------------------------
# Audio player — persists across reruns via session state
# ---------------------------------------------------------------------------

if "last_result" in st.session_state:
    res = st.session_state["last_result"]

    st.divider()
    st.markdown("### 🎧 Generated Audio")

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"**{res['flag']} {res['lang']}** · {res['chars']} characters"
        )

    st.audio(res["audio_bytes"], format=res["mime_type"])

    st.download_button(
        label="⬇️ Download MP3",
        data=res["audio_bytes"],
        file_name=res["file_name"],
        mime=res["mime_type"],
        key="download_btn",
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    '<p style="text-align:center; color:#475569; font-size:0.78rem;">'
    "VoiceCraft · Built with gTTS + Streamlit · "
    "Phase 7 of 17</p>",
    unsafe_allow_html=True,
)
