from typing import TYPE_CHECKING

from besser.agent.core.processors.processor import Processor
from besser.agent.core.session import Session
from besser.agent.nlp.speech2text.hf_speech2text import HFSpeech2Text
from besser.agent.nlp.speech2text.speech2text import Speech2Text
from besser.agent.nlp.llm.llm import LLM

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


class AudioLanguageDetectionProcessor(Processor):
    """The AudioLanguageDetectionProcessor returns the spoken language in a given audio message.

    This processor leverages an LLM to predict the user's spoken language.

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
        self._speech2text: Speech2Text = HFSpeech2Text(self._nlp_engine)

    def process(self, session: Session, message: bytes) -> str:
        """Method to process a message and predict the message's language.

        The detected language will be stored as a session parameter. The key is "detected_audio_language".

        Args:
            session (Session): the current session
            message (str): the message to be processed

        Returns:
            str: the original message
        """
        # transcribe audio bytes
        message = self._speech2text.speech2text(message)

        llm: LLM = self._nlp_engine._llms[self._llm_name]

        prompt = (f"Identify the language the user is speaking in based on the following message: {message}. \n"
                  f"Only return the ISO 639 standard language code of the "
                  f"language you recognized the user is speaking in.")

        detected_lang = llm.predict(prompt, session=session)
        session.set('detected_audio_language', detected_lang)

        return message
