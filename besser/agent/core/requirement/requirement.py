from abc import ABC

from besser.agent.core.session import Session


class Requirement(ABC):

    def __init__(self):
        pass

    def evaluate(self, session: Session) -> bool:
        pass


class RequirementDefinition:

    def __init__(self, name: str):
        self.name = name
        self.requirement: Requirement = None

    def set(self, requirement: Requirement):
        self.requirement = requirement

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)
