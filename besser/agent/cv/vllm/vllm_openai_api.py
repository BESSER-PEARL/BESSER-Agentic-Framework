import base64
import json

import cv2
import numpy as np
from openai import OpenAI

from besser.agent import nlp
from besser.agent.core.agent import Agent
from besser.agent.cv.prediction.image_prediction import ImagePropertyPrediction
from besser.agent.cv.vllm.vllm import VLLM


class VLLMOpenAI(VLLM):

    def __init__(self, agent: 'Agent', name: str, parameters: dict):
        super().__init__(agent.cv_engine, name, parameters)
        self.client: OpenAI = None

    def initialize(self) -> None:
        self.client = OpenAI(api_key=self._cv_engine._agent.get_property(nlp.OPENAI_API_KEY))

    def predict(self, message: str, img: np.ndarray, parameters: dict = None) -> str:
        retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
        base64_img = base64.b64encode(buffer).decode('utf-8')
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": message
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}",
                        "detail": "low"
                    },
                },
            ],
        }]
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=messages,
            **parameters,
        )
        return response.choices[0].message.content

    def predict_image_properties(self, img: np.ndarray, parameters: dict = None) -> list[ImagePropertyPrediction]:
        retval, buffer = cv2.imencode('.jpg', img)  # Encode as JPEG
        base64_img = base64.b64encode(buffer).decode('utf-8')
        # TODO: Make the prompt to be an argument
        prompt = "Analyze the following image and return a JSON containing a key for each of the following property " \
                 "names and a float value between 0 and 1 indicating the score or probability of that property to be" \
                 "satisfied in the image (some properties may provide a description).\n"
        for abstract_entity in self._cv_engine._agent.abstract_entities:
            image_property_string = f"- {abstract_entity.name}"
            if abstract_entity.has_attribute('description'):
                image_property_string += f": {abstract_entity.get_attribute_value('description')}"
            prompt += image_property_string + "\n"
        messages = [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_img}",
                        "detail": "low"
                    },
                },
            ],
        }]
        if not parameters:
            parameters = self.parameters
        response = self.client.chat.completions.create(
            model=self.name,
            messages=messages,
            response_format={"type": "json_object"},
            **parameters,
        )
        response_json = json.loads(response.choices[0].message.content)
        return self.default_json_to_image_property_predictions(response_json=response_json)