from __future__ import annotations

import uuid
import asyncio

from typing import TYPE_CHECKING, Callable
from aiohttp import web

from besser.agent.library.coroutine.async_helpers import sync_coro_call
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms import a2a
from besser.agent.platforms.a2a.agent_card import AgentCard
# from besser.agent.platforms.a2a.client import *
# from besser.agent.platforms.a2a.server import *
from besser.agent.platforms.a2a.agent_registry import AgentRegistry
from besser.agent.platforms.payload import Payload
from besser.agent.platforms.a2a.message_router import A2ARouter
from besser.agent.platforms.a2a.error_handler import AgentNotFound
from besser.agent.platforms.platform import Platform
from besser.agent.platforms.a2a.task_protocol import list_all_tasks, create_task, get_status, execute_task, TaskStatus


if TYPE_CHECKING:
    from besser.agent.core.agent import Agent

class A2APlatform(Platform):
    def __init__(self, agent: Agent, 
                 version: str = '1.0',
                 capabilities: list[str] = [],
                 id: str = str(uuid.uuid4()),
                 endpoints: list[str] = ["http://localhost:8000/a2a", "https://localhost:8000/{agent_id}/agent-card", "https://localhost:8000/agents"],
                 descriptions: list[str] = [], 
                 skills: list[str] = [], 
                 examples: list[dict] | list[str] = [],
                 methods: list[dict] = [],
                 provider = "BESSER-Agentic-Framework"):
        super().__init__()
        self._agent: Agent = agent
        self._port: int = self._agent.get_property(a2a.A2A_WEBOSKET_PORT)
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
        '''
        Returns the agent card in JSON format.
        '''
        return self.agent_card.to_json()
    
    def initialize(self) -> None:
        if self._port is not None:
            self._port = int(self._port)
    
    def start(self) -> None:
        logger.info(f'{self._agent.name}\'s A2APlatform starting')
        self._agent.get_or_create_session("A2A_Session_" + str(self.__hash__()), self)
        self.running = True
        self._app.router.add_post("/a2a", self.router.aiohttp_handler)
        self._app.router.add_get("/agent-card", lambda _: web.json_response(self.get_agent_card(), content_type="application/json"))
        web.run_app(self._app, port=self._port, handle_signals=False)
    
    def stop(self):
        self.running = False
        sync_coro_call(self._app.shutdown())
        sync_coro_call(self._app.cleanup())
        logger.info(f'{self._agent.name}\'s A2APlatform stopped')
    
    def _send(self, session_id, payload: Payload) -> None:
        logger.warning(f'_send() method not implemented in {self.__class__.__name__}')

    def reply(self, session: Session, message: str) -> None:
        logger.warning(f'reply() method not implemented in {self.__class__.__name__}')
    
    def add_capabilities(self, capability: list[str] | str):
        if isinstance(capability, str):
            capability = [capability]
        for cap in capability:
            if not cap:
                raise ValueError("Capability cannot be empty")
                # logger.error("Capability cannot be empty")
            self.agent_card.capabilities.extend([cap])
    
    def add_descriptions(self, descriptions: list[str] | str):
        if isinstance(descriptions, str):
            descriptions = [descriptions]
        for desc in descriptions:
            if not desc:
                logger.warning(f"No description is provided for {self._agent.name}")
            self.agent_card.descriptions.extend([desc])
    
    def add_skills(self, skills: list[str] | str):
        if isinstance(skills, str):
            skills = [skills]
        for skill in skills:
            if not skill:
                logger.warning(f"No example is provided for {self._agent.name}")
            self.agent_card.skills.extend([skill])
    
    def add_methods(self, methods: list[dict]):
        """Enables adding methods manually to the agent_card.methods."""
        if not hasattr(self.agent_card, "methods") or self.agent_card.methods is None:
            self.agent_card.methods = []

        for mth in methods:
            if not mth.get("name") or mth.get("name") not in self.router.methods:
                logger.warning(f"Method {mth.get('name')} is not registered in the router of {self._agent.name}")
            if any(mth["name"] == existing["name"] for existing in self.agent_card.methods):
                continue
            self.agent_card.methods.extend([mth])

    def populate_methods_from_router(self):
        """Automatically fetch registered methods from router and add it to the agent_card.methods."""
        method_list = []
        for name, func in self.router.methods.items():
            doc = func.__doc__ or ""
            method_list.append({"name": name, "description": doc})
        self.add_methods(method_list)
    
    def add_examples(self, examples: list[dict] | list[str]):
        if isinstance(examples, str):
            examples = [examples]
        for eg in examples:
            if not eg:
                logger.warning(f"No example is provided for {self._agent.name}")
            self.agent_card.examples.extend([eg])
    
    # Wrappers for task specific functions (given in task_protocol.py) in each platform/agent
    def create_task(self, method, params):
        return create_task(method, params, task_storage=self.tasks)

    def get_status(self, task_id):
        return get_status(task_id, task_storage=self.tasks)

    def list_tasks(self):
        return list_all_tasks(task_storage=self.tasks)

    async def execute_task(self, task_id):
        return await execute_task(task_id, self.router, task_storage=self.tasks)
    
    # Warppers for agent orchestration function in router
    async def rpc_call_agent(self, target_agent_id: str, method: str, params: dict, registry: AgentRegistry):
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
    
    async def rpc_call_agent_tracked(self, target_agent_id: str, method: str, params: dict, registry: AgentRegistry, parent_task=None):
        '''
        Calls another agent as a subtask, waits for it to complete, and returns its task info, results and so on.
        Ensures the orchestration task can track subtask statuses.
        '''
        target_platform = registry.get(target_agent_id)
        if not target_platform:
            raise AgentNotFound(f'Agent ID "{target_agent_id}" not found')

        # Create task on the target agent
        # subtask_coroutine = target_platform.create_and_execute_task(method, params)
        # subtask_task = asyncio.create_task(subtask_coroutine)
        subtask_info = await target_platform.create_and_execute_task(method, params)

        # Track under parent task (ThirdAgent’s orchestration task)
        if parent_task:
            orchestration_task = self.tasks[parent_task["task_id"]]
            orchestration_task.status = TaskStatus.RUNNING
            
            if orchestration_task.result is None:
                orchestration_task.result = {}
            if "subtasks" not in orchestration_task.result:
                orchestration_task.result["subtasks"] = []
            
            orchestration_task.result["subtasks"].append({
            "task_id": subtask_info["task_id"],
            "agent_id": target_agent_id,
            "method": method,
            "status": TaskStatus.PENDING,
            "result": None,
            "error": None
            })
        
        # Launch a watcher coroutine to update parent status in real time
        async def watch_subtask():
            while True:
                t = target_platform.tasks[subtask_info["task_id"]]
                for st in orchestration_task.result.get("subtasks", []):
                    if st["task_id"] == subtask_info["task_id"]:
                        st["status"] = t.status
                        st["result"] = t.result
                        st["error"] = t.error
                        break
                if t.status in [TaskStatus.DONE, TaskStatus.ERROR]:
                    break
                await asyncio.sleep(0.05)

        asyncio.create_task(watch_subtask())

        return subtask_info
    
    # For agent orchestration (no task registration on orchestration agent, only orchestration)
    def register_orchestration_task_on_resp_agent(self, name: str, func: Callable, registry: AgentRegistry):
        '''
        This function is only for async execution of multiple agents, does not register the execution as a task in Orchestrator's task endpoint. 
        Will register tasks on the respective agent's router. So tasks can be tracked only in their respective agent_id/tasks.
        '''
        async def wrapper(**params: dict):
            return await func(self, params, registry)
        self.router.register(name, wrapper)
    
    # For agent orchestration, with orchestration registered as a task. Status can be viewed in the agent_id/tasks endpoint.
    def register_orchestration_as_task(self, name, coroutine_func, registry):
        '''
        Wrap an async orchestration function as a tracked task. Tracking can be done in the orchestration agent_id/tasks endpoint.
        Backward compatible with coro_func.
        '''
        async def runner(**params):
            task_info = self.create_task(name, params) # A separate task for orchestration agent
            orchestration_task = self.tasks[task_info["task_id"]]
            orchestration_task.status = TaskStatus.RUNNING
            orchestration_task.result = {"subtasks": []}
            
            async def orchestration_coroutine(self_inner, p):
                # call the user-provided coroutine_func and await results for all subtasks.
                async def tracked_call(target_agent_id, method, sub_params, registry):
                    # wrapper to inject parent_task info for tracking, in the case of tracked orchestration calls.
                    subtask_info = await self_inner.rpc_call_agent_tracked(
                        target_agent_id, method, sub_params, registry, parent_task=task_info
                    )
                    return subtask_info
                
                result = await coroutine_func(self_inner, p, registry, tracked_call)

                 # Wait for all subtasks (internal Agent's tasks) to finish and update Orchestration Agent's task status
                subtasks = orchestration_task.result.get("subtasks", [])
                if subtasks:
                    while any(registry.get(st["agent_id"]).tasks[st["task_id"]].status not in [TaskStatus.DONE, TaskStatus.ERROR]
                            for st in subtasks):
                        await asyncio.sleep(0.05)
                
                # Update orchestration task result with final results from coroutine_func
                for key, val in result.items():
                    if key != "subtasks": # to avoid overwriting the tracked subtasks info
                        orchestration_task.result[key] = val
                orchestration_task.status = TaskStatus.DONE
                return orchestration_task.result
            
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
    async def create_and_execute_task(self, method: str, params: dict):
        '''
        This is an internal method. It creates a task and runs it in the background (asynchronous).
        '''
        task_info = self.create_task(method, params)
        asyncio.create_task(execute_task(task_info["task_id"], self.router, self.tasks))
        return task_info

    async def rpc_create_task(self, method: str, params: dict):
        '''
        This is an internal method. It creates an asynchronous task and set the status to PENDING execution or RUNNING depending on the tasks queued in the server. Once the execution is done, results will be available here.
        '''
        return await self.create_and_execute_task(method, params)
