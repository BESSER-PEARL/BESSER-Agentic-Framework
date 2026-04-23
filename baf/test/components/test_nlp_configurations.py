"""Tests for intent classifier configurations."""

import pytest

from baf.nlp.intent_classifier.intent_classifier_configuration import (
    IntentClassifierConfiguration,
    LLMIntentClassifierConfiguration,
    SimpleIntentClassifierConfiguration,
)


def test_simple_config_defaults():
    cfg = SimpleIntentClassifierConfiguration()
    assert cfg.framework == "pytorch"
    assert cfg.num_epochs == 300
    assert cfg.embedding_dim == 128
    assert cfg.hidden_dim == 128
    assert cfg.input_max_num_tokens == 15
    assert cfg.discard_oov_sentences is True
    assert cfg.check_exact_prediction_match is True
    assert cfg.activation_last_layer == "sigmoid"
    assert cfg.lr == 0.001


def test_simple_config_custom_values():
    cfg = SimpleIntentClassifierConfiguration(
        framework="tensorflow",
        num_epochs=50,
        embedding_dim=32,
        hidden_dim=16,
        lr=0.01,
        activation_last_layer="softmax",
    )
    assert cfg.framework == "tensorflow"
    assert cfg.num_epochs == 50
    assert cfg.embedding_dim == 32
    assert cfg.hidden_dim == 16
    assert cfg.lr == 0.01
    assert cfg.activation_last_layer == "softmax"


def test_simple_config_rejects_invalid_framework():
    with pytest.raises(ValueError):
        SimpleIntentClassifierConfiguration(framework="jax")


def test_simple_config_rejects_invalid_activation():
    with pytest.raises(ValueError):
        SimpleIntentClassifierConfiguration(activation_last_layer="relu")


def test_simple_config_is_subclass_of_base():
    cfg = SimpleIntentClassifierConfiguration()
    assert isinstance(cfg, IntentClassifierConfiguration)


def test_llm_config_defaults():
    cfg = LLMIntentClassifierConfiguration(llm_name="gpt-4o-mini")
    assert cfg.llm_name == "gpt-4o-mini"
    assert cfg.parameters == {}
    assert cfg.use_intent_descriptions is True
    assert cfg.use_training_sentences is True
    assert cfg.use_entity_descriptions is True
    assert cfg.use_entity_synonyms is True


def test_llm_config_overrides_and_parameters():
    cfg = LLMIntentClassifierConfiguration(
        llm_name="gpt-4o",
        parameters={"temperature": 0.2, "max_tokens": 512},
        use_intent_descriptions=False,
        use_training_sentences=False,
        use_entity_descriptions=False,
        use_entity_synonyms=False,
    )
    assert cfg.parameters == {"temperature": 0.2, "max_tokens": 512}
    assert cfg.use_intent_descriptions is False
    assert cfg.use_training_sentences is False
    assert cfg.use_entity_descriptions is False
    assert cfg.use_entity_synonyms is False
