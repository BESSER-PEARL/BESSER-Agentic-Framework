from besser.agent.platforms.a2a.a2a_platform import A2APlatform
from besser.agent.exceptions.logger import logger

class AgentRegistry:
    '''
    Keeps track of registered A2A agents by ID.
    '''

    def __init__(self):
        self._agents: dict[str, A2APlatform] = {}

    def register(self, agent_id: str, platform: A2APlatform):
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already registered")
        logger.info(f"Registering agent {agent_id}")
        self._agents[agent_id] = platform

    def get(self, agent_id: str) -> A2APlatform:
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")
        return self._agents[agent_id]

    def list(self) -> dict:
        '''
        Return summary info for all registered agents.
        '''
        return [
            {
                "id": agent_id,
                "name": platform.agent_card.name,
                "description": platform.agent_card.descriptions,
                "capabilities": platform.agent_card.capabilities,
                "endpoints": platform.agent_card.endpoints
            }
            for agent_id, platform in self._agents.items()
        ]

    def count(self) -> int:
        return len(self._agents)
