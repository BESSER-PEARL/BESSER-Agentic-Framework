from typing import Any

from besser.agent.core.attribute import Attribute
from besser.agent.core.entity.entity import Entity


class AbstractEntityAttribute(Attribute):

    dictionary = {
        'description': str,
    }

    def __init__(self, name: str, value: Any):
        if name not in AbstractEntityAttribute.dictionary:
            raise ValueError(f"'{name}' is not a valid AbstractEntityAttribute. Allowed attributes are:\n{AbstractEntityAttribute.dictionary}")
        if AbstractEntityAttribute.dictionary[name] != type(value):
            raise ValueError(f"'{name}' AbstractEntityAttribute must be of type '{AbstractEntityAttribute.dictionary[name]}',not '{value}'")
        super().__init__(name, value)


class AbstractEntity(Entity):
    """The Abstract Entity core component of an agent.

    Abstract Entities are used to specify the properties that can be detected by the agent in an image.

    Args:
        name (str): the abstract entity's name

    Attributes:
        name (str): The abstract entity's name
    """

    def __init__(self, name: str, attributes: dict[str, Any] = {}):
        super().__init__(name)
        self.attributes: list[AbstractEntityAttribute] = []
        for attr_name, attr_value in attributes.items():
            self.attributes.append(AbstractEntityAttribute(attr_name, attr_value))

    def has_attribute(self, name: str) -> bool:
        for attribute in self.attributes:
            if attribute.name == name:
                return True

    def get_attribute_value(self, name: str) -> Any:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute.value
        return None
