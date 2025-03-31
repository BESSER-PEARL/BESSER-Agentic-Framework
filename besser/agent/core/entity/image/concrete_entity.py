from typing import Any

from besser.agent.core.attribute import Attribute
from besser.agent.core.entity.entity import Entity


class ConcreteEntityAttribute(Attribute):

    dictionary = {
        'description': str,
    }

    def __init__(self, name: str, value: Any):
        if name not in ConcreteEntityAttribute.dictionary:
            raise ValueError(f"'{name}' is not a valid ConcreteEntityAttribute. Allowed attributes are:\n{ConcreteEntityAttribute.dictionary}")
        if ConcreteEntityAttribute.dictionary[name] != type(value):
            raise ValueError(f"'{name}' ConcreteEntityAttribute must be of type '{ConcreteEntityAttribute.dictionary[name]}',not '{value}'")
        super().__init__(name, value)


class ConcreteEntity(Entity):
    """The Concrete Entity core component of an agent.

    Concrete Entities are used to specify the entities that can be detected by the agent in an image.

    Args:
        name (str): the concrete entity's name

    Attributes:
        name (str): The concrete entity's name
    """

    def __init__(self, name: str, attributes: dict[str, Any] = {}):
        super().__init__(name)
        self.attributes: list[ConcreteEntityAttribute] = []
        for attr_name, attr_value in attributes.items():
            self.attributes.append(ConcreteEntityAttribute(attr_name, attr_value))

    def has_attribute(self, name: str) -> bool:
        for attribute in self.attributes:
            if attribute.name == name:
                return True

    def get_attribute_value(self, name: str) -> Any:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute.value
        return None
