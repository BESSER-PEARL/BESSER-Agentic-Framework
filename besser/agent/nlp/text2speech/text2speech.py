from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.nlp.nlp_engine import NLPEngine

class Text2Speech(ABC):
    """The Text2Speech abstract class.

        The Text2Speech component, also known as TTS or speech synthesis, is in charge of converting written text into
        audio speech signals. This task is called synthesizing or speech synthesis.

        We can use it in an agent to allow the users to send text messages and synthesize them to audio speech
        signals like regular spoken language

        Args:
            nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent

        Attributes:
            _nlp_engine (): The NLPEngine that handles the NLP processes of the agent
        """

    def __init__(self, nlp_engine: 'NLPEngine'):
        self._nlp_engine: 'NLPEngine' = nlp_engine

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
                sampling_rate (int): an integer value containing the sampling rate, eg. how many samples correspond to
                    one second of audio
        """
        pass