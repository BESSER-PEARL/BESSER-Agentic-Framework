import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")

import requests
from aiohttp import web

from besser.agent.core.agent import Agent
from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.platforms.a2a.server import create_app

agent = Agent('TestAgent')

a2a_platform = agent.use_a2a_platform()

# a2a_platform.agent_card.capabilities = ['print text']
a2a_platform.add_capabilities('print back')
a2a_platform.add_descriptions(['under development'])
a2a_platform.add_examples(['python read_agent_card.py'])

a2a_platform.router.register('ping', lambda: 'pong')
a2a_platform.router.register("echo", lambda msg: f"echo: {msg}")

print(a2a_platform.get_agent_card())

app = create_app(a2a_platform)
web.run_app(app, port=8000)