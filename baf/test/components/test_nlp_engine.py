"""Tests for baf.nlp.nlp_engine.NLPEngine lifecycle."""

import pytest

from baf.core.agent import Agent
from baf.nlp.intent_classifier.intent_classifier_configuration import (
    SimpleIntentClassifierConfiguration,
)
from baf.nlp.nlp_engine import NLPEngine


def test_nlp_engine_fresh_state():
    agent = Agent("a")
    engine = agent.nlp_engine
    assert isinstance(engine, NLPEngine)
    assert engine._intent_classifiers == {}
    assert engine._ner is None
    assert engine._llms == {}


def test_nlp_engine_initialize_builds_ner_and_classifier():
    # Use 1 epoch to make this fast.
    cfg = SimpleIntentClassifierConfiguration(num_epochs=1)
    agent = Agent("a")
    initial = agent.new_state("initial", initial=True, ic_config=cfg)
    hello = agent.new_state("hello")
    hello_intent = agent.new_intent(
        "hello_intent", training_sentences=["hello", "hi", "hey there"]
    )
    initial.when_intent_matched(hello_intent).go_to(hello)

    agent._nlp_engine.initialize()

    # NER was built.
    assert agent._nlp_engine.ner is not None
    # An intent classifier was built for the initial state (it has intents).
    assert initial in agent._nlp_engine._intent_classifiers
    # The hello state has no intents => no classifier built.
    assert hello not in agent._nlp_engine._intent_classifiers


def test_nlp_engine_initialize_skips_states_with_no_intents():
    agent = Agent("a")
    s0 = agent.new_state("s0", initial=True)
    s1 = agent.new_state("s1")
    # Neither state has intents.
    agent._nlp_engine.initialize()
    assert agent._nlp_engine._intent_classifiers == {}


def test_agent_train_marks_trained_and_fills_classifiers():
    cfg = SimpleIntentClassifierConfiguration(num_epochs=1)
    agent = Agent("a")
    initial = agent.new_state("initial", initial=True, ic_config=cfg)
    hello_state = agent.new_state("hello_state")
    hello_intent = agent.new_intent(
        "hello",
        training_sentences=["hello", "hi", "howdy"],
    )
    initial.when_intent_matched(hello_intent).go_to(hello_state)

    agent.train()

    assert agent._trained is True
    assert initial in agent._nlp_engine._intent_classifiers
