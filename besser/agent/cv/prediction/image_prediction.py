import datetime
import json

import numpy as np

from besser.agent.core.entity.image.abstract_entity import AbstractEntity
from besser.agent.core.entity.image.concrete_entity import ConcreteEntity


class ImageObjectPrediction:
    """The prediction result of an ObjectDetector for a specific ConcreteEntity.

    Args:
        concrete_entity (ConcreteEntity): the concrete image entity that was detected by an ObjectDetector
        score (float): the prediction score (between 0 and 1)
        model_name (str): the name of the model that made the object detection
        x1 (int): the x1 coordinate of the object's bounding box
        y1 (int): the y1 coordinate of the object's bounding box
        x2 (int): the x2 coordinate of the object's bounding box
        y2 (int): the y2 coordinate of the object's bounding box

    Attributes:
        concrete_entity (ConcreteEntity): the concrete image entity that was detected by an ObjectDetector
        score (float): the prediction score (between 0 and 1)
        model_name (str): the name of the model that made the object detection
        x1 (int): the x1 coordinate of the object's bounding box
        y1 (int): the y1 coordinate of the object's bounding box
        x2 (int): the x2 coordinate of the object's bounding box
        y2 (int): the y2 coordinate of the object's bounding box
    """

    def __init__(self, concrete_entity: ConcreteEntity, score: float, model_name: str, x1: int, y1: int, x2: int, y2: int):
        self.concrete_entity: ConcreteEntity = concrete_entity
        self.score: float = score
        self.model_name: str = model_name
        self.x1: int = x1
        self.y1: int = y1
        self.x2: int = x2
        self.y2: int = y2


class ImagePropertyPrediction:

    def __init__(self, abstract_entity: AbstractEntity, score: float):
        self.abstract_entity: AbstractEntity = abstract_entity
        self.score: float = score


class ImagePrediction:
    """The prediction result of the CVEngine processes for a specific image.

    Args:
        img (np.ndarray): the image on which the image prediction was done
        image_object_predictions (list[ImageObjectPrediction]): the list of predicted objects within the image
        image_property_predictions (list[ImagePropertyPrediction]): the list of predicted properties within the image
        timestamp (datetime.datetime): the time at which the prediction was done
        image_input_name (str): the name of the image input source

    Attributes:
        img (np.ndarray): the image on which the image prediction was done
        image_object_predictions (list[ImageObjectPrediction]): the list of predicted objects within the image
        image_property_predictions (list[ImagePropertyPrediction]): the list of predicted properties within the image
        timestamp (datetime.datetime): the time at which the prediction was done
        image_input_name (str): the name of the image input source
    """
    def __init__(
            self,
            img: np.ndarray,
            image_object_predictions: list[ImageObjectPrediction],
            image_property_predictions: list[ImagePropertyPrediction],
            timestamp: datetime.datetime,
            image_input_name: str

    ):
        self.img: np.ndarray = img
        self.image_object_predictions: list[ImageObjectPrediction] = image_object_predictions
        self.image_property_predictions: list[ImagePropertyPrediction] = image_property_predictions
        self.timestamp: datetime.datetime = timestamp
        self.image_input_name: str = image_input_name

    def get_image_object_predictions(self, name: str) -> list[ImageObjectPrediction]:
        """Get all the image object predictions with a specific image object name.

        Args:
            name (str): the name of the image objects to get

        Returns:
            list[ImageObjectPrediction]: the image object predictions whose image object's name matches with the
            provided name
        """
        image_object_predictions: list[ImageObjectPrediction] = []
        for image_object_prediction in self.image_object_predictions:
            if image_object_prediction.concrete_entity.name == name:
                image_object_predictions.append(image_object_prediction)
        return image_object_predictions


class ImagePredictionEncoder(json.JSONEncoder):
    """Encoder for the :class:`ImagePrediction` class.

    Example:
        .. code::

            import json
            encoded_image_prediction = json.dumps(image_prediction, cls=ImagePredictionEncoder)
    """

    def default(self, obj):
        """Returns a serializable object for a :class:`ImagePrediction`

        Args:
            obj: the object to serialize

        Returns:
            dict: the serialized image prediction
        """
        if isinstance(obj, ImagePrediction):
            # Convert the ImagePrediction object to a dictionary
            image_prediction_dict = {
                # 'img': obj.img.tolist(),
                'image_object_predictions': [],
                'image_property_predictions': []
            }
            for image_object_prediction in obj.image_object_predictions:
                image_prediction_dict['image_object_predictions'].append({
                    'name': image_object_prediction.concrete_entity.name,
                    'score': image_object_prediction.score,
                    'x1': image_object_prediction.x1,
                    'x2': image_object_prediction.x2,
                    'y1': image_object_prediction.y1,
                    'y2': image_object_prediction.y2,
                })
            for image_property_prediction in obj.image_property_predictions:
                image_prediction_dict['image_property_predictions'].append({
                    'name': image_property_prediction.abstract_entity.name,
                    'score': image_property_prediction.score
                })
            return image_prediction_dict
        return super().default(obj)
