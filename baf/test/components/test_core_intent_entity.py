"""Tests for Intent, IntentParameter, Entity, EntityEntry."""

import pytest

from baf.core.entity.entity import Entity
from baf.core.entity.entity_entry import EntityEntry
from baf.core.intent.intent import Intent
from baf.core.intent.intent_parameter import IntentParameter
from baf.exceptions.exceptions import DuplicatedIntentParameterError


def test_intent_defaults():
    intent = Intent("i")
    assert intent.name == "i"
    assert intent.training_sentences == []
    assert intent.parameters == []
    assert intent.description is None
    assert intent.processed_training_sentences is None


def test_intent_equality_by_name():
    i1 = Intent("hello")
    i2 = Intent("hello")
    i3 = Intent("bye")
    assert i1 == i2
    assert i1 != i3
    assert hash(i1) == hash(i2)
    assert hash(i1) != hash(i3)


def test_intent_parameter_fluent_api():
    entity = Entity("color", entries={"red": []})
    intent = Intent("pick_color", training_sentences=["I want red"])
    result = intent.parameter("col", fragment="red", entity=entity)
    assert result is intent  # fluent returns self
    assert len(intent.parameters) == 1
    param = intent.parameters[0]
    assert isinstance(param, IntentParameter)
    assert param.name == "col"
    assert param.fragment == "red"
    assert param.entity is entity


def test_intent_duplicated_parameter_raises():
    entity = Entity("color", entries={"red": []})
    intent = Intent("pick_color")
    intent.parameter("col", "red", entity)
    with pytest.raises(DuplicatedIntentParameterError):
        intent.parameter("col", "blue", entity)


def test_intent_to_json():
    entity = Entity("color", entries={"red": []})
    intent = Intent("pick", training_sentences=["I want red"], description="d")
    intent.parameter("col", "red", entity)
    data = intent.to_json()
    assert data["training_sentences"] == ["I want red"]
    assert data["description"] == "d"
    assert data["parameters"] == [{"name": "col", "fragment": "red", "entity": "color"}]


def test_entity_custom_entries_become_entity_entries():
    entity = Entity("color", entries={"red": ["crimson"], "blue": []})
    assert entity.name == "color"
    assert entity.base_entity is False
    assert len(entity.entries) == 2
    for entry in entity.entries:
        assert isinstance(entry, EntityEntry)
    red = next(e for e in entity.entries if e.value == "red")
    assert red.synonyms == ["crimson"]


def test_entity_base_entity_has_no_entries():
    entity = Entity("number", base_entity=True)
    assert entity.base_entity is True
    assert entity.entries is None


def test_entity_equality_by_name():
    e1 = Entity("x", entries={"a": []})
    e2 = Entity("x", entries={"b": []})
    assert e1 == e2
    assert hash(e1) == hash(e2)


def test_entity_to_json_custom():
    entity = Entity("color", entries={"red": ["crimson"]}, description="d")
    data = entity.to_json()
    assert data["base_entity"] is False
    assert data["description"] == "d"
    assert data["entries"] == [{"value": "red", "synonyms": ["crimson"]}]


def test_entity_to_json_base_entity():
    entity = Entity("number", base_entity=True, description="numeric")
    data = entity.to_json()
    assert data["base_entity"] is True
    assert data["entries"] == []


def test_entity_entry_defaults():
    entry = EntityEntry("red")
    assert entry.value == "red"
    assert entry.synonyms == []
    assert entry.processed_value is None
    assert entry.processed_synonyms is None
