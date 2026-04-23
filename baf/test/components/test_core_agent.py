"""Tests for baf.core.agent.Agent construction and registration API."""

import pytest

from baf.core.agent import Agent
from baf.exceptions.exceptions import (
    DuplicatedEntityError,
    DuplicatedInitialStateError,
    DuplicatedIntentError,
    DuplicatedStateError,
    InitialStateNotFound,
)


def test_empty_agent_has_expected_defaults():
    a = Agent("a")
    assert a.name == "a"
    assert a.states == []
    assert a.intents == []
    assert a.entities == []
    assert a.processors == []
    assert a.nlp_engine is not None
    assert a.config == {}
    assert a.initial_state() is None


def test_new_state_registration():
    a = Agent("a")
    s0 = a.new_state("s0", initial=True)
    s1 = a.new_state("s1")
    assert s0 in a.states
    assert s1 in a.states
    assert len(a.states) == 2
    assert s0.initial is True
    assert s1.initial is False
    assert a.initial_state() is s0


def test_duplicated_state_name_raises():
    a = Agent("a")
    a.new_state("s")
    with pytest.raises(DuplicatedStateError):
        a.new_state("s")


def test_duplicated_initial_state_raises():
    a = Agent("a")
    a.new_state("s0", initial=True)
    with pytest.raises(DuplicatedInitialStateError):
        a.new_state("s1", initial=True)


def test_new_intent_registration_and_attributes():
    a = Agent("a")
    intent = a.new_intent(
        "greet",
        training_sentences=["hello", "hi"],
        description="say hi",
    )
    assert intent in a.intents
    assert intent.name == "greet"
    assert intent.training_sentences == ["hello", "hi"]
    assert intent.description == "say hi"
    assert intent.parameters == []


def test_duplicated_intent_raises():
    a = Agent("a")
    a.new_intent("hi", training_sentences=["hello"])
    with pytest.raises(DuplicatedIntentError):
        a.new_intent("hi", training_sentences=["hey"])


def test_new_entity_with_entries():
    a = Agent("a")
    color = a.new_entity(
        "color",
        entries={"red": ["crimson", "scarlet"], "blue": []},
    )
    assert color in a.entities
    assert color.name == "color"
    assert color.base_entity is False
    assert len(color.entries) == 2
    values = {entry.value for entry in color.entries}
    assert values == {"red", "blue"}


def test_duplicated_entity_raises():
    a = Agent("a")
    a.new_entity("e", entries={"v": []})
    with pytest.raises(DuplicatedEntityError):
        a.new_entity("e", entries={"v": []})


def test_train_without_initial_state_raises():
    a = Agent("a")
    a.new_state("s")  # no initial
    with pytest.raises(InitialStateNotFound):
        a.train()


def test_agent_state_untrained_by_default():
    a = Agent("a")
    assert a._trained is False
