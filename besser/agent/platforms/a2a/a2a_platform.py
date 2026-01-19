from __future__ import annotations

import uuid
import asyncio

from typing import TYPE_CHECKING, Callable
from enum import Enum
from aiohttp import web

from besser.agent.library.coroutine.async_helpers import sync_coro_call
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms import a2a
from besser.agent.platforms.a2a.agent_card import AgentCard
from besser.agent.platforms.a2a.agent_registry import AgentRegistry
from besser.agent.platforms.payload import Payload
from besser.agent.platforms.a2a.message_router import A2ARouter
from besser.agent.platforms.a2a.error_handler import AgentNotFound
from besser.agent.platforms.platform import Platform
from besser.agent.platforms.a2a.task_protocol import list_all_tasks, create_task, get_status, execute_task, TaskStatus


if TYPE_CHECKING:
    from besser.agent.core.agent import Agent

class A2APlatform(Platform):
    """
    A2APlatform implements the Agent-to-Agent (A2A) communication platform for agent interactions.
    This platform enables agents to communicate with each other using a RESTful API and Server-Sent Events (SSE) over HTTP.
    It stores agent metadata (e.g., capabilities and examples), registers methods, maintains task creation, execution 
    and status tracking, supports tracked and untracked agent-to-agent calls, provides synchronous and asynchronous 
    operations, and supports agent orchestration for coordinating multiple agents.
    
    Args:
        agent (Agent): The agent instance this platform belongs to
        version (str, optional): Version of the agent. Defaults to '1.0'
        capabilities (list[str], optional): List of agent capabilities. Defaults to []
        id (str, optional): Unique identifier for the agent. Defaults to UUID4
        endpoints (list[str], optional): List of API endpoints. Defaults to standard endpoints at localhost:8000
        descriptions (list[str], optional): List of agent descriptions. Defaults to []  
        skills (list[str], optional): List of agent skills. Defaults to []
        examples (Union[list[dict], list[str]], optional): Usage examples. Defaults to []
        methods (list[dict], optional): List of available methods. Defaults to []
        provider (str, optional): Provider name. Defaults to "BESSER-Agentic-Framework"
    
    Attributes:
        _agent (Agent): The agent this platform belongs to
        agent_card (AgentCard): Contains metadata about the agent's capabilities, interface, connection and so on
        router (A2ARouter): Handles routing of messages between agents and agent to endpoints via RPC
        tasks (dict): Storage for registering tasks, managing and monitoring their states
        _port (int): Port number on which this platform will be hosted
        _app (web.Application): Web application to run this platform
    """

    def __init__(self, agent: Agent, 
                 version: str = '1.0',
                 capabilities: list[str] = None,
                 id: str = None,
                 endpoints: list[str] = None,
                 descriptions: list[str] = None, 
                 skills: list[str] = None, 
                 examples: list[dict] | list[str] = None,
                 methods: list[dict] = None,
                 provider = "BESSER-Agentic-Framework"):
        super().__init__()
        if capabilities is None:
            capabilities = []
        if id is None:
            id = str(uuid.uuid4())
        if endpoints is None:
            endpoints = ["http://localhost:8000/agents", "http://localhost:8000/{agent_id}/agent-card", "http://localhost:8000/a2a"]
        if descriptions is None:
            descriptions = []
        if skills is None:
            skills = []
        if examples is None:
            examples = []
        if methods is None:
            methods = []
        self._agent: Agent = agent
        self._port: int = self._agent.get_property(a2a.A2A_WEBSOCKET_PORT)
        self._app: web.Application = web.Application()
        self.router: A2ARouter = A2ARouter()
        self.tasks = {}
        self.agent_card: AgentCard = AgentCard(name=agent._name,
                                               version=version,
                                               id=id, 
                                               endpoints=endpoints, 
                                               capabilities=capabilities, 
                                               descriptions=descriptions, 
                                               skills=skills, 
                                               examples=examples,
                                               methods=methods,
                                               provider=provider)

    def get_agent_card(self) -> AgentCard:
        """
        Returns the agent card in JSON format.
        """
        return self.agent_card.to_json()
    
    def initialize(self) -> None:
        """
        Initializes the platform
        """
        if self._port is not None:
            self._port = int(self._port)
    
    def start(self) -> None:
        """
        Starts the platform
        """
        logger.info(f'{self._agent.name}\'s A2APlatform starting')
        self._agent.get_or_create_session("A2A_Session_" + str(self.__hash__()), self)
        self.running = True
        self._app.router.add_post("/a2a", self.router.aiohttp_handler)
        self._app.router.add_get("/agent-card", lambda _: web.json_response(self.get_agent_card(), content_type="application/json"))
        web.run_app(self._app, port=self._port, handle_signals=False)
    
    def stop(self) -> None:
        """
        Stops the platform
        """
        self.running = False
        sync_coro_call(self._app.shutdown())
        sync_coro_call(self._app.cleanup())
        logger.info(f'{self._agent.name}\'s A2APlatform stopped')
    
    def _send(self, session: Session, payload: Payload) -> None:
        """
        str: log _send() method not implemented in class
        """
        logger.warning(f'_send() method not implemented in {self.__class__.__name__}')

    def reply(self, session: Session, message: str) -> None:
        """
        str: log reply() method not implemented in class
        """
        logger.warning(f'reply() method not implemented in {self.__class__.__name__}')
    
    def add_capabilities(self, capability: list[str] | str) -> None:
        """
        Helper function to add agent's capabilities to the agent_card
        """
        if isinstance(capability, str):
            capability = [capability]
        for cap in capability:
            if not cap:
                raise ValueError("Capability cannot be empty")
                # logger.error("Capability cannot be empty")
            self.agent_card.capabilities.extend([cap])
    
    def add_descriptions(self, descriptions: list[str] | str) -> None:
        """
        Helper function to add agent's description to the agent_card
        """
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        for desc in descriptions:
            if not desc:
                logger.warning(f"No description is provided for {self._agent.name}")
            self.agent_card.descriptions.extend([desc])
    
    def add_skills(self, skills: list[str] | str) -> None:
        """
        Helper function to add agent's skills to the agent_card
        """
        if isinstance(skills, str):
            skills = [skills]
        for skill in skills:
            if not skill:
                logger.warning(f"No skill is provided for {self._agent.name}")
            self.agent_card.skills.extend([skill])
    
    def add_methods(self, methods: list[dict]) -> None:
        """
        Helper function to add agent's methods manually to the agent_card.
        """
        if not hasattr(self.agent_card, "methods") or self.agent_card.methods is None:
            self.agent_card.methods = []

        for mth in methods:
            if not mth.get("name") or mth.get("name") not in self.router.methods:
                logger.warning(f"Method {mth.get('name')} is not registered in the router of {self._agent.name}")
            if any(mth["name"] == existing["name"] for existing in self.agent_card.methods):
                continue
            self.agent_card.methods.extend([mth])

    def populate_methods_from_router(self) -> None:
        """
        Automatically fetch agent's registered methods from router and add it to the agent_card.
        """
        method_list = []
        for name, func in self.router.methods.items():
            doc = func.__doc__ or ""
            method_list.append({"name": name, "description": doc})
        self.add_methods(method_list)
    
    def add_examples(self, examples: list[dict] | list[str]) -> None:
        """
        Helper function to add agent execution examples to the agent_card
        """
        if isinstance(examples, str):
            examples = [examples]
        for eg in examples:
            if not eg:
                logger.warning(f"No example is provided for {self._agent.name}")
            self.agent_card.examples.extend([eg])
    
    # Wrappers for task specific functions (given in task_protocol.py) in each platform/agent
    def create_task(self, method: Callable, params: dict) -> dict:
        return create_task(method, params, task_storage=self.tasks)

    def get_status(self, task_id: str) -> dict:
        return get_status(task_id, task_storage=self.tasks)

    def list_tasks(self) -> list:
        return list_all_tasks(task_storage=self.tasks)

    async def execute_task(self, task_id: str) -> dict:
        return await execute_task(task_id, self.router, task_storage=self.tasks)
    
    # Wrappers for agent orchestration function in router
    async def rpc_call_agent(self, target_agent_id: str, method: str, params: dict, registry: AgentRegistry) -> dict:
        '''
        Calls another agent as a subtask, waits for it to complete, and returns its task info, results and so on.
        Orchestration task cannot track subtask statuses. They can be tracked in the respective agent_id/tasks endpoint.
        '''
        target_platform = registry.get(target_agent_id)
        if not target_platform:
            raise AgentNotFound(f'Agent ID "{target_agent_id}" not found')
        task_info = await target_platform.rpc_create_task(method, params)
        return task_info
        # All the above lines can be replaced with the following one, if one expects a synchronous call and wait for the result.
        # return await registry.call_agent_method(target_agent_id, method, params)
    
    async def rpc_call_agent_tracked(self, target_agent_id: str, method: str, params: dict, registry: AgentRegistry, parent_task=None) -> dict:
        '''
        Calls another agent as a subtask, waits for it to complete, and returns its task info, results and so on.
        Ensures the orchestration task can track subtask statuses at orchestrator agent_id/tasks endpoint.
        '''
        target_platform = registry.get(target_agent_id)
        if not target_platform:
            raise AgentNotFound(f'Agent ID "{target_agent_id}" not found')

        # Create task on the target agent
        subtask_info = await target_platform.create_and_execute_task(method, params)

        # Track under parent task (orchestrator agent's task)
        if parent_task:
            orchestration_task = self.tasks[parent_task["task_id"]]
            orchestration_task.status = TaskStatus.RUNNING
            orchestration_task.is_orchestration = True
            
            if orchestration_task.result is None:
                orchestration_task.result = {}
            if "subtasks" not in orchestration_task.result:
                orchestration_task.result["subtasks"] = []
            
            orchestration_task.result["subtasks"].append({
            "task_id": subtask_info["task_id"],
            "agent_id": target_agent_id,
            "method": method,
            "status": subtask_info.get("status").value if isinstance(subtask_info.get("status"), Enum) else subtask_info.get("status", TaskStatus.PENDING),
            "result": subtask_info.get("result"),
            "error": subtask_info.get("error")
            })

            await orchestration_task.notify_subscribers({
                "type": "subtask_created",
                "subtask_id": subtask_info["task_id"],
                "parent_task_id": parent_task["task_id"]
            })
        
        # Launch a watcher coroutine to update parent status in real time
        async def watch_subtask() -> dict:
            last_status = None # for SSE
            last_result = None # for SSE
            last_error = None # for SSE

            while True:
                t = target_platform.tasks[subtask_info["task_id"]]

                # for SSE - notify if something changes in the task status/result/upon error
                if (t.status != last_status) or (t.result != last_result) or (t.error != last_error):
                    last_status, last_result, last_error = t.status, t.result, t.error

                    for st in orchestration_task.result.get("subtasks", []):
                        if st["task_id"] == subtask_info["task_id"]:
                            st["status"] = t.status.value if isinstance(t.status, Enum) else t.status
                            st["result"] = t.result
                            st["error"] = t.error
                            break
                    
                    # Notify subscribers of any change for SSE
                    await orchestration_task.notify_subscribers({
                        "type": "subtask_update",
                        "parent_task_id": orchestration_task.id,
                        "subtask": {
                            **st,
                            "status": st["status"]  # already a string
                        }
                    })
                    await t.notify_subscribers({
                        "type": "task_update",
                        "task_id": t.id,
                        "status": t.status,
                        "result": t.result,
                        "error": t.error
                    })
                
                creation_done = orchestration_task.result.get("creation_done", False)
                subtasks = orchestration_task.result.get("subtasks", [])

                all_done = len(subtasks) > 0 and all(st["status"] in [TaskStatus.DONE, TaskStatus.ERROR] for st in subtasks)
                
                if not creation_done:
                    # During multiple sequential execution, creation_done is set to True for milliseconds before next task is being added to the list of tasks
                    # To avoid this false flag and make the following if condition True, we need to wait untill no more tasks are pending to be added.
                    await asyncio.sleep(0.5)
                    continue

                if creation_done and all_done and orchestration_task.status != TaskStatus.DONE:
                    # await asyncio.sleep(0.1) # give time for the watcher of the last task to post the subtask_update
                    if orchestration_task.status == TaskStatus.DONE:
                        break # If multiple subtask watchers enter this IF condition simultaneously, then only the first watcher can set the status to DONE and proceed forward to post task_final, others will exit here. This done to avoid multiple task_final report in the SSE endpoint.
                    orchestration_task.status = TaskStatus.DONE
                    await orchestration_task.notify_subscribers({
                        "type": "task_final",
                        "task_id": orchestration_task.id,
                        "status": orchestration_task.status if not isinstance(orchestration_task.status, Enum) else orchestration_task.status.value,
                        "result": orchestration_task.result,
                        "error": orchestration_task.error,
                    })
                    break
                await asyncio.sleep(0.01)

        asyncio.create_task(watch_subtask()) # invoke watcher for each subtask. Each watcher will be executed in async manner.

        return subtask_info
    
    # For agent orchestration (no task registration on orchestration agent, only orchestration)
    def register_orchestration_task_on_resp_agent(self, name: str, func: Callable, registry: AgentRegistry) -> web.json_response:
        '''
        This function is only for async execution of multiple agents, does not register the execution as a task in Orchestrator's task endpoint. 
        Will register tasks on the respective agent's router. So tasks can be tracked only in their respective agent_id/tasks.
        '''
        async def wrapper(**params: dict):
            return await func(self, params, registry)
        self.router.register(name, wrapper)
    
    # For agent orchestration, with orchestration registered as a task. Status can be viewed in the agent_id/tasks endpoint.
    def register_orchestration_as_task(self, name: str, coroutine_func: Callable, registry: AgentRegistry) -> dict:
        '''
        Wrap an async orchestration function as a tracked task. Tracking can be done in the orchestration agent_id/tasks endpoint.
        Backward compatible with coroutine_func.
        '''
        async def runner(**params: dict) -> dict:
            task_info = self.create_task(name, params) # A separate task for orchestration agent
            orchestration_task = self.tasks[task_info["task_id"]]
            orchestration_task.status = TaskStatus.RUNNING
            orchestration_task.result = {"subtasks": [], "creation": False}
            
            async def orchestration_coroutine(self_inner, p: dict):
                # call the user-provided coroutine_func and await results for all subtasks.
                async def tracked_call(target_agent_id, method, sub_params, registry):
                    # wrapper to inject parent_task info for tracking, in the case of tracked orchestration calls.
                    subtask_info = await self_inner.rpc_call_agent_tracked(
                        target_agent_id, method, sub_params, registry, parent_task=task_info
                    )
                    return subtask_info
                
                # run the orchestration coroutine function
                result = await coroutine_func(self_inner, p, registry, tracked_call, orchestration_task)
                
                #------------------------------------------------------------------------------------------------------ 
                # 1. Inform the SSE module that all tasks are created when the final task is created (after return from coroutine function)
                # 2. Inform the user too (currently not done as it is not useful for the user)
                # 3. This will prevent SSE from assuming all tasks are done and print the "task_final" report
                orchestration_task.result["creation_done"] = True
                # await orchestration_task.notify_subscribers({
                #     "type": "creation_done",
                #     "task_id": orchestration_task.id,
                #     "result": orchestration_task.result
                # })
                #------------------------------------------------------------------------------------------------------
                
                # Wait for all subtasks (internal Agent's tasks) to finish and update Orchestration Agent's task status
                subtasks = orchestration_task.result.get("subtasks", [])
                if subtasks:
                    while any(registry.get(st["agent_id"]).tasks[st["task_id"]].status not in [TaskStatus.DONE, TaskStatus.ERROR]
                            for st in subtasks):
                        await asyncio.sleep(0.05)
                
                # Following for loop is required only if the user provides a return from the orchestration function.
                # In that case, result will not be {}, and this for loop will get executed, else this will be skipped.
                final_result = {}
                # Refreshing subtask with live tracked entries
                for key, val in result.items():
                    if isinstance(val, dict) and "task_id" in val:
                        # find live subtask entry
                        for st in orchestration_task.result.get("subtasks", []):
                            if st["task_id"] == val["task_id"]:
                                final_result[key] = st
                                break
                    elif key != "subtasks": # to avoid overwriting the tracked subtasks info
                        final_result[key] = val
                
                # Update orchestration task result with final results from coroutine_func
                orchestration_task.result.update(final_result)

                orchestration_task.status = TaskStatus.DONE

                # Remove subtasks from result as soon as execution is done to avoid clutter and repetition.
                # Currently, the following is commented out as the agent's link to task monitoring endpoint is cut off 
                # immediately after its execution is finished and before the task status gets updated in the endpoint. 
                # This leads the agent's status to be stuck in RUNNING mode even when it is completed. Following line can be
                # uncommented (each agent should have a return in that case) after this bug is resolved. 
                # if "subtasks" in orchestration_task.result:
                #     orchestration_task.result.pop("subtasks")

                return orchestration_task.result
            
            # Execute orchestration as a background tracked task
            asyncio.create_task(
                execute_task(
                    task_id=task_info["task_id"], 
                    router=self,
                    task_storage=self.tasks, 
                    coroutine_func=orchestration_coroutine, 
                    params=params
                    )
                )

            return task_info
    
        self.router.register(name, runner)
    
    # Task execution methods
    async def create_and_execute_task(self, method: str, params: dict) -> dict:
        """
        This is an internal method. It creates a task and runs it in the background (asynchronous).
        """
        task_info = self.create_task(method, params)
        asyncio.create_task(execute_task(task_info["task_id"], self.router, self.tasks))
        return task_info

    async def rpc_create_task(self, method: str, params: dict) -> dict:
        '''
        This is an internal method. It creates an asynchronous task and set the status to PENDING execution or RUNNING depending on the tasks queued in the server. Once the execution is done, results will be available here.
        '''
        return await self.create_and_execute_task(method, params)
