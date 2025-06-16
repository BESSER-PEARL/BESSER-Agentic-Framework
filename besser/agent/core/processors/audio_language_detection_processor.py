from typing import TYPE_CHECKING

from besser.agent.core.processors.processor import Processor
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from besser.agent.nlp.speech2text.hf_speech2text import HFSpeech2Text
from besser.agent.nlp.speech2text.speech2text import Speech2Text
from besser.agent.nlp.llm.llm import LLM

import openai
import io

from pydub import AudioSegment

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class AudioLanguageDetectionProcessor(Processor):
    """The AudioLanguageDetectionProcessor returns the spoken language in a given audio message.

    This processor leverages GPT 4.1 to predict the user's spoken language.

    Args:
        agent (Agent): The agent the processor belongs to
        llm_name (str): the name of the LLM to use.
        user_messages (bool): Whether the processor should be applied to user messages
        agent_messages (bool): Whether the processor should be applied to agent messages

    Attributes:
        agent (Agent): The agent the processor belongs to
        user_messages (bool): Whether the processor should be applied to user messages
        agent_messages (bool): Whether the processor should be applied to agent messages
        _llm_name (str): the name of the LLM to use.
        _nlp_engine (NLPEngine): The NLP Engine the Agent uses
        _speech2text (Speech2Text or None): The Speech-to-Text System used for transcribing the audio bytes
    """
    def __init__(self, agent: 'Agent', llm_name, user_messages: bool = False, agent_messages: bool = False):
        super().__init__(agent=agent, user_messages=user_messages, agent_messages=agent_messages)
        self._llm_name: str = llm_name
        self._nlp_engine: 'NLPEngine' = agent.nlp_engine

    def process(self, session: Session, message: bytes) -> str:
        """Method to process a message and predict the message's language.

        The detected language will be stored as a session parameter. The key is "detected_audio_language".

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the processed message
        """
        # transcribe audio bytes
        #message = self._speech2text.speech2text(message)
        print("dfdfdmf.f.m")
        #print("message: " + message)


        #print("detected lang:" + detected_lang)
        detected_lang = "lb"
        try:
            print("herehrehrh")
            client = openai.OpenAI(api_key="openaikey")

            # Let's say message is raw PCM (e.g., from microphone)
            raw_audio = io.BytesIO(message)

            # You must know the raw format (channels, sample width, framerate)
            # Here's an example: mono, 16-bit, 44.1kHz
            audio = AudioSegment(
                data=raw_audio.read(),
                sample_width=2,
                frame_rate=44100,
                channels=1
            )

            # Export as MP3 to send to OpenAI
            mp3_file = io.BytesIO()
            audio.export(mp3_file, format="mp3")
            mp3_file.name = "audio.mp3"
            mp3_file.seek(0)

            # Send to OpenAI
            # right now hardcoded to use gpt-4o-mini-transcribe, as it's one of the best and fastest models for transcribing any language
            response = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=mp3_file,
                response_format="json"
            )

            print(".,d.y.f.,")
            print("Response from OpenAI:", response)
            llm: LLM = self._nlp_engine._llms[self._llm_name]

            prompt = (f"Identify the language based on the following message: {response.text}. "
                  f"Only return the ISO 639-1 standard language code of the "
                  f"language you recognized.")

            detected_lang = llm.predict(prompt, session=session)
            logger.info(f"Detected language (ISO 639-1): {detected_lang}")
            session.set('detected_audio_language', detected_lang)
        except Exception as e:
            print(f"Error during language detection: {e}")
            detected_lang = "unknown"
            session.set('detected_audio_language', detected_lang)

        return detected_lang
