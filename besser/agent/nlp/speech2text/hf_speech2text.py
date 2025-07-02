from __future__ import annotations

import io
from typing import TYPE_CHECKING

from besser.agent import nlp
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.speech2text.speech2text import Speech2Text

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent

try:
    import librosa
except ImportError:
    logger.warning(
        "librosa dependencies in HFSpeech2Text could not be imported. You can install them from "
        "the requirements/requirements-extras.txt file"
    )

try:
    from transformers import (
        AutoProcessor,
        AutoModelForCTC,
        TFAutoModelForSpeechSeq2Seq,
        logging,
        pipeline,
    )

    logging.set_verbosity_error()
except ImportError:
    logger.warning(
        "transformers dependencies in HFSpeech2Text could not be imported. You can install them from "
        "the requirements/requirements-llms.txt file"
    )


class HFSpeech2Text(Speech2Text):
    """A Hugging Face Speech2Text.

    It loads a Speech2Text Hugging Face model to perform the Speech2Text task.

    Args:
        agent (Agent): the agent instance using this Speech2Text component
        model_name (str): the Hugging Face model name to load
        load_from_pytorch (bool, optional, defaults to False): Load the model weights from a PyTorch checkpoint save file
        language (str, optional): the language to use for transcription

    Attributes:
        _from_pt (bool, optional, defaults to False):  Load the model weights from a PyTorch checkpoint save file
        (see docstring of pretrained_model_name_or_path argument).
        _model_name (str): the Hugging Face model name
        _processor (): the model text processor
        _model (): the Speech2Text model
        _sampling_rate (int): the sampling rate of audio data, it must coincide with the sampling rate used to train the
            model
        _forced_decoder_ids (list): the decoder ids
        _asr (): the transformer ASR pipeline
    """

    def __init__(
        self,
        agent: "Agent",
        model_name: str,
        load_from_pytorch: bool = False,
        language: str = None,
    ):
        super().__init__(agent, language=language)
        # TODO: IMPLEMENT CHUNK BATCHING FOR LONG AUDIO FILES
        # https://huggingface.co/docs/transformers/pipeline_tutorial
        self._from_pt: bool = load_from_pytorch
        self._model_name: str = model_name
        self._sampling_rate: int = 16000
        # Only for OpenAI Whisper Models
        if self._model_name.startswith("openai/whisper"):
            self._processor = AutoProcessor.from_pretrained(self._model_name)
            self._model = TFAutoModelForSpeechSeq2Seq.from_pretrained(
                self._model_name, from_pt=self._from_pt
            )
            # self.model.config.forced_decoder_ids = None
            self._forced_decoder_ids = self._processor.get_decoder_prompt_ids(
                language=self._nlp_engine.get_property(nlp.NLP_LANGUAGE),
                task="transcribe",
            )
        else:
            self._asr = pipeline("automatic-speech-recognition", model=self._model_name)

    def speech2text(self, speech: bytes):
        wav_stream = io.BytesIO(speech)
        # Only for OpenAI Whisper Models
        if self._model_name.startswith("openai/whisper"):
            audio, sampling_rate = librosa.load(wav_stream, sr=self._sampling_rate)
            input_features = self._processor(
                audio, sampling_rate=self._sampling_rate, return_tensors="tf"
            ).input_features
            predicted_ids = self._model.generate(
                input_features, forced_decoder_ids=self._forced_decoder_ids
            )
            transcriptions = self._processor.batch_decode(
                predicted_ids, skip_special_tokens=True
            )
            return transcriptions[0]
        else:
            audio, sampling_rate = librosa.load(wav_stream, sr=self._sampling_rate)
            transcriptions = self._asr(audio)
            return transcriptions["text"]
