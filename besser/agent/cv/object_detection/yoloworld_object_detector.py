import math
from typing import TYPE_CHECKING

import numpy as np
from ultralytics import YOLOWorld
from ultralytics.engine.results import Results

from besser.agent.core.image.image_entity import ImageEntity
from besser.agent.cv.prediction.image_prediction import ImageObjectPrediction
from besser.agent.cv.object_detection.object_detector import ObjectDetector

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class YOLOWorldObjectDetector(ObjectDetector):
    """The YOLOWorld Object Detector.

    YOLOWorld is an open-vocabulary vision model that allows zero-shot object detection.

    Args:
        agent (Agent): the agent the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters

    Attributes:
        _cv_engine (CVEngine): the CVEngine that handles the CV processes of the agent the Object Detector belongs to
        name (str): the Object Detector name
        parameters (dict): the Object Detector parameters
        yolo (YOLOWorld): the YOLOWorld object detection model
    """

    def __init__(self, agent: 'Agent', name: str, model_path: str, parameters: dict = {}):
        super().__init__(agent.cv_engine, name, parameters)
        self.yolo: YOLOWorld = YOLOWorld(model_path)
        if 'classes' in parameters:
            self.yolo.set_classes(parameters['classes'])

    def set_classes(self, classes: list[str]):
        self.yolo.set_classes(classes)

    def initialize(self) -> None:
        pass

    def train(self) -> None:
        pass

    def predict(self, img: np.ndarray) -> list[ImageObjectPrediction]:
        results: list[Results] = self.yolo(img, stream=False, verbose=False)
        image_object_predictions: list[ImageObjectPrediction] = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                score = math.ceil((box.conf[0] * 100)) / 100
                cls = box.cls[0]
                name = self.yolo.names[int(cls)]
                image_entity: ImageEntity = self._cv_engine._agent.get_image_entity(name)
                if image_entity:
                    image_object_prediction: ImageObjectPrediction = ImageObjectPrediction(
                        image_entity=image_entity,
                        score=score,
                        model_name=self.name,
                        x1=x1, y1=y1, x2=x2, y2=y2
                    )
                    image_object_predictions.append(image_object_prediction)
        return image_object_predictions
