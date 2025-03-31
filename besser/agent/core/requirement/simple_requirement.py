from besser.agent.core.requirement.requirement import Requirement


class SimpleRequirement(Requirement):

    def __init__(self, name: str, score: float):
        super().__init__()
        self.name: str = name
        self.score: float = score

    def __str__(self):
        return self.name
