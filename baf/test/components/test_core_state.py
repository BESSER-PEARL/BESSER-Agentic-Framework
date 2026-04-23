"""Tests for baf.core.state.State and related transition builders."""

import pytest

from baf.core.agent import Agent
from baf.exceptions.exceptions import (
    BodySignatureError,
    DuplicatedIntentMatchingTransitionError,
    IntentNotFound,
)


def test_state_equality_uses_name_and_agent():
    a = Agent("a")
    s0a = a.new_state("s")
    a2 = Agent("a")
    s0b = a2.new_state("s")
    assert s0a == s0b  # same state+agent name
    assert hash(s0a) == hash(s0b)


def test_state_distinct_when_names_differ():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    assert s0 != s1
    assert hash(s0) != hash(s1)


def test_auto_transition_go_to():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    s0.go_to(s1)
    assert len(s0.transitions) == 1
    trans = s0.transitions[0]
    assert trans.source is s0
    assert trans.dest is s1
    assert trans.is_auto() is True


def test_when_intent_matched_creates_transition():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    intent = a.new_intent("greet", training_sentences=["hi"])
    s0.when_intent_matched(intent).go_to(s1)
    assert intent in s0.intents
    assert len(s0.transitions) == 1
    trans = s0.transitions[0]
    assert trans.source is s0
    assert trans.dest is s1
    assert trans.event is not None
    assert trans.condition is not None


def test_when_intent_matched_rejects_duplicate_intent():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    intent = a.new_intent("greet", training_sentences=["hi"])
    s0.when_intent_matched(intent).go_to(s1)
    with pytest.raises(DuplicatedIntentMatchingTransitionError):
        s0.when_intent_matched(intent).go_to(s1)


def test_when_intent_matched_rejects_unknown_intent():
    a1 = Agent("a1")
    a2 = Agent("a2")
    s0 = a1.new_state("s0", initial=True)
    foreign = a2.new_intent("foreign", training_sentences=["hey"])
    with pytest.raises(IntentNotFound):
        s0.when_intent_matched(foreign)


def test_when_condition_transition():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")

    def always_true(session):
        return True

    s0.when_condition(always_true).go_to(s1)
    assert len(s0.transitions) == 1
    trans = s0.transitions[0]
    assert trans.event is None
    assert trans.condition is not None


def test_set_body_accepts_valid_signature():
    from baf.core.session import Session

    a = Agent("a")
    s0 = a.new_state("s0", initial=True)

    def body(session: Session):
        session.reply("ok")

    s0.set_body(body)
    assert s0._body is body


def test_set_body_rejects_wrong_signature():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)

    def wrong_body():
        pass

    with pytest.raises(BodySignatureError):
        s0.set_body(wrong_body)


def test_set_fallback_body_rejects_wrong_signature():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)

    def wrong_fallback(session, extra):
        pass

    with pytest.raises(BodySignatureError):
        s0.set_fallback_body(wrong_fallback)
