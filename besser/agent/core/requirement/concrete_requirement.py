from typing import Any

from besser.agent.core.attribute import Attribute
from besser.agent.core.entity.image.concrete_entity import ConcreteEntity
from besser.agent.core.requirement.simple_requirement import SimpleRequirement
from besser.agent.core.session import Session
from besser.agent.cv.prediction.image_prediction import ImageObjectPrediction


class ConcreteEntityAttribute(Attribute):

    dictionary = {
        'score': float,
        'min': int,
        'max': int,
    }

    def __init__(self, name: str, value: Any):
        if name not in ConcreteEntityAttribute.dictionary:
            raise ValueError(
                f"'{name}' is not a valid ConcreteEntityAttribute. Allowed attributes are:\n{ConcreteEntityAttribute.dictionary}")
        if ConcreteEntityAttribute.dictionary[name] != type(value):
            raise ValueError(
                f"'{name}' ConcreteEntityAttribute must be of type '{ConcreteEntityAttribute.dictionary[name]}',not '{value}'")
        super().__init__(name, value)


class ConcreteRequirement(SimpleRequirement):

    def __init__(
            self,
            name: str,
            concrete_entity: ConcreteEntity,
            attributes: dict[str, Any]
    ):

        super().__init__(name, attributes['score'])
        self.concrete_entity: ConcreteEntity = concrete_entity
        self.attributes: list[ConcreteEntityAttribute] = []
        for attr_name, attr_value in attributes.items():
            self.attributes.append(ConcreteEntityAttribute(attr_name, attr_value))
        if 'min' not in [attribute.name for attribute in self.attributes]:
            self.attributes.append(ConcreteEntityAttribute('min', 1))
        if 'max' not in [attribute.name for attribute in self.attributes]:
            self.attributes.append(ConcreteEntityAttribute('max', 0))
        min = self.get_attribute_value('min')
        max = self.get_attribute_value('max')
        if min < 1:
            raise ValueError(f'Error creating {self.name}: min must be > 0')
        if min > max and max != 0:
            raise ValueError(f'Error creating {self.name}: min must <= max (unless max = 0)')

    def get_attribute_value(self, name: str) -> Any:
        for attribute in self.attributes:
            if attribute.name == name:
                return attribute.value
        return None

    def evaluate(self, session: Session):
        if session.image_prediction is None:
            return False
        _min = self.get_attribute_value('min')
        _max = self.get_attribute_value('max')
        score = self.get_attribute_value('score')
        image_object_predictions: list[ImageObjectPrediction] = session.image_prediction.image_object_predictions
        filtered_image_object_predictions = [
            image_object_prediction for image_object_prediction in image_object_predictions
            if image_object_prediction.concrete_entity == self.concrete_entity and image_object_prediction.score >= score
        ]
        num_predictions = len(filtered_image_object_predictions)
        if num_predictions == 0:
            return False
        if _max == 0 and num_predictions >= _min:
            return True
        if _min <= num_predictions <= _max:
            return True
        return False
