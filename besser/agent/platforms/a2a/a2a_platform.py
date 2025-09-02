from __future__ import annotations

import uuid

from typing import TYPE_CHECKING

from aiohttp import web

from besser.agent.library.coroutine.async_helpers import sync_coro_call
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms import a2a
from besser.agent.platforms.a2a.agent_card import AgentCard
# from besser.agent.platforms.a2a.client import *
# from besser.agent.platforms.a2a.server import *
# from besser.agent.platforms.a2a.task_protocol import *
from besser.agent.platforms.payload import Payload
from besser.agent.platforms.a2a.message_router import A2ARouter
from besser.agent.platforms.platform import Platform

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent

class A2APlatform(Platform):
    def __init__(self, agent: Agent, 
                 version: str = '1.0',
                 capabilities: list[str] = [],
                 id: str = str(uuid.uuid4()), 
                 endpoints: list[str] = ["http://localhost:8000/a2a"],
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
        """Returns the agent card in JSON format."""
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
    

        
    