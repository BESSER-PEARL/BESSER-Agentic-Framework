"""Tests for baf.core.session.Session read/write and helpers."""

import pytest

from baf.core.agent import Agent
from baf.core.session import Session


def _make_session(fake_platform) -> Session:
    agent = Agent("session_agent")
    agent.new_state("initial", initial=True)
    agent._platforms.append(fake_platform)
    return Session("sid-1", agent, fake_platform, username="alice")


def test_session_initial_attributes(fake_platform):
    s = _make_session(fake_platform)
    assert s.id == "sid-1"
    assert s.platform is fake_platform
    assert s.current_state.name == "initial"
    assert s.event is None
    assert list(s.events) == []


def test_session_dictionary_roundtrip(fake_platform):
    s = _make_session(fake_platform)
    s.set("username", "bob")
    s.set("age", 42)
    assert s.get("username") == "bob"
    assert s.get("age") == 42
    assert s.get_dictionary() == {"username": "bob", "age": 42}


def test_session_get_missing_returns_default(fake_platform):
    s = _make_session(fake_platform)
    assert s.get("missing") is None
    assert s.get("missing", default="fallback") == "fallback"


def test_session_delete_key(fake_platform):
    s = _make_session(fake_platform)
    s.set("k", "v")
    s.delete("k")
    assert s.get("k") is None
    assert s.get_dictionary() == {}


def test_session_delete_missing_is_safe(fake_platform):
    s = _make_session(fake_platform)
    # Should not raise even though the key doesn't exist.
    s.delete("does_not_exist")
    assert s.get_dictionary() == {}


def test_session_event_setter(fake_platform):
    from baf.library.transition.events.base_events import ReceiveTextEvent

    s = _make_session(fake_platform)
    event = ReceiveTextEvent(text="hi", session_id=s.id, human=True)
    s.event = event
    assert s.event is event


def test_session_reply_goes_through_platform(fake_platform):
    s = _make_session(fake_platform)
    s.reply("hello user")
    assert fake_platform.replies == [("sid-1", "hello user")]
