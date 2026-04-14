"""
voice_selector.py
-----------------
Reusable Streamlit component for voice gender, mood, and speed selection.

Two-layer pattern (same as all other components):
  1. Pure logic functions  — get_all_moods, filter_moods, get_speed_label,
                             get_mood_emoji, build_voice_config,
                             validate_voice_config
                             → independently testable, no Streamlit dependency
  2. Render function       — render_voice_selector()
                             → returns a VoiceConfig dict

Usage:
    from app.components.voice_selector import render_voice_selector

    voice_config = render_voice_selector(key_prefix="sidebar")
    # Returns: {"gender": "female", "mood": "calm", "speed": 1.0}
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Voice / Mood Metadata
# ---------------------------------------------------------------------------

# Full mood registry — name, emoji, description, and valid engines
_MOODS: list[dict] = [
    {
        "id":          "neutral",
        "label":       "Neutral",
        "emoji":       "😐",
        "description": "Balanced, everyday tone — works for any content",
        "engines":     ["gtts", "elevenlabs"],
    },
    {
        "id":          "calm",
        "label":       "Calm",
        "emoji":       "😌",
        "description": "Slow, soothing delivery — ideal for meditation or narration",
        "engines":     ["gtts", "elevenlabs"],
    },
    {
        "id":          "formal",
        "label":       "Formal",
        "emoji":       "🎩",
        "description": "Professional, measured tone — suitable for business or news",
        "engines":     ["gtts", "elevenlabs"],
    },
    {
        "id":          "energetic",
        "label":       "Energetic",
        "emoji":       "⚡",
        "description": "Lively, upbeat delivery — great for promotions or announcements",
        "engines":     ["gtts", "elevenlabs"],
    },
]

# Gender options with display metadata
_GENDERS: list[dict] = [
    {"id": "female",  "label": "Female",  "emoji": "👩"},
    {"id": "male",    "label": "Male",    "emoji": "👨"},
    {"id": "neutral", "label": "Neutral", "emoji": "🧑"},
]

# Speed presets with labels
_SPEED_PRESETS: list[dict] = [
    {"value": 0.5,  "label": "🐢 Slow",    "description": "Half speed — great for learners"},
    {"value": 0.75, "label": "🚶 Relaxed", "description": "75% speed"},
    {"value": 1.0,  "label": "▶️ Normal",  "description": "Default speed"},
    {"value": 1.25, "label": "🏃 Brisk",   "description": "125% speed"},
    {"value": 1.5,  "label": "🐇 Fast",    "description": "150% speed — time-efficient"},
    {"value": 2.0,  "label": "⚡ Maximum", "description": "Double speed"},
]


# ---------------------------------------------------------------------------
# Pure Logic Functions
# ---------------------------------------------------------------------------

def get_all_moods(engine: str = "gtts") -> list[dict]:
    """
    Return all mood options, optionally filtered by engine support.

    Args:
        engine: "gtts" | "elevenlabs" | "all"

    Returns:
        List of mood dicts with id, label, emoji, description.
    """
    if engine == "all":
        return _MOODS
    return [m for m in _MOODS if engine in m["engines"]]


def filter_moods(moods: list[dict], query: str) -> list[dict]:
    """
    Filter moods by a search query against label and description.

    Falls back to full list if no matches found.

    Args:
        moods: List of mood dicts.
        query: User search string (case-insensitive).

    Returns:
        Filtered list, never empty.
    """
    query = query.strip().lower()
    if not query:
        return moods

    matched = [
        m for m in moods
        if query in m["label"].lower()
        or query in m["description"].lower()
        or query in m["id"].lower()
    ]
    return matched if matched else moods


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
        return "🐢 Slow"
    if speed > 1.0:
        return "🐇 Fast"
    return "▶️ Normal"


def get_mood_emoji(mood_id: str) -> str:
    """
    Return the emoji for a given mood ID.

    Args:
        mood_id: Mood identifier e.g. "calm", "energetic".

    Returns:
        Emoji string. Defaults to "😐" for unknown moods.
    """
    for mood in _MOODS:
        if mood["id"] == mood_id:
            return mood["emoji"]
    return "😐"


def build_voice_config(gender: str, mood: str, speed: float) -> dict:
    """
    Assemble a validated voice configuration dict.

    Args:
        gender: "male" | "female" | "neutral"
        mood:   "neutral" | "calm" | "formal" | "energetic"
        speed:  Float 0.5–2.0

    Returns:
        VoiceConfig dict with all selections plus derived display fields.

    Raises:
        ValueError: If any value is outside allowed ranges.
    """
    valid_genders = {g["id"] for g in _GENDERS}
    valid_moods = {m["id"] for m in _MOODS}

    if gender not in valid_genders:
        raise ValueError(f"Invalid gender '{gender}'. Must be one of: {sorted(valid_genders)}")
    if mood not in valid_moods:
        raise ValueError(f"Invalid mood '{mood}'. Must be one of: {sorted(valid_moods)}")
    if not (0.5 <= speed <= 2.0):
        raise ValueError(f"Invalid speed '{speed}'. Must be between 0.5 and 2.0.")

    return {
        "gender":      gender,
        "mood":        mood,
        "speed":       speed,
        "speed_label": get_speed_label(speed),
        "mood_emoji":  get_mood_emoji(mood),
        "is_slow":     speed < 1.0,
    }


def validate_voice_config(config: dict) -> tuple[bool, str]:
    """
    Validate a voice config dict produced by build_voice_config.

    Args:
        config: Dict with gender, mood, speed keys.

    Returns:
        Tuple (is_valid: bool, error_message: str).
    """
    try:
        build_voice_config(
            gender=config.get("gender", ""),
            mood=config.get("mood", ""),
            speed=config.get("speed", 1.0),
        )
        return True, ""
    except ValueError as exc:
        return False, str(exc)


def get_mood_display_options(moods: list[dict]) -> list[str]:
    """
    Build formatted display strings for the mood selectbox.

    Format: "{emoji} {label} — {description}"

    Args:
        moods: List of mood dicts.

    Returns:
        List of display strings.
    """
    return [f"{m['emoji']} {m['label']} — {m['description']}" for m in moods]


def resolve_mood_from_display(display: str, moods: list[dict]) -> str:
    """
    Reverse-lookup: given a display string, return the mood ID.

    Args:
        display: Formatted display string from get_mood_display_options().
        moods:   The mood list the display was built from.

    Returns:
        Mood ID string e.g. "calm". Returns "neutral" if not found.
    """
    for mood in moods:
        if display.startswith(f"{mood['emoji']} {mood['label']}"):
            return mood["id"]
    return "neutral"


# ---------------------------------------------------------------------------
# Streamlit Render Function
# ---------------------------------------------------------------------------

def render_voice_selector(
    engine: str = "gtts",
    key_prefix: str = "",
    default_gender: str = "female",
    default_mood: str = "neutral",
    default_speed: float = 1.0,
) -> dict:
    """
    Render the full voice configuration panel inside the current Streamlit context.

    Displays:
      - Mood search bar with dynamic filtering
      - Searchable mood selector (emoji + description)
      - Gender radio buttons
      - Speed slider with live label

    Args:
        engine:         TTS engine — determines available moods.
        key_prefix:     Unique prefix for widget keys.
        default_gender: Pre-selected gender.
        default_mood:   Pre-selected mood ID.
        default_speed:  Pre-selected speed value.

    Returns:
        VoiceConfig dict with keys: gender, mood, speed, speed_label,
        mood_emoji, is_slow.
    """
    all_moods = get_all_moods(engine=engine)

    # --- Mood ---
    st.markdown(
        '<p style="color:#A78BFA; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "🎭 Tone / Mood</p>",
        unsafe_allow_html=True,
    )

    # Mood search bar
    mood_search = st.text_input(
        "Search mood",
        placeholder="e.g. calm, formal, energetic...",
        key=f"{key_prefix}_mood_search",
        label_visibility="collapsed",
    )

    filtered_moods = filter_moods(all_moods, mood_search)
    mood_options = get_mood_display_options(filtered_moods)

    # Find default index
    default_mood_idx = next(
        (i for i, m in enumerate(filtered_moods) if m["id"] == default_mood), 0
    )

    selected_mood_display = st.selectbox(
        "Mood",
        options=mood_options,
        index=default_mood_idx,
        key=f"{key_prefix}_mood_select",
        label_visibility="collapsed",
    )
    selected_mood_id = resolve_mood_from_display(selected_mood_display, filtered_moods)

    st.divider()

    # --- Gender ---
    st.markdown(
        '<p style="color:#A78BFA; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "🎙️ Voice Gender</p>",
        unsafe_allow_html=True,
    )

    gender_labels = [f"{g['emoji']} {g['label']}" for g in _GENDERS]
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
        '<p style="color:#A78BFA; font-size:0.78rem; font-weight:600; '
        'letter-spacing:0.08em; text-transform:uppercase; margin-bottom:4px;">'
        "⚡ Speed</p>",
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
        mood=selected_mood_id,
        speed=speed,
    )
