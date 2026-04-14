"""
text_input.py
-------------
Reusable Streamlit component for validated text input.

Follows the same two-layer pattern as language_selector.py:
  1. Pure logic functions  — validate_text, get_counter_color, count_words,
                             is_rtl_language, get_placeholder_text
                             → independently testable, no Streamlit dependency
  2. Render function       — render_text_input()
                             → thin Streamlit wrapper that returns the text value

Usage:
    from app.components.text_input import render_text_input

    text, is_valid = render_text_input(
        language_code="hi",
        max_length=5000,
        key_prefix="main",
    )
    if is_valid:
        # proceed with synthesis
"""

from typing import Optional
import streamlit as st

# ---------------------------------------------------------------------------
# RTL Language Registry
# ---------------------------------------------------------------------------

# BCP-47 codes for right-to-left script languages
_RTL_LANGUAGE_CODES = frozenset({
    "ar",    # Arabic
    "iw",    # Hebrew (gTTS uses "iw")
    "he",    # Hebrew (ISO 639-1)
    "fa",    # Persian / Farsi
    "ur",    # Urdu
})

# Language-specific placeholder text for a more native feel
_PLACEHOLDER_MAP: dict[str, str] = {
    "en":    "Type or paste your text here...",
    "hi":    "यहाँ अपना पाठ टाइप करें या पेस्ट करें...",
    "bn":    "এখানে আপনার পাঠ্য টাইপ করুন বা পেস্ট করুন...",
    "te":    "ఇక్కడ మీ వచనాన్ని టైప్ చేయండి లేదా పేస్ట్ చేయండి...",
    "ta":    "இங்கே உங்கள் உரையை தட்டச்சு செய்யுங்கள்...",
    "mr":    "येथे आपला मजकूर टाइप करा किंवा पेस्ट करा...",
    "gu":    "અહીં તમારો ટેક્સ્ટ ટાઇપ કરો અથવા પેસ્ટ કરો...",
    "kn":    "ಇಲ್ಲಿ ನಿಮ್ಮ ಪಠ್ಯವನ್ನು ಟೈಪ್ ಮಾಡಿ ಅಥವಾ ಅಂಟಿಸಿ...",
    "ml":    "ഇവിടെ നിങ്ങളുടെ ടെക്സ്റ്റ് ടൈപ്പ് ചെയ്യുക...",
    "pa":    "ਇੱਥੇ ਆਪਣਾ ਟੈਕਸਟ ਟਾਈਪ ਕਰੋ ਜਾਂ ਪੇਸਟ ਕਰੋ...",
    "ar":    "اكتب نصك هنا أو الصقه...",
    "fa":    "متن خود را اینجا تایپ کنید...",
    "ur":    "یہاں اپنا متن ٹائپ کریں یا پیسٹ کریں...",
    "iw":    "הקלד או הדבק את הטקסט שלך כאן...",
    "zh-CN": "在此处输入或粘贴您的文本...",
    "zh-TW": "在此處輸入或貼上您的文字...",
    "ja":    "ここにテキストを入力または貼り付けてください...",
    "ko":    "여기에 텍스트를 입력하거나 붙여넣으세요...",
    "fr":    "Tapez ou collez votre texte ici...",
    "de":    "Geben Sie Ihren Text hier ein oder fügen Sie ihn ein...",
    "es":    "Escriba o pegue su texto aquí...",
    "pt":    "Digite ou cole seu texto aqui...",
    "ru":    "Введите или вставьте ваш текст здесь...",
    "tr":    "Metninizi buraya yazın veya yapıştırın...",
    "it":    "Digita o incolla il tuo testo qui...",
}

_DEFAULT_PLACEHOLDER = "Type or paste your text here..."


# ---------------------------------------------------------------------------
# Pure Logic Functions (testable without Streamlit)
# ---------------------------------------------------------------------------

def validate_text(text: str, max_length: int = 5000) -> tuple[bool, str]:
    """
    Validate the input text for TTS synthesis.

    Args:
        text:       Raw text from the input field.
        max_length: Maximum allowed character count.

    Returns:
        Tuple of (is_valid: bool, message: str).
        message is empty string when valid.
    """
    if not text or not text.strip():
        return False, "Text cannot be empty."
    if len(text) > max_length:
        return False, f"Text exceeds the {max_length:,} character limit."
    if len(text.strip()) < 2:
        return False, "Text is too short. Please enter at least 2 characters."
    return True, ""


