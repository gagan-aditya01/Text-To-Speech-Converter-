"""
css.py
------
Centralized CSS for the VoiceCraft Streamlit app.

Exporting CSS as a module constant (instead of inline strings in main.py):
  - Keeps main.py focused on logic
  - Makes styles reviewable and diffable
  - Allows easy theming by swapping this module

Design system:
  --primary:   #7C3AED  (violet-600)
  --secondary: #A78BFA  (violet-400)
  --accent:    #60A5FA  (blue-400)
  --bg:        #0F0F1A  (deep navy)
  --surface:   #1A1A2E  (dark surface)
  --surface2:  #16213E  (slightly lighter)
  --text:      #E2E8F0  (slate-200)
  --muted:     #94A3B8  (slate-400)
  --border:    rgba(124, 58, 237, 0.25)
"""

GOOGLE_FONTS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
"""

MAIN_CSS = """
<style>
/* ============================================================
   FONTS & GLOBAL RESET
   ============================================================ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ============================================================
   APP BACKGROUND
   ============================================================ */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0F0F1A 0%, #1A1A2E 50%, #16213E 100%);
    min-height: 100vh;
}

[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(124, 58, 237, 0.15);
}

/* Main content padding */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 860px;
}

/* ============================================================
   SIDEBAR — GLASSMORPHISM
   ============================================================ */
[data-testid="stSidebar"] {
    background: rgba(15, 15, 26, 0.9) !important;
    border-right: 1px solid rgba(124, 58, 237, 0.25);
    backdrop-filter: blur(20px);
}

[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}

/* Sidebar dividers */
[data-testid="stSidebar"] hr {
    border-color: rgba(124, 58, 237, 0.2);
    margin: 1rem 0;
}

/* ============================================================
   HERO TITLE — ANIMATED GRADIENT
   ============================================================ */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    background: linear-gradient(270deg, #7C3AED, #A78BFA, #60A5FA, #7C3AED);
    background-size: 300% 300%;
    animation: gradientShift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 0.25rem;
}

.hero-sub {
    color: #94A3B8;
    font-size: 1.05rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
    letter-spacing: 0.01em;
}

/* ============================================================
   STAT BADGES
   ============================================================ */
.stat-badge {
    display: inline-block;
    background: rgba(124, 58, 237, 0.12);
    border: 1px solid rgba(124, 58, 237, 0.35);
    border-radius: 20px;
    padding: 0.25rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 500;
    color: #A78BFA;
    margin-right: 0.4rem;
    margin-bottom: 0.4rem;
    transition: all 0.25s ease;
}
.stat-badge:hover {
    background: rgba(124, 58, 237, 0.25);
    border-color: rgba(124, 58, 237, 0.6);
    transform: translateY(-1px);
}

/* ============================================================
   ENGINE BADGE
   ============================================================ */
.engine-badge-gtts {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #10B981;
}
.engine-badge-elevenlabs {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 20px;
    padding: 0.2rem 0.75rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: #F59E0B;
}
.engine-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 2s infinite;
}
.engine-dot-gtts { background: #10B981; }
.engine-dot-elevenlabs { background: #F59E0B; }

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.6; transform: scale(1.25); }
}

/* ============================================================
   CONVERT BUTTON
   ============================================================ */
@keyframes gradientButton {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

div.stButton > button[kind="primary"],
div.stButton > button {
    background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 50%, #4C1D95 100%);
    background-size: 200% 200%;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    width: 100%;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35) !important;
    cursor: pointer;
}

div.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 30px rgba(124, 58, 237, 0.55) !important;
    animation: gradientButton 2s ease infinite;
}

div.stButton > button:active {
    transform: translateY(-1px) !important;
}

/* Small replay buttons */
div.stButton > button[data-testid="baseButton-secondary"] {
    width: auto !important;
    padding: 0.2rem 0.6rem !important;
    font-size: 0.75rem !important;
}

/* ============================================================
   TEXT AREA
   ============================================================ */
textarea {
    border-radius: 12px !important;
    border: 1.5px solid rgba(124, 58, 237, 0.3) !important;
    font-size: 0.97rem !important;
    background: rgba(15, 15, 26, 0.7) !important;
    color: #E2E8F0 !important;
    transition: border-color 0.2s ease !important;
    line-height: 1.6 !important;
}
textarea:focus {
    border-color: rgba(124, 58, 237, 0.7) !important;
    box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.12) !important;
    outline: none !important;
}

/* Text input (search bars) */
input[type="text"] {
    border-radius: 8px !important;
    border: 1px solid rgba(124, 58, 237, 0.25) !important;
    background: rgba(15, 15, 26, 0.6) !important;
    color: #E2E8F0 !important;
    transition: border-color 0.2s ease !important;
}
input[type="text"]:focus {
    border-color: rgba(124, 58, 237, 0.6) !important;
    box-shadow: 0 0 0 2px rgba(124, 58, 237, 0.1) !important;
}

