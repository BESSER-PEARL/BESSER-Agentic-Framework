"""Tests for baf.library.transition.events.base_events classes."""

from datetime import datetime

import pytest

from baf.core.file import File
from baf.library.transition.events.base_events import (
    DummyEvent,
    ReceiveFileEvent,
    ReceiveJSONEvent,
    ReceiveMessageEvent,
    ReceiveTextEvent,
    WildcardEvent,
)


def test_dummy_event_name():
    e = DummyEvent()
    assert e.name == "dummy_event"


def test_wildcard_event_matches_any_subclass_of_event():
    wildcard = WildcardEvent()
    assert wildcard.is_matching(DummyEvent()) is True
    assert wildcard.is_matching(ReceiveTextEvent(text="hi")) is True
    assert wildcard.is_matching(ReceiveFileEvent(file=File(file_data=b"x"))) is True


def test_receive_message_event_defaults():
    event = ReceiveMessageEvent(message="hi")
    assert event.message == "hi"
    assert event.human is True
    assert event.session_id is None
    assert event.name == "receive_message"


def test_receive_message_event_matches_subclass_with_same_name_prefix():
    msg_event = ReceiveMessageEvent(message="hi")
    text_event = ReceiveTextEvent(text="hi")
    # ReceiveTextEvent._name starts with 'receive_message' — base event matches it.
    assert msg_event.is_matching(text_event) is True


def test_receive_text_event_defaults_and_log():
    event = ReceiveTextEvent(text="hello", human=True)
    assert event.message == "hello"
    assert event.human is True
    assert event._name == "receive_message_text"
    assert event.predicted_intent is None
    assert "hello" in event.log()


def test_receive_json_event_with_message_key():
    payload = {"message": "greetings", "extra": 1}
    event = ReceiveJSONEvent(payload=payload, session_id="sid-1")
    assert event.contains_message is True
    assert event.message == "greetings"
    assert event.json == payload
    assert event.session_id == "sid-1"


def test_receive_json_event_without_message_key_serialises_full_payload():
    payload = {"foo": "bar", "n": 1}
    event = ReceiveJSONEvent(payload=payload)
    assert event.contains_message is False
    # message should serialise the dict; loading it back yields the original
    import json
    assert json.loads(event.message) == payload


def test_receive_file_event_attributes():
    f = File(file_name="a.txt", file_type="txt", file_data=b"x")
    event = ReceiveFileEvent(file=f, session_id="sid-1", human=True)
    assert event.file is f
    assert event.session_id == "sid-1"
    assert event.human is True
    assert event.name == "receive_file"
