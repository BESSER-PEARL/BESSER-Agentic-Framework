from typing import Any

from besser.agent.core.attribute import Attribute
from besser.agent.core.entity.image.abstract_entity import AbstractEntity
from besser.agent.core.requirement.simple_requirement import SimpleRequirement
from besser.agent.core.session import Session
from besser.agent.cv.prediction.image_prediction import ImagePropertyPrediction


class AbstractRequirementAttribute(Attribute):

    dictionary = {
        'confidence': float,
    }

    def __init__(self, name: str, value: Any):
        if name not in AbstractRequirementAttribute.dictionary:
            raise ValueError(f"'{name}' is not a valid AbstractRequirementAttribute. Allowed attributes are:\n{AbstractRequirementAttribute.dictionary}")
        if AbstractRequirementAttribute.dictionary[name] != type(value):
            raise ValueError(f"'{name}' AbstractRequirementAttribute must be of type '{AbstractRequirementAttribute.dictionary[name]}',not '{value}'")
        super().__init__(name, value)


class AbstractRequirement(SimpleRequirement):

    def __init__(
            self,
            name: str,
            abstract_entity: AbstractEntity,
            attributes: dict[str, Any]
    ):

        super().__init__(name, attributes['confidence'])
        self.abstract_entity: AbstractEntity = abstract_entity
        self.attributes: list[AbstractRequirementAttribute] = []
        for attr_name, attr_value in attributes.items():
            self.attributes.append(AbstractRequirementAttribute(attr_name, attr_value))

    def get_attribute_value(self, name: str) -> Any:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute.value
        return None

    def evaluate(self, session: Session):
        if session.image_prediction is None:
            return False
        image_property_predictions: list[ImagePropertyPrediction] = session.image_prediction.image_property_predictions
        confidence = self.get_attribute_value('confidence')
        for image_property_prediction in image_property_predictions:
            if image_property_prediction.abstract_entity == self.abstract_entity and image_property_prediction.score >= confidence:
                return True
        return False