/* ============================================================
   SELECTBOX
   ============================================================ */
[data-testid="stSelectbox"] > div > div {
    background: rgba(26, 26, 46, 0.8) !important;
    border: 1px solid rgba(124, 58, 237, 0.25) !important;
    border-radius: 8px !important;
}

/* ============================================================
   METRIC CARDS — hover lift
   ============================================================ */
[data-testid="stMetric"] {
    background: rgba(26, 26, 46, 0.7);
    border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 12px;
    padding: 0.8rem 1rem;
    transition: all 0.25s ease;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(124, 58, 237, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.15);
}
[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
[data-testid="stMetricValue"] {
    color: #E2E8F0 !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}

/* ============================================================
   ALERTS / NOTIFICATIONS
   ============================================================ */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    border-left-width: 3px !important;
}

.stSuccess {
    background: rgba(16, 185, 129, 0.08) !important;
    border-left-color: #10B981 !important;
}
.stError {
    background: rgba(239, 68, 68, 0.08) !important;
    border-left-color: #EF4444 !important;
}
.stWarning {
    background: rgba(245, 158, 11, 0.08) !important;
    border-left-color: #F59E0B !important;
}
.stInfo {
    background: rgba(96, 165, 250, 0.08) !important;
    border-left-color: #60A5FA !important;
}

/* ============================================================
   AUDIO PLAYER
   ============================================================ */
audio {
    width: 100%;
    border-radius: 10px;
    background: rgba(26, 26, 46, 0.8);
    outline: none;
    margin: 0.5rem 0;
}

/* ============================================================
   DOWNLOAD BUTTON
   ============================================================ */
[data-testid="stDownloadButton"] > button {
    background: rgba(16, 185, 129, 0.12) !important;
    border: 1.5px solid rgba(16, 185, 129, 0.4) !important;
    color: #10B981 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: rgba(16, 185, 129, 0.22) !important;
    border-color: rgba(16, 185, 129, 0.7) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.2) !important;
}

/* ============================================================
   EXPANDER (history panel)
   ============================================================ */
[data-testid="stExpander"] {
    background: rgba(26, 26, 46, 0.5) !important;
    border: 1px solid rgba(124, 58, 237, 0.2) !important;
    border-radius: 12px !important;
}

/* ============================================================
   RADIO BUTTONS
   ============================================================ */
[data-testid="stRadio"] > div {
    gap: 0.5rem;
}
[data-testid="stRadio"] label {
    background: rgba(26, 26, 46, 0.6);
    border: 1px solid rgba(124, 58, 237, 0.2);
    border-radius: 8px;
    padding: 0.3rem 0.7rem;
    cursor: pointer;
    transition: all 0.2s ease;
}
[data-testid="stRadio"] label:hover {
    border-color: rgba(124, 58, 237, 0.5);
    background: rgba(124, 58, 237, 0.1);
}

/* ============================================================
   SLIDER
   ============================================================ */
[data-testid="stSlider"] [role="slider"] {
    background: #7C3AED !important;
    border: 2px solid #A78BFA !important;
}

/* ============================================================
   DIVIDERS
   ============================================================ */
hr {
    border: none !important;
    border-top: 1px solid rgba(124, 58, 237, 0.15) !important;
    margin: 1.2rem 0 !important;
}

/* ============================================================
   SCROLLBAR
   ============================================================ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(15, 15, 26, 0.5); }
::-webkit-scrollbar-thumb {
    background: rgba(124, 58, 237, 0.4);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(124, 58, 237, 0.7); }

/* ============================================================
   SPINNER
   ============================================================ */
[data-testid="stSpinner"] {
    color: #A78BFA !important;
}

/* ============================================================
   CAPTION / SMALL TEXT
   ============================================================ */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #64748B !important;
    font-size: 0.78rem !important;
}

/* ============================================================
   SECTION LABEL UTILITY
   ============================================================ */
.section-label {
    color: #A78BFA;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
    margin-top: 0.2rem;
}

/* ============================================================
   SUCCESS GLOW — applied to audio player after synthesis
   ============================================================ */
@keyframes successGlow {
    0%   { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
    70%  { box-shadow: 0 0 0 12px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.audio-success {
    animation: successGlow 1.5s ease-out;
    border-radius: 12px;
}

/* ============================================================
   FOOTER
   ============================================================ */
.app-footer {
    text-align: center;
    color: #374151;
    font-size: 0.75rem;
    padding: 0.5rem 0;
    border-top: 1px solid rgba(124, 58, 237, 0.1);
    margin-top: 1rem;
}
.app-footer a {
    color: #7C3AED;
    text-decoration: none;
}
.app-footer a:hover { text-decoration: underline; }

</style>
"""


def get_full_css() -> str:
    """Return the complete CSS string for injection into Streamlit."""
    return GOOGLE_FONTS + MAIN_CSS
