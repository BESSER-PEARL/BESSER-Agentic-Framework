from pydantic import BaseModel

class AgentCard(BaseModel):
    """
    Represents the agent card that has the metadata and description about the agent.
    """
    # Define the fields and their type for the agent card
    name: str
    id: str
    endpoints: list[str]
    version: str
    capabilities: list[str]
    descriptions: list[str]
    provider: str
    skills: list[str]
    examples: list[dict] | list[str] = []
    methods: list[dict] = []

    def to_json(self):
        return self.model_dump_json(indent=4)
    
    @classmethod
    def from_json(cls, json_str):
        return cls.model_validate_json(json_str)
