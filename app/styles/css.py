"""
css.py
------
Centralized, Streamlit-Cloud-safe CSS for VoiceCraft.

This version:
  - Uses @import inside <style>
  - Avoids [data-testid] selectors where possible
  - Implements a sophisticated, professional Beige/Off-white Light Mode aesthetics.
"""

MAIN_CSS = """
<style>
/* ── GOOGLE FONTS ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── GLOBAL RESET ──────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp, .stApp *, div, p, span, label, input, textarea, select {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── BACKGROUND ─────────────────────────────────────────── */
.stApp {
    background: linear-gradient(135deg, #F9F7F3 0%, #FAF8F6 55%, #F0EDE5 100%) !important;
    color: #2C2C2C !important;
}

header[data-testid="stHeader"], .stHeader {
    background: transparent !important;
    border-bottom: 1px solid rgba(139,115,85,0.15) !important;
}

.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 860px !important;
}

/* ── SIDEBAR ────────────────────────────────────────────── */
section[data-testid="stSidebar"], .css-1d391kg, .css-163ttbj {
    background: #F2EFE9 !important;
    border-right: 1px solid rgba(139,115,85,0.2) !important;
}

/* ── HERO TITLE ─────────────────────────────────────────── */
.hero-title {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    color: #2C2C2C !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.1rem !important;
}

.hero-sub {
    color: #5C5C5C !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    margin-bottom: 0.5rem !important;
}

/* ── STAT BADGES ─────────────────────────────────────────── */
.stat-badge {
    display: inline-block;
    background: #FFFFFF;
    border: 1px solid #D3CEC4;
    border-radius: 20px;
    padding: 0.22rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 600;
    color: #4A4A4A;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    transition: all 0.2s ease;
    cursor: default;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.stat-badge:hover {
    background: #FAFAFA;
    border-color: #8B7355;
    transform: translateY(-1px);
}

/* ── ENGINE BADGE ────────────────────────────────────────── */
.engine-badge-gtts {
    display: inline-flex; align-items: center; gap: 6px;
    background: #E8F5E9; border: 1px solid #A5D6A7;
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.72rem; font-weight: 600; color: #2E7D32;
}
.engine-badge-edgetts {
    display: inline-flex; align-items: center; gap: 6px;
    background: #E3F2FD; border: 1px solid #90CAF9;
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.72rem; font-weight: 600; color: #1565C0;
}
.engine-badge-elevenlabs {
    display: inline-flex; align-items: center; gap: 6px;
    background: #FFF3E0; border: 1px solid #FFCC80;
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.72rem; font-weight: 600; color: #EF6C00;
}
@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.5; transform:scale(1.3); }
}
.engine-dot {
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block; animation: pulse-dot 2s infinite;
}
.engine-dot-gtts        { background: #4CAF50; }
.engine-dot-edgetts     { background: #2196F3; }
.engine-dot-elevenlabs  { background: #FF9800; }

/* ── BUTTONS ─────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #8B7355, #6B573F) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.65rem 1.8rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 10px rgba(139,115,85,0.3) !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(139,115,85,0.4) !important;
}
.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* Download button */
.stDownloadButton > button {
    background: #FFFFFF !important;
    border: 1.5px solid #8B7355 !important;
    color: #8B7355 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: #FAFAFA !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 10px rgba(139,115,85,0.1) !important;
}

/* ── TEXT AREA ───────────────────────────────────────────── */
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid #D3CEC4 !important;
    font-size: 0.97rem !important;
    background: #FFFFFF !important;
    color: #2C2C2C !important;
    line-height: 1.65 !important;
    transition: border-color 0.2s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
}
.stTextArea textarea:focus {
    border-color: #8B7355 !important;
    box-shadow: 0 0 0 3px rgba(139,115,85,0.15) !important;
}
.stTextArea textarea::placeholder { color: #8F8B83 !important; }

/* ── TEXT INPUT ──────────────────────────────────────────── */
.stTextInput input {
    border-radius: 6px !important;
    border: 1px solid #D3CEC4 !important;
    background: #FFFFFF !important;
    color: #2C2C2C !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput input:focus {
    border-color: #8B7355 !important;
    box-shadow: 0 0 0 2px rgba(139,115,85,0.1) !important;
}
.stTextInput input::placeholder { color: #8F8B83 !important; }

/* ── SELECTBOX ───────────────────────────────────────────── */
.stSelectbox > div > div {
    background: #FFFFFF !important;
    border: 1px solid #D3CEC4 !important;
    border-radius: 6px !important;
    color: #2C2C2C !important;
}

/* ── ALERTS ──────────────────────────────────────────────── */
.stAlert {
    border-radius: 8px !important;
    border-left-width: 4px !important;
    font-size: 0.9rem !important;
    background: #FFFFFF !important;
    border-color: #8B7355 !important;
    color: #2C2C2C !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03) !important;
}

/* ── EXPANDER ────────────────────────────────────────────── */
.stExpander {
    background: #FFFFFF !important;
    border: 1px solid #E8E5DF !important;
    border-radius: 8px !important;
}

/* ── RADIO ───────────────────────────────────────────────── */
.stRadio > div { gap: 0.4rem !important; flex-wrap: wrap !important; }
.stRadio label {
    background: #FFFFFF !important;
    border: 1px solid #D3CEC4 !important;
    border-radius: 6px !important;
    padding: 0.3rem 0.65rem !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    color: #4B4B4B !important;
}
.stRadio label:hover {
    border-color: #8B7355 !important;
    background: #F9F7F3 !important;
}

/* ── SLIDER ──────────────────────────────────────────────── */
.stSlider .thumb { background: #8B7355 !important; }
.stSlider .track-fill { background: #8B7355 !important; }

/* ── AUDIO PLAYER ────────────────────────────────────────── */
audio {
    width: 100% !important;
    border-radius: 6px !important;
    margin: 0.5rem 0 !important;
    outline: none !important;
}

/* ── METRICS (custom cards via html) ────────────────────── */
.metric-card {
    background: #FFFFFF;
    border: 1px solid #E8E5DF;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    transition: all 0.22s ease;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.metric-card:hover {
    border-color: #C0B7A6;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
}
.metric-label {
    color: #8F8B83;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.25rem;
}
.metric-value {
    color: #2C2C2C;
    font-size: 1.05rem;
    font-weight: 600;
}

/* ── DIVIDERS ────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid #D3CEC4 !important;
    margin: 1.2rem 0 !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F9F7F3; }
::-webkit-scrollbar-thumb { background: #D3CEC4; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #8B7355; }

/* ── CAPTIONS ────────────────────────────────────────────── */
.stCaption, small { color: #8F8B83 !important; font-size: 0.76rem !important; }

/* ── SECTION LABEL UTILITY ───────────────────────────────── */
.section-label {
    color: #8B7355;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* ── SCRIPT HINT ─────────────────────────────────────────── */
.script-hint {
    background: #FFFAF0;
    border: 1px solid #F6E0B5;
    border-radius: 6px;
    padding: 0.6rem 0.9rem;
    font-size: 0.83rem;
    color: #A67C00;
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

/* ── FOOTER ──────────────────────────────────────────────── */
.app-footer {
    text-align: center;
    color: #8F8B83;
    font-size: 0.73rem;
    padding: 0.5rem 0;
    border-top: 1px solid #E8E5DF;
    margin-top: 1rem;
}
.app-footer a { color: #8B7355; text-decoration: none; }
.app-footer a:hover { text-decoration: underline; }
</style>
"""

def get_full_css() -> str:
    """Return complete CSS for injection into Streamlit via st.markdown()."""
    return MAIN_CSS
