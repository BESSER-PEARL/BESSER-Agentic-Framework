import io
import openai
from besser.agent import nlp
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.speech2text.speech2text import Speech2Text

class OpenAISpeech2Text(Speech2Text):
    """Speech2Text using OpenAI Whisper API."""

    def __init__(self, nlp_engine: 'NLPEngine'):
        super().__init__(nlp_engine)
        self._api_key = self._nlp_engine.get_property(nlp.OPENAI_API_KEY)
        self._model_name = self._nlp_engine.get_property(nlp.NLP_STT_OPENAI_MODEL)
        openai.api_key = self._api_key

    def speech2text(self, speech: bytes):
        try:
            audio_file = io.BytesIO(speech)
            audio_file.name = "audio.wav"  # OpenAI API expects a filename
            response = openai.audio.transcriptions.create(
                model=self._model_name,
                file=audio_file,
                response_format="text"
            )
            return response
        except Exception as e:
            logger.error(f"OpenAI Speech2Text failed: {e}")
            return ""
