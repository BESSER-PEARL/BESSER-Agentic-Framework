from __future__ import annotations

import regex as re
import requests

from typing import TYPE_CHECKING

from besser.agent import nlp
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.speech2text.speech2text import Speech2Text

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.nlp_engine import NLPEngine


class LuxASRSpeech2Text(Speech2Text):
    """Makes use of the LuxASR API (Note: This only works with Luxembourgish speech)

    It calls the LuxASR API provided by the University of Luxembourg: https://luxasr.uni.lu/

    Args:
        nlp_engine (NLPEngine): the NLPEngine that handles the NLP processes of the agent
    """

    def __init__(self, agent: 'Agent', language: str = None):
        super().__init__(agent, language=language)
        # these should be parameters of the constructor, but for now we set them to default values
        self._diarization = 'Enabled'  # Default diarization setting
        self._output_format = 'text'  # Default output format
        self._mime_type = 'application/octet-stream'

    def speech2text(self, speech: bytes) -> str:
        url = f"https://luxasr.uni.lu/v2/asr?diarization={self._diarization}&outfmt={self._output_format}"
        headers = {
            "accept": "application/json"
        }
        # Set MIME type
        mime_type = self._mime_type
        files = {
            "audio_file": ("recorded_speech", speech, mime_type)
        }
        response = requests.post(url, headers=headers, files=files)

        # Given that the text is returned in the following format: "User: \"[00.03-02.17] SPEAKER_00: M\u00e4in Numm ass Julian.\""
        # we need to extract just the text
        # Find all text after "SPEAKER_XX: "
        pattern = r'SPEAKER_\d+:\s*(.+?)(?=\s*SPEAKER_\d+:|$)'
        matches = re.findall(pattern, response.text, re.DOTALL)

        spoken_texts = []
        for match in matches:
            # Clean timestamps and quotes from the match
            cleaned = re.sub(r'\[[\d\.-]+\]', '', match)
            cleaned = cleaned.strip().strip('"\'')
            # Decode Unicode escape sequences
            try:
                cleaned = cleaned.encode().decode('unicode_escape')
            except UnicodeDecodeError:
                # If decoding fails, keep original text
                pass
            if cleaned:
                spoken_texts.append(cleaned)

        # Join all text segments with a space
        return " ".join(spoken_texts)