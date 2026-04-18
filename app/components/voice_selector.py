"""
voice_selector.py
-----------------
Reusable Streamlit component for voice gender and speed selection.

Two-layer pattern (same as all other components):
  1. Pure logic functions  — get_speed_label, build_voice_config,
                             validate_voice_config
                             → independently testable, no Streamlit dependency
  2. Render function       — render_voice_selector()
                             → returns a VoiceConfig dict

Usage:
    from app.components.voice_selector import render_voice_selector

    voice_config = render_voice_selector(key_prefix="sidebar")
    # Returns: {"gender": "female", "speed": 1.0}
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Voice Metadata
# ---------------------------------------------------------------------------

# Gender options with display metadata
_GENDERS: list[dict] = [
    {"id": "female",  "label": "Female"},
    {"id": "male",    "label": "Male"},
]

# Speed presets with labels
_SPEED_PRESETS: list[dict] = [
    {"value": 0.5,  "label": "Slow",    "description": "Half speed — great for learners"},
    {"value": 0.75, "label": "Relaxed", "description": "75% speed"},
    {"value": 1.0,  "label": "Normal",  "description": "Default speed"},
    {"value": 1.25, "label": "Brisk",   "description": "125% speed"},
    {"value": 1.5,  "label": "Fast",    "description": "150% speed — time-efficient"},
    {"value": 2.0,  "label": "Maximum", "description": "Double speed"},
]


# ---------------------------------------------------------------------------
# Pure Logic Functions
# ---------------------------------------------------------------------------

def get_speed_label(speed: float) -> str:
    """
    Return a descriptive emoji label for a given speed value.

    Args:
        speed: Float speed multiplier (0.5–2.0).

    Returns:
        Label string e.g. "🐢 Slow", "▶️ Normal", "🐇 Fast".
    """
    for preset in _SPEED_PRESETS:
        if abs(preset["value"] - speed) < 0.01:
            return preset["label"]

    # Interpolated label for values between presets
    if speed < 1.0:
        return "Slow"
    if speed > 1.0:
        return "Fast"
    return "Normal"


def build_voice_config(gender: str, speed: float) -> dict:
    """
    Assemble a validated voice configuration dict.

    Args:
        gender: "male" | "female"
        speed:  Float 0.5–2.0

    Returns:
        VoiceConfig dict with all selections plus derived display fields.

    Raises:
        ValueError: If any value is outside allowed ranges.
    """
    valid_genders = {g["id"] for g in _GENDERS}

    if gender not in valid_genders:
        raise ValueError(f"Invalid gender '{gender}'. Must be one of: {sorted(valid_genders)}")
    if not (0.5 <= speed <= 2.0):
        raise ValueError(f"Invalid speed '{speed}'. Must be between 0.5 and 2.0.")

    return {
        "gender":      gender,
        # We implicitly provide "calm" mood to avoid breaking downstream services that expect it
        "mood":        "calm",
        "speed":       speed,
        "speed_label": get_speed_label(speed),
        "is_slow":     speed < 1.0,
    }


def validate_voice_config(config: dict) -> tuple[bool, str]:
    """
    Validate a voice config dict produced by build_voice_config.

    Args:
        config: Dict with gender, speed keys.

    Returns:
        Tuple (is_valid: bool, error_message: str).
    """
    try:
        build_voice_config(
            gender=config.get("gender", ""),
            speed=config.get("speed", 1.0),
        )
        return True, ""
    except ValueError as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Streamlit Render Function
# ---------------------------------------------------------------------------

def render_voice_selector(
    engine: str = "gtts",
    key_prefix: str = "",
    default_gender: str = "female",
    default_speed: float = 1.0,
) -> dict:
    """
    Render the full voice configuration panel inside the current Streamlit context.

    Displays:
      - Gender radio buttons
      - Speed slider with live label

    Args:
        engine:         TTS engine string.
        key_prefix:     Unique prefix for widget keys.
        default_gender: Pre-selected gender.
        default_speed:  Pre-selected speed value.

    Returns:
        VoiceConfig dict with keys: gender, mood, speed, speed_label, is_slow.
    """

    # --- Gender ---
    st.markdown(
        '<p style="color:#8B7355; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "Voice Gender</p>",
        unsafe_allow_html=True,
    )

    gender_labels = [f"{g['label']}" for g in _GENDERS]
    default_gender_idx = next(
        (i for i, g in enumerate(_GENDERS) if g["id"] == default_gender), 0
    )

    selected_gender_label = st.radio(
        "Voice Gender",
        options=gender_labels,
        index=default_gender_idx,
        horizontal=True,
        key=f"{key_prefix}_gender_radio",
        label_visibility="collapsed",
    )
    selected_gender_id = _GENDERS[gender_labels.index(selected_gender_label)]["id"]

    st.divider()

    # --- Speed ---
    st.markdown(
        '<p style="color:#8B7355; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "Speed</p>",
        unsafe_allow_html=True,
    )

    speed = st.slider(
        "Speed",
        min_value=0.5,
        max_value=2.0,
        value=default_speed,
        step=0.25,
        key=f"{key_prefix}_speed_slider",
        label_visibility="collapsed",
    )
    st.caption(f"{get_speed_label(speed)} ({speed}x)")

    return build_voice_config(
        gender=selected_gender_id,
        speed=speed,
    )
