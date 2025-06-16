from __future__ import annotations

import base64
import json
from datetime import datetime
from io import StringIO

import numpy as np
import pandas as pd

from besser.agent.core.message import MessageType, Message
from besser.agent.exceptions.logger import logger
from besser.agent.platforms.payload import PayloadAction, Payload
from besser.agent.platforms.websocket.streamlit_ui.session_management import get_streamlit_session
from besser.agent.platforms.websocket.streamlit_ui.vars import QUEUE

try:
    import cv2
except ImportError:
    logger.warning("cv2 dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")
try:
    import plotly
except ImportError:
    logger.warning("plotly dependencies in websocket_callbacks.py could not be imported. You can install them from "
                   "the requirements/requirements-extras.txt file")

def on_message(ws, payload_str):
    # https://github.com/streamlit/streamlit/issues/2838
    streamlit_session = get_streamlit_session()
    payload: Payload = Payload.decode(payload_str)
    content = None
    if payload.action == PayloadAction.AGENT_REPLY_STR.value:
        content = payload.message
        t = MessageType.STR
    elif payload.action == PayloadAction.AGENT_REPLY_MARKDOWN.value:
        content = payload.message
        t = MessageType.MARKDOWN
    elif payload.action == PayloadAction.AGENT_REPLY_HTML.value:
        content = payload.message
        t = MessageType.HTML
    elif payload.action == PayloadAction.AGENT_REPLY_FILE.value:
        content = payload.message
        t = MessageType.FILE
    elif payload.action == PayloadAction.AGENT_REPLY_AUDIO.value:
        # Encode the string back to bytes (using utf-8 or ascii)
        base64_bytes = payload.message['audio_data_base64'].encode('utf-8')
        # Decode the Base64 bytes to get the original raw audio bytes
        audio_bytes = base64.b64decode(base64_bytes)
        # Convert the raw bytes back to a NumPy array using np.frombuffer
        reconstructed_array_flat = np.frombuffer(audio_bytes, dtype=np.dtype(payload.message['metadata']['dtype']))
        # Verify size consistency
        shape = payload.message['metadata']['shape']
        expected_size = np.prod(shape)
        if reconstructed_array_flat.size != expected_size:
            logger.error(f"Decoded data size ({reconstructed_array_flat.size}) does not match expected size from shape " 
                f"{shape} ({expected_size}). Check dtype and shape.")
            logger.error(f"Error during decoding")
            logger.error("Ensure the provided dtype and shape match the original array used for encoding.")
            return
        # Reshape the flat array back to its original shape
        reconstructed_array = reconstructed_array_flat.reshape(shape)
        # recreate original dictionary
        tts_dict = {
            "audio": reconstructed_array,
            "sampling_rate": payload.message['metadata']['sample_rate']
        }
        content = tts_dict
        t = MessageType.AUDIO
    elif payload.action == PayloadAction.AGENT_REPLY_IMAGE.value:
        decoded_data = base64.b64decode(payload.message)  # Decode base64 back to bytes
        np_data = np.frombuffer(decoded_data, np.uint8)  # Convert bytes to numpy array
        img = cv2.imdecode(np_data, cv2.IMREAD_COLOR)  # Decode numpy array back to image
        content = img
        t = MessageType.IMAGE
    elif payload.action == PayloadAction.AGENT_REPLY_DF.value:
        content = pd.read_json(StringIO(payload.message))
        t = MessageType.DATAFRAME
    elif payload.action == PayloadAction.AGENT_REPLY_PLOTLY.value:
        content = plotly.io.from_json(payload.message)
        t = MessageType.PLOTLY
    elif payload.action == PayloadAction.AGENT_REPLY_LOCATION.value:
        content = {
            'latitude': [payload.message['latitude']],
            'longitude': [payload.message['longitude']]
        }
        t = MessageType.LOCATION
    elif payload.action == PayloadAction.AGENT_REPLY_OPTIONS.value:
        t = MessageType.OPTIONS
        d = json.loads(payload.message)
        content = []
        for button in d.values():
            content.append(button)
    elif payload.action == PayloadAction.AGENT_REPLY_RAG.value:
        t = MessageType.RAG_ANSWER
        content = payload.message
    if content is not None:
        message = Message(t=t, content=content, is_user=False, timestamp=datetime.now())
        streamlit_session._session_state[QUEUE].put(message)

    streamlit_session._handle_rerun_script_request()


def on_error(ws, error):
    pass


def on_open(ws):
    pass


def on_close(ws, close_status_code, close_msg):
    pass


def on_ping(ws, data):
    pass


def on_pong(ws, data):
    pass