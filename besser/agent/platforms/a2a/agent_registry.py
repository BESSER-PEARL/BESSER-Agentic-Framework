# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
#     from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from aiohttp import web

from besser.agent.exceptions.logger import logger
from besser.agent.platforms.a2a.error_handler import AgentNotFound

class AgentRegistry:
    '''
    Keeps track of registered A2A agents by ID.
    Attributes:
    _agents: dictionary of registered agents
    '''

    def __init__(self):
        self._agents: dict[str, 'A2APlatform'] = {}

    def register(self, agent_id: str, platform: 'A2APlatform') -> None:
        """
        Register the provided agent (through agent_id) in the given platform
        """
        if agent_id in self._agents:
            logger.error(f'Agent ID "{agent_id}" already registered')
            raise ValueError(f'Agent ID "{agent_id}" already registered')
        logger.info(f'Registering agent {agent_id}')
        self._agents[agent_id] = platform

        # Auto-register the methods that are common to all agents.
        if hasattr(platform, "router") and platform.router:
            platform.router.register_task_methods(platform)

    def get(self, agent_id: str) -> 'A2APlatform':
        """
        Get the registered agent
        """
        if agent_id not in self._agents:
            raise ValueError(f'Agent ID "{agent_id}" not found')
        return self._agents[agent_id]

    def list(self) -> list:
        '''
        Return summary info for all registered agents.
        '''
        return [
            {
                "id": agent_id,
                "name": platform.agent_card.name,
                "description": platform.agent_card.descriptions,
                "capabilities": platform.agent_card.capabilities,
                "card_url": f"/agents/{agent_id}/agent-card"
            }
            for agent_id, platform in self._agents.items()
        ]

    def count(self) -> int:
        """
        provide total number of agents that are registered
        """
        return len(self._agents)
    
    # Used for synchronous agent orchestration calls
    async def call_agent_method(self, target_agent_id: str, method: str, params: dict) -> web.json_response:
        target_platform = self.get(target_agent_id)
        if not target_platform:
            raise AgentNotFound(f'Agent ID "{target_agent_id}" not found')
        return await target_platform.router.handle(method, params)
