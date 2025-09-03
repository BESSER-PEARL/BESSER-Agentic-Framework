import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")

import asyncio
import requests
from aiohttp import web

from besser.agent.core.agent import Agent
# from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.platforms.a2a.server import create_app
from besser.agent.platforms.a2a.task_protocol import create_task, get_status, execute_task

agent = Agent('TestAgent')

a2a_platform = agent.use_a2a_platform()

async def echo(msg: str):
    '''
    A simple echo method that waits for 60 seconds before returning the message.
    '''
    if not isinstance(msg, str):
        raise ValueError("msg must be a string")
    
    print(f"message is: {msg} before start")
    await asyncio.sleep(60)
    return f"message is: {msg} after ending"

async def failing_method():
    '''
    Checking exception handling in A2A.
    '''
    raise Exception('exception_raised')

a2a_platform.router.register("echo_message", echo)
a2a_platform.router.register("task_create", create_task)
a2a_platform.router.register("task_status", get_status)
a2a_platform.router.register("failing_method", failing_method)

async def create_and_execute_task(method: str, params: dict, router):
    '''
    Creates a task and runs it in the background.
    '''
    task_info = create_task(method, params)
    asyncio.create_task(execute_task(task_info["task_id"], router))
    return task_info

async def rpc_create_task(method: str, params: dict):
    '''
    Creates a task and waits for its execution to be completed before providing the result.
    '''
    return await create_and_execute_task(method, params, a2a_platform.router)

a2a_platform.router.register("create_task_and_run", rpc_create_task)

# print(a2a_platform.get_agent_card())
# a2a_platform.agent_card.capabilities = ['print text']
a2a_platform.add_capabilities('Prints the entered message')
a2a_platform.add_descriptions(['Waits for 60 seconds and then provides the entered message'])

methods_info = [{"name": 'create_task_and_run', "description": 'Creates a task and waits for its execution to be completed before providing the result.'}, {"name": "My method", "description": "My method description"}]

a2a_platform.add_methods(methods_info)
a2a_platform.populate_methods_from_router()
a2a_platform.add_examples([{'To execute "echo_message" method': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"create_task_and_run\",\"params\":{\"method\":\"echo_message\",\"params\":{\"msg\":\"hellloooo1\"}},\"id\":1}"', 'To get status of the task with task_id': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"method\":\"task_status\",\"params\":{\"task_id\":\"<task_id>\"},\"id\":2}"'}])

app = create_app(platform=a2a_platform)
web.run_app(app, port=8000)