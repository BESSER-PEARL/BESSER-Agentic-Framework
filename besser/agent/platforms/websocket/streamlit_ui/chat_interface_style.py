from __future__ import annotations

import json
import os
from datetime import datetime

import streamlit as st

from besser.agent.platforms.websocket.streamlit_ui.vars import (
    CHAT_INTERFACE_STYLES,
    CHAT_INTERFACE_STYLE_SIGNATURE,
)


_DEFAULT_STYLE = {
    "size": 16,
    "font": "sans",
    "lineSpacing": 1.5,
    "alignment": "left",
    "color": "inherit",
    "contrast": "medium",
}

_FONT_MAP = {
    "sans": "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "serif": "Georgia, 'Times New Roman', serif",
    "monospace": "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace",
    "neutral": "Inter, system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "grotesque": "'Helvetica Neue', Helvetica, Arial, sans-serif",
    "condensed": "Roboto Condensed, Arial Narrow, Arial, sans-serif",
}


def _debug_enabled() -> bool:
    raw = str(os.environ.get("STREAMLIT_CHAT_STYLE_DEBUG", "1")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _debug_log(message: str) -> None:
    if not _debug_enabled():
        return
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[chat-interface-style {timestamp}] {message}")


def _load_default_style_from_env() -> dict:
    default_style = dict(_DEFAULT_STYLE)
    raw_default_style = os.environ.get("STREAMLIT_CHAT_INTERFACE_DEFAULT_STYLE_JSON")
    if not raw_default_style:
        return default_style

    try:
        parsed = json.loads(raw_default_style)
    except Exception:
        _debug_log("failed to parse STREAMLIT_CHAT_INTERFACE_DEFAULT_STYLE_JSON; using built-in defaults")
        return default_style

    if not isinstance(parsed, dict):
        return default_style

    for key in ("size", "font", "lineSpacing", "alignment", "color", "contrast"):
        if key in parsed:
            default_style[key] = parsed[key]
    return default_style


def _extract_styles_from_mapping(data: dict) -> dict[str, dict]:
    if not isinstance(data, dict):
        return {}

    extracted_styles: dict[str, dict] = {}
    for profile_name, value in data.items():
        if not isinstance(value, dict):
            continue

        style = value.get("interfaceStyle")
        if not isinstance(style, dict):
            presentation = value.get("presentation") if isinstance(value.get("presentation"), dict) else {}
            style = presentation.get("interfaceStyle")

        if isinstance(style, dict):
            extracted_styles[str(profile_name)] = style

    return extracted_styles


def load_interface_styles() -> dict[str, dict]:
    """Load profile chat styles from env forwarded by the websocket platform."""
    raw_configurations = os.environ.get("STREAMLIT_AGENT_CONFIGURATIONS_JSON")
    if not raw_configurations:
        raw_styles = os.environ.get("STREAMLIT_CHAT_INTERFACE_STYLES_JSON")
        if not raw_styles:
            _debug_log("no agent configurations/style payload found in env")
            return {}

        try:
            style_data = json.loads(raw_styles)
        except Exception:
            _debug_log("failed to parse STREAMLIT_CHAT_INTERFACE_STYLES_JSON")
            return {}

        extracted = _extract_styles_from_mapping(style_data)
        _debug_log(f"loaded style keys from STREAMLIT_CHAT_INTERFACE_STYLES_JSON: {list(extracted.keys())}")
        return extracted

    try:
        config_data = json.loads(raw_configurations)
    except Exception:
        _debug_log("failed to parse STREAMLIT_AGENT_CONFIGURATIONS_JSON")
        return {}

    extracted = _extract_styles_from_mapping(config_data)
    _debug_log(f"loaded style keys from STREAMLIT_AGENT_CONFIGURATIONS_JSON: {list(extracted.keys())}")
    return extracted


def _safe_int(value, default: int, min_value: int, max_value: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(numeric, min_value), max_value)


def _safe_float(value, default: float, min_value: float, max_value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(numeric, min_value), max_value)


def _safe_color(value, fallback_color: str) -> str:
    if not isinstance(value, str):
        return fallback_color

    color = value.strip()
    if not color or len(color) > 64:
        return fallback_color

    if color.startswith("var("):
        return fallback_color

    if color.startswith("#"):
        return color

    if color.lower().startswith(("rgb(", "rgba(", "hsl(", "hsla(")):
        return color

    if color.replace("-", "").replace("_", "").isalnum():
        return color

    return fallback_color


def _resolve_style_for_profile() -> dict | None:
    default_style = _load_default_style_from_env()
    styles = st.session_state.get(CHAT_INTERFACE_STYLES, {})
    if not isinstance(styles, dict) or not styles:
        _debug_log("resolve: no profile styles found in session_state; using config default style")
        return default_style

    profile_name = st.session_state.get("user_profile")
    _debug_log(f"resolve: user_profile={profile_name!r}; available_style_keys={list(styles.keys())}")
    if isinstance(profile_name, str) and profile_name in styles and isinstance(styles[profile_name], dict):
        _debug_log(f"resolve: exact profile match found for {profile_name!r}")
        return styles[profile_name]

    _debug_log("resolve: no profile-specific style matched; using config default style")
    return default_style


def _normalize_style(style: dict) -> dict:
    defaults = _load_default_style_from_env()
    normalized = dict(defaults)

    size = _safe_int(style.get("size"), defaults["size"], 10, 32)
    line_spacing = _safe_float(style.get("lineSpacing"), defaults["lineSpacing"], 1.0, 3.0)

    font_key = style.get("font") if isinstance(style.get("font"), str) else defaults["font"]
    font_key = font_key if font_key in _FONT_MAP else defaults["font"]

    alignment = style.get("alignment") if isinstance(style.get("alignment"), str) else defaults["alignment"]
    alignment = alignment if alignment in {"left", "center", "justify"} else defaults["alignment"]

    contrast = style.get("contrast") if isinstance(style.get("contrast"), str) else defaults["contrast"]
    contrast = contrast if contrast in {"low", "medium", "high"} else defaults["contrast"]

    normalized["size"] = size
    normalized["lineSpacing"] = line_spacing
    normalized["font"] = font_key
    normalized["fontFamily"] = _FONT_MAP[font_key]
    normalized["alignment"] = alignment
    normalized["color"] = _safe_color(style.get("color"), defaults["color"])
    normalized["contrast"] = contrast
    normalized["fontWeight"] = 600 if contrast == "high" else 400
    normalized["opacity"] = 0.85 if contrast == "low" else 1.0

    return normalized


def apply_chat_interface_style() -> None:
    _debug_log("apply_chat_interface_style called")
    configured_style = _resolve_style_for_profile()
    if not configured_style:
        _debug_log("apply: no configured style resolved; skipping CSS injection")
        st.session_state[CHAT_INTERFACE_STYLE_SIGNATURE] = ""
        return

    normalized = _normalize_style(configured_style)
    _debug_log(f"apply: normalized style -> {normalized}")
    signature = json.dumps(normalized, sort_keys=True)
    previous_signature = st.session_state.get(CHAT_INTERFACE_STYLE_SIGNATURE)
    if previous_signature == signature:
        _debug_log("apply: style signature unchanged; re-injecting CSS for Streamlit rerun")
    st.session_state[CHAT_INTERFACE_STYLE_SIGNATURE] = signature
    _debug_log("apply: injecting chat CSS")

    st.markdown(
        f"""
<style>
div[data-testid="stChatMessage"] *,
div[data-testid="stChatInput"] textarea {{
    font-size: {normalized['size']}px !important;
    font-family: {normalized['fontFamily']} !important;
    line-height: {normalized['lineSpacing']} !important;
    text-align: {normalized['alignment']} !important;
    color: {normalized['color']} !important;
    font-weight: {normalized['fontWeight']} !important;
    opacity: {normalized['opacity']} !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )
