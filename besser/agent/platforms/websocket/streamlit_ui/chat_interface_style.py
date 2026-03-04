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




def _load_default_style_from_env() -> dict:
    default_style = dict(_DEFAULT_STYLE)
    raw_default_style = os.environ.get("STREAMLIT_CHAT_INTERFACE_DEFAULT_STYLE_JSON")
    if not raw_default_style:
        return default_style

    try:
        parsed = json.loads(raw_default_style)
    except Exception:
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
            return {}

        try:
            style_data = json.loads(raw_styles)
        except Exception:
            return {}

        extracted = _extract_styles_from_mapping(style_data)
        return extracted

    try:
        config_data = json.loads(raw_configurations)
    except Exception:
        return {}

    extracted = _extract_styles_from_mapping(config_data)
    return extracted


def _save_int(value, default: int, min_value: int, max_value: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(numeric, min_value), max_value)


def _save_float(value, default: float, min_value: float, max_value: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(numeric, min_value), max_value)


def _save_color(value, fallback_color: str) -> str:
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
        return default_style

    profile_name = st.session_state.get("user_profile")
    if isinstance(profile_name, str) and profile_name in styles and isinstance(styles[profile_name], dict):
        return styles[profile_name]

    return default_style


def _normalize_style(style: dict) -> dict:
    defaults = _load_default_style_from_env()
    normalized = dict(defaults)

    size = _save_int(style.get("size"), defaults["size"], 10, 32)
    line_spacing = _save_float(style.get("lineSpacing"), defaults["lineSpacing"], 1.0, 3.0)

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
    normalized["color"] = _save_color(style.get("color"), defaults["color"])
    normalized["contrast"] = contrast
    normalized["fontWeight"] = 600 if contrast == "high" else 400
    normalized["opacity"] = 0.85 if contrast == "low" else 1.0

    return normalized


def apply_chat_interface_style() -> None:
    configured_style = _resolve_style_for_profile()
    if not configured_style:
        st.session_state[CHAT_INTERFACE_STYLE_SIGNATURE] = ""
        return

    normalized = _normalize_style(configured_style)
    signature = json.dumps(normalized, sort_keys=True)
    st.session_state[CHAT_INTERFACE_STYLE_SIGNATURE] = signature

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
        unsave_allow_html=True,
    )
