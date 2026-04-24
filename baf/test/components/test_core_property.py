"""Tests for baf.core.property.Property and Agent.get_property/set_property."""

import pytest

from baf.core.agent import Agent
from baf.core.property import Property


def test_property_attributes():
    p = Property("x.y", int, 42)
    assert p.name == "x.y"
    assert p.type is int
    assert p.default_value == 42


def test_agent_get_property_returns_default_when_unset():
    a = Agent("a")
    p = Property("test.setting", str, "default-value")
    assert a.get_property(p) == "default-value"


def test_agent_set_and_get_property():
    a = Agent("a")
    p = Property("test.int", int, 0)
    a.set_property(p, 7)
    assert a.get_property(p) == 7


def test_agent_set_property_type_mismatch_raises():
    a = Agent("a")
    p = Property("test.int", int, 0)
    with pytest.raises(TypeError):
        a.set_property(p, "not-an-int")


def test_agent_property_coercion_from_yaml_string():
    a = Agent("a")
    p_bool = Property("test.bool", bool, False)
    # Simulate a value loaded from YAML where True was written as "true"
    a._config[p_bool.name] = "true"
    assert a.get_property(p_bool) is True


def test_agent_property_coercion_invalid_falls_back_to_default():
    a = Agent("a")
    p = Property("test.int", int, 99)
    a._config[p.name] = "not-a-number"
    assert a.get_property(p) == 99


def test_load_properties_from_yaml(tmp_path):
    yaml_file = tmp_path / "cfg.yaml"
    yaml_file.write_text(
        "agent:\n"
        "  check_transitions_delay: 0.25\n"
        "custom:\n"
        "  flag: true\n",
        encoding="utf-8",
    )
    a = Agent("a")
    a.load_properties(str(yaml_file))
    assert a.config["agent.check_transitions_delay"] == 0.25
    assert a.config["custom.flag"] is True


def test_load_properties_rejects_non_yaml(tmp_path):
    bad = tmp_path / "cfg.json"
    bad.write_text("{}", encoding="utf-8")
    a = Agent("a")
    with pytest.raises(ValueError):
        a.load_properties(str(bad))
