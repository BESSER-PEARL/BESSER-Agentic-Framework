from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

import streamlit as st


PROFILE_FILE = Path(__file__).parent / "user_profiles.json"


def profiles_available() -> bool:
    """Return True if profiles are available via env or local file."""
    if os.environ.get("STREAMLIT_USER_PROFILES_JSON"):
        return True
    return PROFILE_FILE.exists()


def load_profiles(path: Path) -> list[dict]:
    """Load profiles from env (if provided) or disk. Accepts list or mapping of name->profile."""
    raw_env = os.environ.get("STREAMLIT_USER_PROFILES_JSON")
    if raw_env:
        try:
            data = json.loads(raw_env)
        except Exception as exc:
            raise ValueError("Failed to parse STREAMLIT_USER_PROFILES_JSON") from exc
    else:
        if not path.exists():
            raise FileNotFoundError(f"Profile file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(data, dict):
        return [{"name": name, "user_profile": profile} for name, profile in data.items()]
    if not isinstance(data, list):
        raise ValueError("Expected a list or mapping of profiles in the JSON file.")
    return data


def bullet_lines(data: object, indent: int = 0) -> Iterable[str]:
    """Convert nested data into simple markdown bullet lines."""
    prefix = "  " * indent + "- "
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                yield f"{prefix}{key}:"
                yield from bullet_lines(value, indent + 1)
            else:
                yield f"{prefix}{key}: {value}"
    elif isinstance(data, list):
        for index, item in enumerate(data, start=1):
            if isinstance(item, (dict, list)):
                yield f"{prefix}{index}:"
                yield from bullet_lines(item, indent + 1)
            else:
                yield f"{prefix}{item}"
    else:
        yield f"{prefix}{data}"


def profile_selector() -> bool:
    """Render the profile card carousel. Returns True when the user confirms or leaves."""
    st.title("Choose a user profile")
    st.write("Flip through the cards, then confirm the one that fits you best.")

    try:
        profiles = load_profiles(PROFILE_FILE)
    except Exception as exc:
        st.error(str(exc))
        return False

    st.session_state.setdefault("profile_current_idx", 0)
    st.session_state.setdefault("user_profile", None)

    current_idx = st.session_state.profile_current_idx
    current_profile = profiles[current_idx]
    profile_name = current_profile.get("name") or f"Profile {current_idx + 1}"

    col_prev, col_pos, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("< Previous", use_container_width=True, disabled=current_idx == 0):
            st.session_state.profile_current_idx = max(0, current_idx - 1)
            st.rerun()
    with col_pos:
        st.markdown(f"**Card {current_idx + 1} of {len(profiles)}**")
        st.caption(profile_name)
    with col_next:
        if st.button("Next >", use_container_width=True, disabled=current_idx == len(profiles) - 1):
            st.session_state.profile_current_idx = min(len(profiles) - 1, current_idx + 1)
            st.rerun()

    st.markdown("---")

    card = st.container()
    with card:
        st.markdown(
            """
            <div style="border: 1px solid #e6e6e6; border-radius: 12px; padding: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.06); background: #fafafa;">
            """,
            unsafe_allow_html=True,
        )
        st.subheader(f"Meet {profile_name}")

        details = current_profile.get("user_profile") or current_profile.get("User") or current_profile
        if isinstance(details, dict):
            if "model" in details:
                model = details["model"]
            elif "User" in details:
                model = details["User"]
            else:
                model = details
        else:
            model = details

        lines = "\n".join(bullet_lines(model)) if model else "No details provided."
        st.markdown(lines)

        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_confirm, col_back = st.columns([3, 1])
    with col_confirm:
        if st.button("Confirm as fitting to me", type="primary", use_container_width=True):
            st.session_state.user_profile = profile_name
            st.session_state.pop("sent_user_profile", None)
            return True
    with col_back:
        if st.button("Back", use_container_width=True):
            return True

    if st.session_state.get("user_profile"):
        st.success(f"Current profile: {st.session_state.user_profile}")

    return False
