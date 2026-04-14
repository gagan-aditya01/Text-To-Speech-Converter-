"""
css.py
------
Centralized, Streamlit-Cloud-safe CSS for VoiceCraft.

This version:
  - Uses @import inside <style> (works in Streamlit Cloud sandbox)
  - Avoids [data-testid] selectors (version-unstable, break on Cloud)
  - Uses .stApp, .main, element-level selectors only (stable across versions)
  - Every rule has !important where needed to beat Streamlit defaults
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
    background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 55%, #16213E 100%) !important;
}

header[data-testid="stHeader"], .stHeader {
    background: transparent !important;
    border-bottom: 1px solid rgba(124,58,237,0.15) !important;
}

.main .block-container {
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 860px !important;
}

/* ── SIDEBAR ────────────────────────────────────────────── */
section[data-testid="stSidebar"], .css-1d391kg, .css-163ttbj {
    background: rgba(15,15,26,0.95) !important;
    border-right: 1px solid rgba(124,58,237,0.25) !important;
}

/* ── HERO TITLE ─────────────────────────────────────────── */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.hero-title {
    font-size: 2.8rem !important;
    font-weight: 800 !important;
    background: linear-gradient(270deg, #7C3AED, #A78BFA, #60A5FA, #7C3AED) !important;
    background-size: 300% 300% !important;
    animation: gradientShift 6s ease infinite !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em !important;
    margin-bottom: 0.1rem !important;
}

.hero-sub {
    color: #94A3B8 !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    margin-bottom: 0.5rem !important;
}

/* ── STAT BADGES ─────────────────────────────────────────── */
.stat-badge {
    display: inline-block;
    background: rgba(124,58,237,0.12);
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 20px;
    padding: 0.22rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: #A78BFA;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
    transition: all 0.2s ease;
    cursor: default;
}
.stat-badge:hover {
    background: rgba(124,58,237,0.22);
    transform: translateY(-1px);
}

/* ── ENGINE BADGE ────────────────────────────────────────── */
.engine-badge-gtts {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.12);
    border: 1px solid rgba(16,185,129,0.4);
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.72rem; font-weight: 600; color: #10B981;
}
.engine-badge-elevenlabs {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(245,158,11,0.12);
    border: 1px solid rgba(245,158,11,0.4);
    border-radius: 20px; padding: 0.2rem 0.7rem;
    font-size: 0.72rem; font-weight: 600; color: #F59E0B;
}
@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.5; transform:scale(1.3); }
}
.engine-dot {
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block; animation: pulse-dot 2s infinite;
}
.engine-dot-gtts        { background: #10B981; }
.engine-dot-elevenlabs  { background: #F59E0B; }

/* ── BUTTONS ─────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #7C3AED, #5B21B6) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.8rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.35) !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 28px rgba(124,58,237,0.55) !important;
}
.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* Download button — distinct green */
.stDownloadButton > button {
    background: rgba(16,185,129,0.1) !important;
    border: 1.5px solid rgba(16,185,129,0.45) !important;
    color: #10B981 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: rgba(16,185,129,0.2) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 14px rgba(16,185,129,0.25) !important;
}

/* ── TEXT AREA ───────────────────────────────────────────── */
.stTextArea textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124,58,237,0.3) !important;
    font-size: 0.97rem !important;
    background: rgba(15,15,26,0.7) !important;
    color: #E2E8F0 !important;
    line-height: 1.65 !important;
    transition: border-color 0.2s ease !important;
}
.stTextArea textarea:focus {
    border-color: rgba(124,58,237,0.7) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}
.stTextArea textarea::placeholder { color: #475569 !important; }

/* ── TEXT INPUT ──────────────────────────────────────────── */
.stTextInput input {
    border-radius: 8px !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    background: rgba(15,15,26,0.6) !important;
    color: #E2E8F0 !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput input:focus {
    border-color: rgba(124,58,237,0.6) !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.1) !important;
}
.stTextInput input::placeholder { color: #475569 !important; }

/* ── SELECTBOX ───────────────────────────────────────────── */
.stSelectbox > div > div {
    background: rgba(26,26,46,0.85) !important;
    border: 1px solid rgba(124,58,237,0.25) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

/* ── ALERTS ──────────────────────────────────────────────── */
.stAlert {
    border-radius: 10px !important;
    border-left-width: 3px !important;
    font-size: 0.9rem !important;
}

/* ── EXPANDER ────────────────────────────────────────────── */
.stExpander {
    background: rgba(26,26,46,0.5) !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 12px !important;
}

/* ── RADIO ───────────────────────────────────────────────── */
.stRadio > div { gap: 0.4rem !important; flex-wrap: wrap !important; }
.stRadio label {
    background: rgba(26,26,46,0.6) !important;
    border: 1px solid rgba(124,58,237,0.2) !important;
    border-radius: 8px !important;
    padding: 0.3rem 0.65rem !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    color: #CBD5E1 !important;
}
.stRadio label:hover {
    border-color: rgba(124,58,237,0.55) !important;
    background: rgba(124,58,237,0.1) !important;
}

/* ── SLIDER ──────────────────────────────────────────────── */
.stSlider .thumb { background: #7C3AED !important; }
.stSlider .track-fill { background: #7C3AED !important; }

/* ── AUDIO PLAYER ────────────────────────────────────────── */
audio {
    width: 100% !important;
    border-radius: 10px !important;
    margin: 0.5rem 0 !important;
    outline: none !important;
}

/* ── METRICS (custom cards via html) ────────────────────── */
.metric-card {
    background: rgba(26,26,46,0.75);
    border: 1px solid rgba(124,58,237,0.2);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    transition: all 0.22s ease;
    text-align: center;
}
.metric-card:hover {
    border-color: rgba(124,58,237,0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(124,58,237,0.15);
}
.metric-label {
    color: #94A3B8;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.25rem;
}
.metric-value {
    color: #E2E8F0;
    font-size: 1.05rem;
    font-weight: 600;
}

/* ── DIVIDERS ────────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid rgba(124,58,237,0.15) !important;
    margin: 1rem 0 !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(15,15,26,0.5); }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.4); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.65); }

/* ── CAPTIONS ────────────────────────────────────────────── */
.stCaption, small { color: #64748B !important; font-size: 0.76rem !important; }

/* ── SECTION LABEL UTILITY ───────────────────────────────── */
.section-label {
    color: #A78BFA;
    font-size: 0.73rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
}

/* ── SCRIPT HINT ─────────────────────────────────────────── */
.script-hint {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    font-size: 0.83rem;
    color: #FCD34D;
    margin-bottom: 0.5rem;
    line-height: 1.5;
}

/* ── FOOTER ──────────────────────────────────────────────── */
.app-footer {
    text-align: center;
    color: #374151;
    font-size: 0.73rem;
    padding: 0.5rem 0;
    border-top: 1px solid rgba(124,58,237,0.1);
    margin-top: 1rem;
}
.app-footer a { color: #7C3AED; text-decoration: none; }
.app-footer a:hover { text-decoration: underline; }
</style>
"""


def get_full_css() -> str:
    """Return complete CSS for injection into Streamlit via st.markdown()."""
    return MAIN_CSS
