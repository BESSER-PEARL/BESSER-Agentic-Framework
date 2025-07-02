from __future__ import annotations

from typing import TYPE_CHECKING

from besser.agent.exceptions.logger import logger
from besser.agent.nlp.text2speech.text2speech import Text2Speech

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent

try:
    import torch
except ImportError:
    logger.warning("torch dependencies in HFText2Speech could not be imported. You can install them from "
                   "the requirements/requirements-torch.txt file")

try:
    from transformers import (logging, pipeline, VitsTokenizer, VitsModel, set_seed, SpeechT5HifiGan,
                              SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan)
    logging.set_verbosity_error()
except ImportError:
    logger.warning("transformers dependencies in HFText2Speech could not be imported. You can install them from "
                   "the requirements/requirements-llms.txt file")

class HFText2Speech(Text2Speech):
    """A Hugging Face Text2Speech.

    It loads a Speech2Text Hugging Face model to perform the Speech2Text task.


    Args:
        agent (Agent): The agent instance.
        model_name (str): The Hugging Face model name.
        language (str, optional): Language code.


    Attributes:
        _model_name (str): The Hugging Face model name
        _tts (): The Transformer Text-to-Speech Pipeline
        _tokenizer (): The Vits Tokenizer. Also supports MMS-TTS.
        _model (): The complete VITS model
    """
    def __init__(
        self,
        agent: 'Agent',
        model_name: str,
        language: str = None,
    ):

        super().__init__(agent, language=language)
        self._model_name = model_name
        #self._return_tensor = return_tensor
        # for Facebook models
        if self._model_name.startswith('facebook/') or "vits" in self._model_name:
            self._tokenizer = VitsTokenizer.from_pretrained(self._model_name)
            self._model = VitsModel.from_pretrained(self._model_name)
        else:
            self._tts = pipeline("text-to-speech", model=self._model_name)

    def text2speech(self, text: str, return_tensor: str = "pt") -> dict:
        """Synthesize a text into its corresponding audio speech signal.

        Args:
            text (str): the text that wants to be synthesized
            return_tensor (str, optional): Property for the HFText2Speech agent component. If set, will return tensors instead of list of python integers. Acceptable values are:
            'tf': Return TensorFlow tf.constant objects.
            'pt': Return PyTorch torch.Tensor objects.
            'np': Return Numpy np.ndarray objects.
            name: ``nlp.text2speech.hf.rt``
            type: ``str``
            default value: ``pt``


        Returns:
            dict: the speech synthesis as a dictionary containing 2 keys:
                audio (np.ndarray): the generated audio waveform as a numpy array with dimensions (nb_channels, audio_length),
                    where nb_channels is the number of audio channels (usually 1 for mono) and audio_length is the number
                    of samples in the audio
                sampling_rate (int): an integer value containing the sampling rate, e.g. how many samples correspond to
                    one second of audio
        """
        # TODO Improve quality of SpeechT5: https://huggingface.co/microsoft/speecht5_tts
        if self._model_name.startswith('facebook/') or "vits" in self._model_name:
            inputs = self._tokenizer(text=text, return_tensors=return_tensor)
            with torch.no_grad():
                outputs = self._model(**inputs)
            # also need to convert the torch tensor to numpy array
            waveform = outputs.waveform.detach().numpy()
            sample_rate = self._model.config.sampling_rate
            # create dictionary to pass audio tensor and sample rate
            tts = {
                'audio': waveform,
                'sampling_rate': sample_rate
            }
            return tts
        elif self._model_name.startswith('microsoft/speech'):
            speaker_embeddings = torch.zeros((1, 512))  # or load xvectors from a file
            tts = self._tts(text, forward_params={"speaker_embeddings": speaker_embeddings})  # returns dict
            return tts
        else:
            tts = self._tts(text)  # returns dict
            return tts
