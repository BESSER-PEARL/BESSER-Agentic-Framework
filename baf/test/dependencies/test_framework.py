"""Smoke tests for the framework itself.

These tests confirm that the main BAF modules can be imported and the most
common public entry points can be exercised without triggering errors that
would indicate a broken dependency stack.
"""

import pytest


def test_import_core():
    from baf.core.agent import Agent
    from baf.core.state import State
    from baf.core.intent.intent import Intent
    from baf.core.entity.entity import Entity
    from baf.core.message import Message, MessageType
    from baf.core.session import Session
    from baf.core.property import Property
    from baf.core.file import File
    assert all([Agent, State, Intent, Entity, Message, MessageType, Session, Property, File])


def test_import_library_events():
    from baf.library.transition.events.base_events import (
        ReceiveMessageEvent,
        ReceiveJSONEvent,
        ReceiveFileEvent,
    )
    assert ReceiveMessageEvent
    assert ReceiveJSONEvent
    assert ReceiveFileEvent


def test_import_db_handler():
    from baf.db.db_handler import DBHandler
    from baf.db.monitoring_db import MonitoringDB
    assert DBHandler
    assert MonitoringDB


def test_import_exceptions():
    from baf.exceptions.exceptions import (
        AgentNotTrainedError,
        DuplicatedIntentError,
        DuplicatedStateError,
    )
    from baf.exceptions.logger import logger
    assert AgentNotTrainedError
    assert DuplicatedIntentError
    assert DuplicatedStateError
    assert logger


def test_import_nlp_engine():
    from baf.nlp.nlp_engine import NLPEngine
    from baf.nlp.intent_classifier.intent_classifier_configuration import (
        IntentClassifierConfiguration,
        SimpleIntentClassifierConfiguration,
    )
    from baf.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
    assert NLPEngine
    assert IntentClassifierConfiguration
    assert SimpleIntentClassifierConfiguration
    assert IntentClassifierPrediction


def test_import_llm_wrappers():
    from baf.nlp.llm.llm import LLM
    from baf.nlp.llm.llm_openai_api import LLMOpenAI
    from baf.nlp.llm.llm_replicate_api import LLMReplicate
    from baf.nlp.llm.llm_huggingface import LLMHuggingFace
    from baf.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
    assert all([LLM, LLMOpenAI, LLMReplicate, LLMHuggingFace, LLMHuggingFaceAPI])


def test_import_intent_classifiers():
    from baf.nlp.intent_classifier.intent_classifier import IntentClassifier
    from baf.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier
    from baf.nlp.intent_classifier.simple_intent_classifier_pytorch import (
        SimpleIntentClassifierTorch,
    )
    from baf.nlp.intent_classifier.simple_intent_classifier_tensorflow import (
        SimpleIntentClassifierTF,
    )
    assert all([IntentClassifier, LLMIntentClassifier, SimpleIntentClassifierTorch, SimpleIntentClassifierTF])


def test_import_ner_and_preprocessing():
    from baf.nlp.ner.ner import NER
    from baf.nlp.ner.simple_ner import SimpleNER
    from baf.nlp.preprocessing.pipelines import lang_map
    from baf.nlp.preprocessing.text_preprocessing import process_text  # noqa: F401
    assert NER
    assert SimpleNER
    assert isinstance(lang_map, dict)


def test_import_rag():
    from baf.nlp.rag.rag import RAG
    assert RAG


def test_import_speech_modules():
    from baf.nlp.speech2text.speech2text import Speech2Text
    from baf.nlp.text2speech.text2speech import Text2Speech
    assert Speech2Text
    assert Text2Speech


def test_import_platforms():
    from baf.platforms.platform import Platform
    from baf.platforms.telegram.telegram_platform import TelegramPlatform
    from baf.platforms.websocket.websocket_platform import WebSocketPlatform
    from baf.platforms.github.github_platform import GitHubPlatform
    from baf.platforms.gitlab.gitlab_platform import GitLabPlatform
    from baf.platforms.a2a.a2a_platform import A2APlatform
    assert all([Platform, TelegramPlatform, WebSocketPlatform, GitHubPlatform, GitLabPlatform, A2APlatform])


def test_agent_instantiation_and_state():
    from baf.core.agent import Agent
    agent = Agent("unit_test_agent")
    assert agent

    initial = agent.new_state("s0", initial=True)
    assert initial.initial is True

    other = agent.new_state("s1")
    assert other in agent.states
    assert len(agent.states) == 2


def test_agent_intent_and_entity_creation():
    from baf.core.agent import Agent
    agent = Agent("agent_with_intents")
    intent = agent.new_intent(
        "greet",
        training_sentences=["hello", "hi there", "good morning"],
    )
    assert intent in agent.intents
    entity = agent.new_entity("color", entries={"red": ["crimson"], "blue": []})
    assert entity in agent.entities


def test_duplicated_intent_raises():
    from baf.core.agent import Agent
    from baf.exceptions.exceptions import DuplicatedIntentError

    agent = Agent("dup_intent_agent")
    agent.new_intent("hello", training_sentences=["hi"])
    with pytest.raises(DuplicatedIntentError):
        agent.new_intent("hello", training_sentences=["hi again"])


def test_message_types_enum():
    from baf.core.message import MessageType
    assert MessageType.STR is not None
    assert MessageType.RAG_ANSWER is not None


def test_config_properties_load():
    import baf
    from baf import nlp
    from baf.core.property import Property
    from baf.core.agent import Agent

    assert isinstance(baf.CHECK_TRANSITIONS_DELAY, Property)
    assert nlp is not None
    agent = Agent("config_agent")
    assert isinstance(agent._config, dict)


def test_intent_classifier_configuration_defaults():
    from baf.nlp.intent_classifier.intent_classifier_configuration import (
        SimpleIntentClassifierConfiguration,
    )
    cfg = SimpleIntentClassifierConfiguration()
    assert cfg is not None


def test_receive_message_event_roundtrip():
    from baf.library.transition.events.base_events import ReceiveMessageEvent
    ev = ReceiveMessageEvent(message="hello")
    assert ev is not None
