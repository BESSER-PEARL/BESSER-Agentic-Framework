from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.nlp_engine import NLPEngine


class Speech2Text(ABC):
    """The Speech2Text abstract class.

    The Speech2Text component, also known as STT, Automatic Speech Recognition or ASR, is in charge of converting spoken
    language or audio speech signals into written text. This task is called transcribing.

    We can use it in an agent to allow the users to send voice messages and transcribe them to written text so the agent
    can process them like regular text messages.

    Args:
        agent (Agent): The Agent the Speech2Text system belongs to
        language (str): The user language for the Speech2Text system

    Attributes:
        _nlp_engine (): The NLPEngine that handles the NLP processes of the agent
    """

    def __init__(self, agent: 'Agent', language: str = None):
        self._nlp_engine: 'NLPEngine' = agent.nlp_engine
        if language is None:
            # if no language is specified, we assume English 
            # if en is already set, we do not overwrite it
            if "en" not in self._nlp_engine._language_to_speech2text_module:
                self._nlp_engine._language_to_speech2text_module["en"] = self
        else:
            self._nlp_engine._language_to_speech2text_module[language] = self

    @abstractmethod
    def speech2text(self, speech: bytes) -> str:
        """Transcribe a voice audio into its corresponding text representation.

        Args:
            speech (bytes): the recorded voice that wants to be transcribed

        Returns:
            str: the speech transcription
        """
        pass
