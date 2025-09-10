import sys
sys.path.append("C:/Users/chidambaram/Downloads/GitHub/BESSER-Agentic-Framework_Natarajan")

import asyncio
import requests
from aiohttp import web

from besser.agent.core.agent import Agent
from besser.agent.platforms.a2a.agent_registry import AgentRegistry
# from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.platforms.a2a.server import create_app

registry = AgentRegistry()

agent1 = Agent('TestAgent1')
agent2 = Agent('TestAgent2')
agent3 = Agent('TestAgent3')

a2a_platform1 = agent1.use_a2a_platform()
a2a_platform2 = agent2.use_a2a_platform()
a2a_platform3 = agent3.use_a2a_platform()

registry.register('EchoAgent', a2a_platform1)
registry.register('SummationAgent', a2a_platform2)
registry.register('ThirdAgent', a2a_platform3)

# print(f"Total registered agents: {registry.count()}")
# print(registry.get("EchoAgent")._agent.name)
# print(registry.get("SummationAgent")._agent.name)

async def echo(msg: str):
    '''
    A simple echo method that waits for 45 seconds before returning the message.
    '''
    if not isinstance(msg, str):
        raise ValueError("msg must be a string")
    
    await asyncio.sleep(45)
    return f"message is: {msg} after ending"

async def do_summation(num1: int, num2: int):
    '''
    A simple summation method that waits for 45 seconds before returning the summation.
    '''
    if not isinstance(num1, int) or not isinstance(num2, int):
        raise ValueError("Please enter integers only")
    
    await asyncio.sleep(45)
    return f"summation is: {num1+num2}"

# async def failing_method():
#     '''
#     Checking exception handling in A2A.
#     '''
#     raise Exception('exception_raised')

a2a_platform1.router.register("echo_message", echo)
a2a_platform2.router.register("do_summation", do_summation)

a2a_platform1.add_capabilities('Prints the entered message')
a2a_platform1.add_descriptions(['Waits for 45 seconds and then provides the entered message'])

# methods_info = [{"name": 'create_task_and_run', "description": 'Creates a task and waits for its execution to be completed before providing the result.'}, {"name": "My method", "description": "My method description"}]

# a2a_platform1.add_methods(methods_info)
a2a_platform1.populate_methods_from_router()
a2a_platform1.add_examples([{'To execute "echo_message" method': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"agent_id\":\"EchoAgent\", \"method\":\"create_task_and_run\",\"params\":{\"method\":\"echo_message\",\"params\":{\"msg\":\"hellloooo1\"}},\"id\":1}"', 'To get status of the task with task_id': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"agent_id\":\"EchoAgent\",\"method\":\"task_status\",\"params\":{\"task_id\":\"<task_id>\"},\"id\":2}"'}])

a2a_platform2.add_capabilities('Prints summation of two numbers')
a2a_platform2.add_descriptions(['Waits for 45 seconds and then provides the summation of two entered numbers'])
a2a_platform2.populate_methods_from_router()
a2a_platform2.add_examples([{'To execute "echo_message" method': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"agent_id\":\"SummationAgent\", \"method\":\"create_task_and_run\",\"params\":{\"method\":\"do_summation\",\"params\":{\"int1\":2, \"int2\":4}},\"id\":1}"', 'To get status of the task with task_id': 'curl -X POST http://localhost:8000/a2a -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"agent_id\":\"SummationAgent\",\"method\":\"task_status\",\"params\":{\"task_id\":\"<task_id>\"},\"id\":2}"'}])

# For orchestration, register the orchestration methods in each agent's router. This enables an agent (e.g., EchoAgent) to call another agent (e.g., SummationAgent).
for agent_id, platform in registry._agents.items():
    if hasattr(platform, "router"):
        platform.router.register_orchestration_methods(platform, registry)

# Separate agent for orchestration (only orchestration, no tasks)
async def orchestrate_echo_and_sum(platform, params, registry):
    '''
    Orchestrates EchoAgent and SummationAgent tasks.
    params: dict containing {'msg': str, 'num1': int, 'num2': int}
    '''
    echo_task = await platform.rpc_call_agent(
        "EchoAgent", 
        "echo_message", 
        {"msg": params["msg"]}, 
        registry
    )
    sum_task = await platform.rpc_call_agent(
        "SummationAgent", 
        "do_summation", 
        {"num1": params["num1"], "num2": params["num2"]}, 
        registry
    )
    return {"echo_task": echo_task, "sum_task": sum_task}

async def orchestrate_echo_and_sum_tracked(platform, params, registry, tracked_call, orchestration_task):
    '''
    Orchestrates EchoAgent and SummationAgent tasks.
    params: dict containing {'msg': str, 'num1': int, 'num2': int}
    '''
    echo_task = await tracked_call(
        "EchoAgent", 
        "echo_message", 
        {"msg": params["msg"]}, 
        registry
    )
    sum_task = await tracked_call(
        "SummationAgent", 
        "do_summation", 
        {"num1": params["num1"], "num2": params["num2"]}, 
        registry
    )
    # return {}
    orchestration_result = {}
    for st in orchestration_task.result.get("subtasks", []):
        if st["agent_id"] == "EchoAgent":
            orchestration_result["echo_task"] = st
        elif st["agent_id"] == "SummationAgent":
            orchestration_result["sum_task"] = st

    return orchestration_result
    # return {"echo_task": echo_task, "sum_task": sum_task}

# a2a_platform3.register_orchestration_task_on_resp_agent("orchestrate_tasks", orchestrate_echo_and_sum, registry)
# a2a_platform3.register_orchestration_task("orchestrate_tasks_tracked", a2a_platform3.wrap_as_task("orchestrate_tasks", orchestrate_echo_and_sum), registry)
a2a_platform3.register_orchestration_as_task("orchestrate_tasks_tracked", orchestrate_echo_and_sum_tracked, registry)


# Run the platform with registry containing registered agents.
app = create_app(registry=registry)
web.run_app(app, port=8000)

