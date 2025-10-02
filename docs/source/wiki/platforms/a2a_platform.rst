A2A platform
============

A2A (Agent-to-Agent) is a platform that follows Google's `A2A protocol <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability>`_ and allows direct communication between agents developed using BESSER-Agentic-Framework and other frameworks too.


How to use it
-------------

Required imports are:

.. code:: python

    import asyncio
    from aiohttp import web
    from besser.agent.core.agent import Agent
    from besser.agent.platforms.a2a.agent_registry import AgentRegistry
    from besser.agent.platforms.a2a.server import create_app


Define an agent (with its name), attach it to an A2A platform and register the agent's platform with an ID (this is the agent ID that the users will use to identify this agent).

.. code:: python

    registry = AgentRegistry()
    agent = Agent('TestAgent')
    a2a_platform = agent.use_a2a_platform()
    registry.register('test_platform', a2a_platform)


Define an asynchronous method that the agent has to execute (the functionality of agent) and register it in the corresponding agent's platform's router with your desired ID (this is the method ID that the users will use to invoke this method).

.. code:: python

    async def my_method(method_params: dict):
        # Logic of this method
    
    a2a_platform.router.register("method_id", my_method)


You can add the agent's metadata using the built-in helper functions.

.. code:: python

    a2a_platform.add_capabilities(['capability1', 'capability2'])
    a2a_platform.add_descriptions(['description1', 'description2'])
    a2a_platform.add_examples([{'first example': 'example1', 'second example': 'example2'}])


To add agent specific methods to agent's metadata, either an automated built-in function (automatically identify and add methods that are regitered with the platform's router) or the helper function to add it manually can be used.

.. code:: python

    a2a_platform.populate_methods_from_router() # method description will be taken from method's doc string 


or

.. code:: python

    a2a_platform.add_methods([{"name": "my_method", "description": "method description"}])

Execute the platform on port=8000 using the following lines. Registry has the platform (agent(s)) and platform has the method(s) corresponding to the agent(s).

.. code:: python

    app = create_app(registry=registry)
    web.run_app(app, port=8000)


Executing this script will provide a message similar to the following in your terminal window.

.. code-block:: bash

    <timestamp> - BESSER Agentic Framework - INFO - Registering agent TestAgent
    ======== Running on http://0.0.0.0:8000 ========
    (Press CTRL+C to quit)


In a browser, you can see the agents hosted on your server at the endpoint: `http://localhost:8000/agents <http://localhost:8000/agents>`_. Each agent will have its ID, name, 
description, capabilities and a link to its agent card.

In a browser, you can see the agent card of your agent at the endpoint: `http://localhost:8000/agents/test_platform/agent-card <http://localhost:8000/agents/test_platform/agent-card>`_. 
test_platform is our agent_id. For getting the agent card of another agent, test_platform should be replaced with the corresponding agent's agent_id.

.. note:: Methods corresponding to the following method IDs are by default included in all the agents:

    **method_id: task_create, params: method, params** - creates a new synchronous/asynchronous task (for executing the method given in params) and adds it to the task dictionary.
    
    **method_id: create_task_and_run, params: method, params** - creates a new asynchronous task (for executing the method given in params), adds it to the task dictionary, 
    sets task's status to PENDING and executes the method provided within params. When the execution starts, corresponding task's status will be changed to RUNNING and 
    once the execution is finished, the status will be changed to DONE. In case of an error, its status will be changed to ERROR.
    
    **method_id: task_status, params: task_id** - provides the current status of the task (PENDING, RUNNING, DONE/ERROR) based on its agent_id and task_id.

In a different terminal, you can use the agent present on your server hosted at `http://localhost:8000/a2a <http://localhost:8000/a2a>`_ endpoint. 
Here is an example CURL command for using the agent.

To send a message to the server from your system (in a different terminal than the one that is executing your script)

.. code-block:: bash

    curl -X POST http://localhost:8000/a2a \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0", "agent_id": "test_platform", "method": "create_task_and_run", "params":{"method":"method_id", "params":{method_params:<param_key>}}, "id":1}'

There are three ways to get the status of the task that is being executed in the agent: 

1. by CURL command in the terminal

2. In browser via HTTP polling.

3. In browser via SSE. You can watch the result/status live, no need to refresh the page.

.. code-block:: bash

    curl -X POST http://localhost:8000/a2a \
        -H "Content-Type: application/json" \
        -d '{"jsonrpc":"2.0", "agent_id": "test_platform", "method": "task_status", "params":{"task_id":<task_id>}, "id":2}'

or

Open in browser: `https:localhost:8000/agents/test_platform/tasks <https:localhost:8000/agents/test_platform/tasks>`_

or

Open in browser: `https:localhost:8000/agents/test_platform/events/<task_id> <https:localhost:8000/agents/test_platform/events/\<task_id\>>`_


.. note:: 
    
    The above mentioned example is for executing a single agent. There are multiple ways this platform can be used. For three agents named A, B and C, the following are also possible.

    Executing agent A or B or C (same as above)

    De-centralised orchestration: Using agent A to invoke agent B

    Parallel execution: A || B || ...

    Sequential execution: A -> B -> ...

    Hybrid execution: A || B -> C ...

More examples can be viewed at :doc:`/examples/a2a_multiagent`

API References
--------------

For more details, see the :class:`besser.agent.platforms.a2a.A2APlatform` class documentation.

- Agent: :class:`besser.agent.core.agent.Agent`
- Agent.use_a2a_platform(): :meth:`besser.agent.core.agent.Agent.use_a2a_platform`
- A2APlatform: :class:`besser.agent.platforms.a2a.a2a_platform.A2APlatform`
- AgentCard: :class:`besser.agent.platforms.a2a.agent_card.AgentCard`
- HTTP_polling(): :meth:`besser.agent.platforms.a2a.server.a2a_handler`
- SSE(): :meth:`besser.agent.platforms.a2a.server.sse_event_handler`
- Task: :class:`besser.agent.platforms.a2a.task_protocol.Task`
- A2ARouter: :class:`besser.agent.platforms.a2a.message_router.A2ARouter`
- aiohttp_handler(): :meth:`besser.agent.platforms.a2a.message_router.A2ARouter.aiohttp_handler`
- error_response(): :meth:`besser.agent.platforms.a2a.error_handler.error_response`
- AgentRegistry: :class:`besser.agent.platforms.a2a.agent_registry.AgentRegistry`
- rpc_call_agent(): :meth:`besser.agent.platforms.a2a.a2a_platform.A2APlatform.rpc_call_agent`
- rpc_call_agent_tracked(): :meth:`besser.agent.platforms.a2a.a2a_platform.A2APlatform.rpc_call_agent_tracked`
- register_orchestration_as_task(): :meth:`besser.agent.platforms.a2a.a2a_platform.A2APlatform.register_orchestration_as_task`