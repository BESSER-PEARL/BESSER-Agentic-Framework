from typing import TYPE_CHECKING

import io
import soundfile as sf
import numpy as np


from besser.agent.core.processors.processor import Processor
from besser.agent.core.session import Session
from besser.agent.nlp.nlp_engine import NLPEngine
from besser.agent.nlp.llm.llm import LLM

from besser.agent.exceptions.logger import logger

from besser.agent.nlp.speech2text.speech2text import Speech2Text


if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class AudioLanguageDetectionProcessor(Processor):
    """The AudioLanguageDetectionProcessor detects the spoken language in a given audio message.

    This processor uses a speech-to-text model to transcribe audio and then leverages an LLM to predict the language.
    Ideally, you use a model that is trained for language detection, such as OpenAI's GPT-4o-mini
    or anything that works well on a plethora of languages.

    Args:
        agent (Agent): The agent the processor belongs to.
        transcription_model (Speech2Text): The speech-to-text model to use for transcription.
        llm_name (str): The name of the LLM to use for language detection.

    Attributes:
        agent (Agent): The agent the processor belongs to.
        _transcription_model_name (str): The speech-to-text model to use for transcription.
        _llm_name (str): The name of the LLM used for language detection.
        _nlp_engine (NLPEngine): The NLP Engine the Agent uses.
    """

    def __init__(self, agent: "Agent", transcription_model: Speech2Text, llm_name: str):
        super().__init__(agent=agent, user_messages=True, agent_messages=False)
        self._llm_name: str = llm_name
        self._transcription_model: Speech2Text = transcription_model
        self._nlp_engine: NLPEngine = agent.nlp_engine

    def process(self, session: Session, message: bytes) -> bytes:
        """Method to process a message and predict the message's language.

        The detected language will be stored as a session parameter. The key is "user_language".

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the original message
        """
        # transcribe audio bytes
        llm: LLM = self._nlp_engine._llms.get(self._llm_name)

        try:
            raw_audio = io.BytesIO(message)

            # Convert raw bytes to NumPy array
            audio_data = np.frombuffer(raw_audio.read(), dtype=np.int16)

            # Save as WAV in memory
            wav_file = io.BytesIO()
            sf.write(
                wav_file, audio_data, samplerate=44100, format="WAV", subtype="PCM_16"
            )
            wav_file.name = "audio.wav"
            wav_file.seek(0)

            # Use the transcription model to transcribe the audio
            transcription = self._transcription_model.speech2text(wav_file.getvalue())

            prompt = (
                f"Identify the language based on the following message: {transcription}. "
                f"Only return the ISO 639-1 standard language code of the "
                f"language you recognized."
            )
            # Use the LLM to detect the language based on the transcription
            # this might not work with all LLMs
            detected_lang = llm.predict(prompt, session=session)
            
            logger.info(f"Detected language (ISO 639-1): {detected_lang}")
            
            session.set("user_language", detected_lang)
        except Exception as e:
            logger.error(f"Error during language detection: {e}")

        return message
