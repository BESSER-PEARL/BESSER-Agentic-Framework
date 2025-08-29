import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")

import asyncio
import requests
from aiohttp import web

from besser.agent.core.agent import Agent
# from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.platforms.a2a.server import create_app
from besser.agent.platforms.a2a.task_protocol import create_task, get_status
from besser.agent.platforms.a2a.task_executor import execute_task

agent = Agent('TestAgent')

a2a_platform = agent.use_a2a_platform()

# a2a_platform.agent_card.capabilities = ['print text']
a2a_platform.add_capabilities('print back')
a2a_platform.add_descriptions(['under development'])
a2a_platform.add_examples(['python read_agent_card.py'])

async def echo(msg: str):
    print(f"message is: {msg} before start")
    await asyncio.sleep(60)
    return f"message is: {msg} after ending"

a2a_platform.router.register("agent.card.get", lambda: a2a_platform.get_agent_card())
a2a_platform.router.register("capabilities.list", lambda: a2a_platform.agent_card.capabilities)
a2a_platform.router.register("echo", echo)
a2a_platform.router.register("task_create", create_task)
a2a_platform.router.register("task_status", get_status)

async def create_task_and_run(method: str, params: dict, router):
    task_info = create_task(method, params)
    asyncio.create_task(execute_task(task_info["task_id"], router))
    return task_info

async def rpc_create_task(method: str, params: dict):
    return await create_task_and_run(method, params, a2a_platform.router)

a2a_platform.router.register("create_task_and_run", rpc_create_task)

# print(a2a_platform.get_agent_card())

app = create_app(a2a_platform)
web.run_app(app, port=8000)