"""Tests for baf.core.processors.Processor abstract base class."""

import pytest

from baf.core.agent import Agent
from baf.core.processors.processor import Processor
from baf.exceptions.exceptions import ProcessorTargetUndefined


class UpperProcessor(Processor):
    def process(self, session, message):
        return message.upper() if isinstance(message, str) else message


def test_processor_must_target_at_least_one_direction():
    a = Agent("a")
    with pytest.raises(ProcessorTargetUndefined):
        UpperProcessor(agent=a)


def test_processor_auto_registers_on_agent():
    a = Agent("a")
    p = UpperProcessor(agent=a, user_messages=True)
    assert p in a.processors
    assert p.user_messages is True
    assert p.agent_messages is False


def test_processor_registers_for_both_directions():
    a = Agent("a")
    p = UpperProcessor(agent=a, user_messages=True, agent_messages=True)
    assert p.user_messages is True
    assert p.agent_messages is True


def test_processor_process_is_called():
    a = Agent("a")
    p = UpperProcessor(agent=a, user_messages=True)
    assert p.process(session=None, message="hello") == "HELLO"
    assert p.process(session=None, message=42) == 42


def test_processor_is_abstract():
    # Cannot instantiate Processor directly because `process` is abstract.
    a = Agent("a")
    with pytest.raises(TypeError):
        Processor(agent=a, user_messages=True)
