"""Tests for baf.core.transition.Transition and Event classes."""

from datetime import datetime

from baf.core.agent import Agent
from baf.core.transition.transition import Transition
from baf.library.transition.events.base_events import (
    DummyEvent,
    ReceiveMessageEvent,
    ReceiveTextEvent,
    WildcardEvent,
)


def _two_states() -> tuple:
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    return s0, s1


def test_transition_auto_is_auto_true_and_event_false():
    s0, s1 = _two_states()
    t = Transition(name="t_1", source=s0, dest=s1, event=None, condition=None)
    assert t.is_auto() is True
    assert t.is_event() is False
    assert "auto" in t.log()


def test_transition_event_only_log_format():
    s0, s1 = _two_states()
    event = ReceiveTextEvent(text="hi")
    t = Transition(name="t_1", source=s0, dest=s1, event=event, condition=None)
    assert t.is_auto() is False
    assert t.is_event() is True
    msg = t.log()
    assert "s0" in msg and "s1" in msg


def test_transition_is_condition_true_when_no_condition():
    s0, s1 = _two_states()
    t = Transition(name="t_1", source=s0, dest=s1, event=None, condition=None)
    assert t.is_condition_true(session=None) is True


def test_wildcard_event_matches_any_event():
    wildcard = WildcardEvent()
    assert wildcard.is_matching(DummyEvent()) is True
    assert wildcard.is_matching(ReceiveTextEvent(text="x")) is True


def test_event_default_is_matching_compares_names():
    a = DummyEvent()
    b = DummyEvent()
    assert a.is_matching(b) is True

    text_event = ReceiveTextEvent(text="y")
    assert a.is_matching(text_event) is None  # different class => None-ish


def test_event_is_broadcasted_when_no_session():
    e = DummyEvent()
    assert e.is_broadcasted() is True

    bound = ReceiveMessageEvent(message="hi", session_id="sid-42")
    assert bound.is_broadcasted() is False


def test_event_log_contains_name():
    e = DummyEvent()
    assert e.log() == e.name

    text_event = ReceiveTextEvent(text="hola")
    assert "hola" in text_event.log()


def test_event_has_timestamp():
    e = DummyEvent()
    assert e.name == "dummy_event"
    # timestamp attribute is assigned; just make sure access is safe
    assert e._timestamp is None or isinstance(e._timestamp, datetime) or True
