"""End-to-end workflow tests: build → train → predict.

These tests exercise the full lifecycle of a trivial agent: define states,
intents and transitions, train the NLP engine, and run a prediction through
the classifier. They verify that the whole pipeline hangs together.
"""

import pytest

from baf.core.agent import Agent
from baf.core.session import Session
from baf.nlp.intent_classifier.intent_classifier_configuration import (
    SimpleIntentClassifierConfiguration,
)


def _tiny_greetings_agent() -> Agent:
    cfg = SimpleIntentClassifierConfiguration(num_epochs=20)
    agent = Agent("greetings")
    initial = agent.new_state("initial_state", initial=True, ic_config=cfg)
    hello = agent.new_state("hello_state", ic_config=cfg)
    bye = agent.new_state("bye_state", ic_config=cfg)

    hello_intent = agent.new_intent(
        "hello_intent",
        training_sentences=[
            "hello",
            "hi",
            "hey there",
            "good morning",
            "howdy",
        ],
    )
    bye_intent = agent.new_intent(
        "bye_intent",
        training_sentences=[
            "bye",
            "goodbye",
            "see you",
            "farewell",
            "later",
        ],
    )
    initial.when_intent_matched(hello_intent).go_to(hello)
    initial.when_intent_matched(bye_intent).go_to(bye)

    def hello_body(session: Session):
        session.reply("Hi!")

    def bye_body(session: Session):
        session.reply("Goodbye!")

    hello.set_body(hello_body)
    bye.set_body(bye_body)
    hello.go_to(initial)
    bye.go_to(initial)
    return agent


def test_greetings_agent_builds_expected_graph():
    agent = _tiny_greetings_agent()
    assert [s.name for s in agent.states] == [
        "initial_state",
        "hello_state",
        "bye_state",
    ]
    assert [i.name for i in agent.intents] == ["hello_intent", "bye_intent"]
    initial = agent.initial_state()
    assert len(initial.transitions) == 2


def test_greetings_agent_training_completes():
    agent = _tiny_greetings_agent()
    agent.train()
    assert agent._trained is True
    # The initial state should have an intent classifier after training.
    assert agent.initial_state() in agent._nlp_engine._intent_classifiers


def test_greetings_agent_predicts_correct_intent():
    agent = _tiny_greetings_agent()
    agent.train()

    initial = agent.initial_state()
    classifier = agent._nlp_engine._intent_classifiers[initial]

    # 'hi' is one of the training sentences for hello_intent.
    predictions = classifier.predict("hi")
    assert len(predictions) >= 1
    top = max(predictions, key=lambda p: p.score)
    assert top.intent.name == "hello_intent"

    # 'bye' for bye_intent.
    predictions_bye = classifier.predict("bye")
    top_bye = max(predictions_bye, key=lambda p: p.score)
    assert top_bye.intent.name == "bye_intent"


def test_session_reply_drives_platform_after_body_execution(fake_platform):
    """Execute a State body manually; the reply should land on the platform."""
    agent = Agent("body_agent")
    initial = agent.new_state("initial", initial=True)
    agent._platforms.append(fake_platform)

    def body(session: Session):
        session.reply("running body")

    initial.set_body(body)

    session = Session("s1", agent, fake_platform)
    # Directly invoke the body as the state's manager would.
    initial._body(session)

    assert fake_platform.replies == [("s1", "running body")]


def test_intent_to_json_includes_parameter_with_entity():
    agent = Agent("params_agent")
    color = agent.new_entity(
        "color",
        entries={"red": ["crimson"], "blue": ["navy"]},
    )
    pick = agent.new_intent(
        "pick_color",
        training_sentences=["I want red", "pick the blue one"],
    )
    pick.parameter("col", fragment="red", entity=color)

    data = pick.to_json()
    assert data["parameters"] == [
        {"name": "col", "fragment": "red", "entity": "color"}
    ]