def get_counter_color(char_count: int, max_length: int) -> str:
    """
    Return a hex color reflecting how close the count is to the limit.

    Thresholds:
        < 70%  → muted grey  (#94A3B8) — plenty of room
        70–90% → amber       (#F59E0B) — approaching limit
        > 90%  → red         (#EF4444) — near/over limit

    Args:
        char_count: Current number of characters.
        max_length: Maximum allowed characters.

    Returns:
        Hex color string.
    """
    if max_length <= 0:
        return "#94A3B8"
    ratio = char_count / max_length
    if ratio > 0.9:
        return "#EF4444"
    if ratio > 0.7:
        return "#F59E0B"
    return "#94A3B8"


def count_words(text: str) -> int:
    """
    Count the number of words in the input text.

    Splits on any whitespace; handles empty and whitespace-only strings.

    Args:
        text: Input string.

    Returns:
        Word count. 0 for empty or whitespace-only strings.
    """
    return len(text.split()) if text.strip() else 0


def is_rtl_language(language_code: str) -> bool:
    """
    Return True if the language is written right-to-left.

    Covers Arabic, Hebrew, Persian/Farsi, and Urdu.

    Args:
        language_code: BCP-47 code e.g. "ar", "iw", "fa".

    Returns:
        Boolean.
    """
    return language_code.lower() in _RTL_LANGUAGE_CODES


def get_placeholder_text(language_code: str) -> str:
    """
    Return a language-native placeholder string for the text area.

    Falls back to English if no specific translation is available.

    Args:
        language_code: BCP-47 code.

    Returns:
        Placeholder string in the target language.
    """
    return _PLACEHOLDER_MAP.get(language_code, _DEFAULT_PLACEHOLDER)


def get_char_stats(text: str, max_length: int) -> dict:
    """
    Compute all character/word statistics in one call.

    Useful for rendering multiple stat widgets without repeated computation.

    Args:
        text:       Input string.
        max_length: Maximum allowed characters.

    Returns:
        Dict with keys: char_count, word_count, remaining, color, pct_used.
    """
    char_count = len(text)
    word_count = count_words(text)
    remaining = max_length - char_count
    color = get_counter_color(char_count, max_length)
    pct_used = round((char_count / max_length) * 100, 1) if max_length > 0 else 0.0

    return {
        "char_count": char_count,
        "word_count": word_count,
        "remaining": remaining,
        "color": color,
        "pct_used": pct_used,
    }


# ---------------------------------------------------------------------------
# Streamlit Render Function
# ---------------------------------------------------------------------------

def render_text_input(
    language_code: str = "en",
    max_length: int = 5000,
    key_prefix: str = "",
    height: int = 180,
) -> tuple[str, bool]:
    """
    Render a validated text area with live stats and RTL support.

    Displays:
      - Language-aware placeholder text
      - RTL direction hint for RTL languages
      - Live character + word counter (color-coded)
      - Inline validation error if text is invalid

    Args:
        language_code: BCP-47 code — determines placeholder and RTL hint.
        max_length:    Maximum character limit (from settings).
        key_prefix:    Unique prefix for widget keys.
        height:        Height of the text area in pixels.

    Returns:
        Tuple of (text: str, is_valid: bool).
        Callers should only proceed with synthesis when is_valid is True.
    """
    # RTL direction hint
    rtl = is_rtl_language(language_code)
    if rtl:
        st.markdown(
            '<p style="color:#F59E0B; font-size:0.78rem; margin-bottom:4px;">'
            "↩️ Right-to-left language detected — text will render in RTL direction.</p>",
            unsafe_allow_html=True,
        )

    # Section label
    st.markdown(
        '<p style="color:#A78BFA; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "📝 Enter Text</p>",
        unsafe_allow_html=True,
    )

    # Text area
    text = st.text_area(
        label="Text to synthesize",
        placeholder=get_placeholder_text(language_code),
        height=height,
        max_chars=max_length,
        label_visibility="collapsed",
        key=f"{key_prefix}_text_area",
    )

    # Compute stats
    stats = get_char_stats(text, max_length)

    # Counter row: chars · words · remaining
    st.markdown(
        f'<div style="display:flex; justify-content:space-between; '
        f'font-size:0.78rem; margin-top:-10px; color:{stats["color"]};">'
        f'<span>{stats["word_count"]} words</span>'
        f'<span>{stats["char_count"]:,} / {max_length:,} chars '
        f'({stats["pct_used"]}%)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Validation
    is_valid, error_msg = validate_text(text, max_length)

    if text and not is_valid:
        st.error(f"⚠️ {error_msg}")

    return text, is_valid
