from __future__ import annotations

from typing import TYPE_CHECKING

import io

from besser.agent import nlp
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.text2speech.text2speech import Text2Speech

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.nlp_engine import NLPEngine


try:
    import soundfile as sf
except ImportError:
    logger.warning("soundfile dependencies in OpenAIText2Speech could not be imported. You can install them from "
                   "the requirements/requirements-extra.txt file")

try:
    from transformers import logging
    logging.set_verbosity_error()
except ImportError:
    logger.warning("transformers dependencies in OpenAIText2Speech could not be imported. You can install them from "
                   "the requirements/requirements-llms.txt file")

try:
    from openai import OpenAI, APIError
except ImportError:
    logger.warning(
        "OpenAI dependencies in OpenAIText2Speech could not be imported. You can install them from "
        "the requirements/requirements-llms.txt file")


class OpenAIText2Speech(Text2Speech):
    """An OpenAI Text2Speech.

    Implements the OpenAI Create Speech API.

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent

    Attributes:
        _model_name (str): The Hugging Face model name
        _voice (str): The voice to use when generating the audio
    """
    def __init__(self, agent: 'Agent', model_name: str, voice: str = "alloy", language: str = None):
        super().__init__(agent, language=language)
        self._model_name = model_name
        self._voice = voice
        self._sampling_rate: int = 24000
        self._api_key = self._nlp_engine.get_property(nlp.OPENAI_API_KEY)

    def text2speech(self, text: str) -> dict:
        client = OpenAI(
            api_key=self._api_key
        )
        try:
            # Make the standard API call (without with_streaming_response)
            response = client.audio.speech.create(
                model=self._model_name,
                voice=self._voice,
                input=text,
                # optionally specify response_format, e.g., 'mp3', 'opus', 'aac', 'flac'
                response_format="wav" # Default is mp3
            )
            # Access the raw audio bytes directly from the response content
            audio_bytes = response.content
            # --- Decoding using soundfile ---
            # Wrap the bytes in a BytesIO object to make it file-like
            audio_io = io.BytesIO(audio_bytes)
            # Read the audio data using soundfile
            # It returns the data as a NumPy array and the sample rate
            # dtype='float32' gives samples between -1.0 and 1.0 (common for processing)
            # dtype='int16' gives 16-bit integer samples
            audio_array, sample_rate = sf.read(audio_io, dtype='float32')
            tts = {
                'audio': audio_array,
                'sampling_rate': sample_rate
            }
        except APIError as e:
            logger.error(f"An API error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        return tts


