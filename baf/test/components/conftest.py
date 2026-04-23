"""Shared fixtures for framework component tests."""

from __future__ import annotations

import pytest

from baf.core.agent import Agent
from baf.platforms.platform import Platform


class FakePlatform(Platform):
    """Minimal in-memory Platform implementation for tests.

    Captures replies in a list instead of hitting the network. Satisfies the
    abstract contract of :class:`Platform` so that Session/Agent code paths
    that depend on a platform can be exercised without real I/O.
    """

    def __init__(self):
        super().__init__()
        self.replies: list[tuple[str, str]] = []  # (session_id, message)
        self.sent_payloads: list[tuple[str, object]] = []

    def initialize(self) -> None:
        pass

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def _send(self, session_id: str, payload) -> None:
        self.sent_payloads.append((session_id, payload))

    def reply(self, session, message: str) -> None:
        self.replies.append((session.id, message))


@pytest.fixture
def fake_platform() -> FakePlatform:
    return FakePlatform()


@pytest.fixture
def agent() -> Agent:
    """Fresh, empty agent with no platforms configured."""
    return Agent("test_agent")


@pytest.fixture
def agent_with_platform(fake_platform) -> Agent:
    """Agent that has the fake platform registered."""
    a = Agent("test_agent_platform")
    a._platforms.append(fake_platform)
    return a
