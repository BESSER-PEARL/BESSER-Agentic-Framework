from abc import ABC


class Entity(ABC):

    def __init__(self, name: str):
        self.name: str = name

    def __eq__(self, other):
        if type(other) is type(self):
            return self.name == other.name
        else:
            return False

    def __hash__(self):
        return hash(self.name)
