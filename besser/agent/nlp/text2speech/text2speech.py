from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.nlp_engine import NLPEngine


class Text2Speech(ABC):
    """The Text2Speech abstract class.

    The Text2Speech component, also known as TTS or speech synthesis, is in charge of converting written text into
    audio speech signals. This task is called synthesizing or speech synthesis.

    We can use it in an agent to allow the users to send text messages and synthesize them to audio speech
    signals like regular spoken language

    Args:
        agent (Agent): The Agent the Text2Speech system belongs to
        language (str): The user language for the Text2Speech system

    Attributes:
        _nlp_engine (): The NLPEngine that handles the NLP processes of the agent
    """

    def __init__(self, agent: "Agent", language: str = None):
        self._nlp_engine: "NLPEngine" = agent.nlp_engine
        if language is None:
            # if no language is specified, we assume English
            # if en is already set, we do not overwrite it
            if "en" not in self._nlp_engine._language_to_text2speech_module:
                self._nlp_engine._language_to_text2speech_module["en"] = self
        else:
            self._nlp_engine._language_to_text2speech_module[language] = self

    @abstractmethod
    def text2speech(self, text: str) -> dict:
        """Synthesize a text into its corresponding audio speech signal.

        Args:
            text (str): the text that wants to be synthesized

        Returns:
            dict: the speech synthesis as a dictionary containing 2 keys:
                audio (np.ndarray): the generated audio waveform as a numpy array with dimensions (nb_channels, audio_length),
                    where nb_channels is the number of audio channels (usually 1 for mono) and audio_length is the number
                    of samples in the audio
                sampling_rate (int): an integer value containing the sampling rate, e.g. how many samples correspond to
                    one second of audio
        """
        pass
