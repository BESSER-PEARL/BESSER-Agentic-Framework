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
agent4 = Agent('TestAgent4')

a2a_platform1 = agent1.use_a2a_platform()
a2a_platform2 = agent2.use_a2a_platform()
a2a_platform3 = agent3.use_a2a_platform()
a2a_platform4 = agent4.use_a2a_platform()

registry.register('EchoAgent', a2a_platform1)
registry.register('SummationAgent', a2a_platform2)
registry.register('OrchAgent', a2a_platform3)
registry.register('FinalSumAgent', a2a_platform4)

# print(f"Total registered agents: {registry.count()}")
# print(registry.get("EchoAgent")._agent.name)
# print(registry.get("SummationAgent")._agent.name)

async def echo(msg: str):
    '''
    A simple echo method that waits for 30 seconds before returning the message.
    '''
    if not isinstance(msg, str):
        raise ValueError("msg must be a string")
    
    await asyncio.sleep(30)
    return f"message is: {msg}"

async def do_summation(num1: int, num2: int):
    '''
    A simple summation method that waits for 30 seconds before returning the summation.
    '''
    if not isinstance(num1, int) or not isinstance(num2, int):
        raise ValueError("Please enter integers only")
    
    await asyncio.sleep(30)
    return f"{num1+num2}"

async def final_summation(sum: int, num1: int):
    '''
    A simple echo method that waits for 20 seconds before returning the message.
    '''
    if not isinstance(sum, int) or not isinstance(num1, int):
        raise ValueError("numbers must be a integer")
    
    await asyncio.sleep(20)
    return f"{sum+num1}"

async def await_subtask_result(orchestration_task, subtask, poll_interval=0.1):
    '''
    This is an internal and private helper function to await a subtask's result within an orchestration task.
    '''
    while True:
        for st in orchestration_task.result.get("subtasks", []):
            if st["task_id"] == subtask["task_id"]:
                if st["status"] in ["DONE", "ERROR"]:
                    return st.get("result")
                break
        await asyncio.sleep(poll_interval)

# async def failing_method():
#     '''
#     Checking exception handling in A2A.
#     '''
#     raise Exception('exception_raised')

a2a_platform1.router.register("echo_message", echo)
a2a_platform2.router.register("do_summation", do_summation)
a2a_platform4.router.register("do_summation", do_summation)
a2a_platform4.router.register("final_summation", final_summation)

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

a2a_platform4.add_capabilities('Displays the summation result')
a2a_platform4.add_descriptions(['Gets the summation of two numbers from the SummationAgent, waits for 30 seconds, adds it to another number, and prints the summation'])
a2a_platform4.add_methods([{"name": "do_summation", "description": "Gets the summation of two numbers from the SummationAgent, waits for 30 seconds, adds it to another number, and prints the summation."}])
a2a_platform4.add_examples([{'Not a standalone execution':'This will be executed in orchestration way, not a standalone'}])

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

# Separate agent for orchestration (also has its own registered tasks)
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

    # Enable the following lines if the following behaviour is wanted: 
    # Under the orchestration result, displays each agent's results (mostly duplicate of what is found in subtasks).
    # orchestration_result = {}
    # for st in orchestration_task.result.get("subtasks", []):
    #     if st["agent_id"] == "EchoAgent":
    #         orchestration_result["echo_task"] = st
    #     elif st["agent_id"] == "SummationAgent":
    #         orchestration_result["sum_task"] = st
    # orchestration_result["pipeline"] = "Echo and Summation in parallel."

    # return orchestration_result
    return {}

# Separate agent for orchestration (also has its own registered tasks)
async def orchestrate_echo_sum_display_seq_tracked(platform, params, registry, tracked_call, orchestration_task):
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
    sum_result = await await_subtask_result(orchestration_task, sum_task, poll_interval=0.2)
    
    display_task = await tracked_call(
        "FinalSumAgent", 
        "final_summation", 
        {"sum": int(sum_result), "num1": params["num3"]},
        registry
    )
    # orchestration_result = {}
    # for st in orchestration_task.result.get("subtasks", []):
    #     if st["agent_id"] == "EchoAgent":
    #         orchestration_result["echo_task"] = st
    #     elif st["agent_id"] == "SummationAgent":
    #         orchestration_result["sum_task"] = st
    # orchestration_result["pipeline"] = "Echo and Summation in parallel."

    # return orchestration_result
    return {}

# a2a_platform3.register_orchestration_task_on_resp_agent("orchestrate_tasks", orchestrate_echo_and_sum, registry)
# a2a_platform3.register_orchestration_task("orchestrate_tasks_tracked", a2a_platform3.wrap_as_task("orchestrate_tasks", orchestrate_echo_and_sum), registry)
# a2a_platform3.register_orchestration_as_task("orchestrate_tasks_tracked", orchestrate_echo_and_sum_tracked, registry)
a2a_platform3.register_orchestration_as_task("orchestrate_tasks_tracked_seq", orchestrate_echo_sum_display_seq_tracked, registry)

# Run the platform with registry containing registered agents.
app = create_app(registry=registry)
web.run_app(app, port=8000)

