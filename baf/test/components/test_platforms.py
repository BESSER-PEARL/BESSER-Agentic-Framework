"""Smoke tests for each Platform wrapper.

We instantiate each platform on an Agent without starting its network loop.
This guarantees that the registration path (`agent.use_*_platform`) wires the
platform correctly and that its Python dependencies resolve in the current
environment.
"""

import pytest

from baf.core.agent import Agent
from baf.platforms.platform import Platform


def test_platform_is_abstract():
    with pytest.raises(TypeError):
        Platform()  # abstract class


def test_websocket_platform_registration():
    agent = Agent("ws_agent")
    platform = agent.use_websocket_platform(use_ui=False)
    assert platform in agent._platforms
    assert platform.running is False
    assert hasattr(platform, "initialize")
    assert hasattr(platform, "start")
    assert hasattr(platform, "stop")


def test_telegram_platform_registration():
    agent = Agent("tg_agent")
    platform = agent.use_telegram_platform()
    assert platform in agent._platforms
    assert platform.running is False


def test_github_platform_registration():
    agent = Agent("gh_agent")
    platform = agent.use_github_platform()
    assert platform in agent._platforms
    assert platform.running is False


def test_gitlab_platform_registration():
    agent = Agent("gl_agent")
    platform = agent.use_gitlab_platform()
    assert platform in agent._platforms
    assert platform.running is False


def test_a2a_platform_registration():
    agent = Agent("a2a_agent")
    platform = agent.use_a2a_platform()
    assert platform in agent._platforms
    assert platform.running is False


def test_fake_platform_fixture_is_usable(fake_platform):
    assert fake_platform.running is False
    fake_platform.start()
    assert fake_platform.running is True
    fake_platform.stop()
    assert fake_platform.running is False
