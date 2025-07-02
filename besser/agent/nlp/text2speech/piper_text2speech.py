from __future__ import annotations

import numpy as np
import requests

from typing import TYPE_CHECKING

from besser.agent.exceptions.logger import logger
from besser.agent.nlp.text2speech.text2speech import Text2Speech

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.nlp_engine import NLPEngine

try:
    from transformers import logging
    logging.set_verbosity_error()
except ImportError:
    logger.warning("transformers dependencies in HFText2Speech could not be imported. You can install them from "
                   "the requirements/requirements-llms.txt file")

class PiperText2Speech(Text2Speech):
    """A Piper Text2Speech implementation.

    It loads a specific Piper model running in a Docker container to perform the Speech2Text task.
    Piper Model: https://huggingface.co/mbarnig/lb_rhasspy_piper_tts

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent

    Attributes:
        _model_name (str): The Piper model name
        _piper_api_url (str): The URL to the docker container containing the API
        _sample_rate (int): The model's actual sample rate
        _dtype (): The audio dtype
    """
    def __init__(self, agent: 'Agent', model_name: str = "mbarnig/lb_rhasspy_piper_tts", language: str = None):
        super().__init__(agent, language=language)
        self._model_name = model_name
        self._piper_api_url = "http://localhost:8000/synthesize"
        self._sample_rate = 22500  # NEEDS TO MATCH SAMPLE RATE IN main.py within the docker container
        self._dtype = np.int16  # Because the service sends audio/l16

    def text2speech(self, text: str) -> dict:
        """Sends text to the Dockerized Piper service and plays the audio."""
        try:
            payload = {"text": text}
            logger.info(f"Sending request to {self._piper_api_url}...")
            response = requests.post(self._piper_api_url, json=payload)
            response.raise_for_status()  # Check for HTTP errors (like 4xx, 5xx)

            # Check content type (optional but good practice)
            content_type = response.headers.get('content-type')
            logger.info(f"Received response with Content-Type: {content_type}")
            # Ideally, parse sample rate/channels from content_type if possible

            # Get raw audio bytes (PCM data)
            audio_bytes = response.content
            logger.info(f"Received {len(audio_bytes)} audio bytes.")

            if not audio_bytes:
                logger.info("Received empty audio response.")

            # Convert PCM bytes to NumPy array
            audio_array = np.frombuffer(audio_bytes, dtype=self._dtype)
            tts = {
                'audio': audio_array,
                'sampling_rate': self._sample_rate
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Error: Could not connect to the Piper TTS service at {self._piper_api_url}.")
            logger.error("Ensure the Docker container 'piper-service' is running.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error during API request to Piper TTS service: {e}")
            # Print response body if it contains error details
            try:
                logger.error(f"Service Response: {response.json()}")
            except:  # Handle cases where response is not JSON
                logger.error(f"Service Response (raw): {response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            # import traceback
            # traceback.print_exc() # Uncomment for detailed debugging
        return tts
