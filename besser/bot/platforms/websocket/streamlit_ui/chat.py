import base64
import json
import time
import uuid
from datetime import datetime

import streamlit as st

from besser.bot.core.file import File
from besser.bot.core.message import Message, MessageType
from besser.bot.platforms.payload import Payload, PayloadAction, PayloadEncoder
from besser.bot.platforms.websocket.streamlit_ui.vars import TYPING_TIME, BUTTONS, HISTORY, QUEUE, WEBSOCKET, ASSISTANT, \
    USER

user_type = {
    0: ASSISTANT,
    1: USER
}


def write_message(message: Message, stream: bool = False):
    def stream_text(text: str):
        def stream_callback():
            for word in text.split(" "):
                yield word + " "
                time.sleep(TYPING_TIME)
        return stream_callback

    with st.chat_message(user_type[message.is_user]):
        if message.type == MessageType.AUDIO:
            st.audio(message.content, format="audio/wav")

        elif message.type == MessageType.FILE:
            file: File = File.from_dict(message.content)
            file_name = file.name
            file_type = file.type
            file_data = base64.b64decode(file.base64.encode('utf-8'))
            st.download_button(label='Download ' + file_name, file_name=file_name, data=file_data, mime=file_type,
                               key=file_name + str(time.time()))

        elif message.type == MessageType.IMAGE:
            st.image(message.content)

        elif message.type == MessageType.LOCATION:
            st.map(message.content)

        elif message.type == MessageType.HTML:
            st.html(message.content)

        elif message.type == MessageType.DATAFRAME:
            st.dataframe(message.content)

        elif message.type == MessageType.PLOTLY:
            st.plotly_chart(message.content, key=uuid.uuid4())

        elif message.type == MessageType.RAG_ANSWER:
            # TODO: Add stream text
            st.write(f'🔮 {message.content["answer"]}')
            with st.expander('Details'):
                st.write(f'This answer has been generated by an LLM: **{message.content["llm_name"]}**')
                st.write(f'It received the following documents as input to come up with a relevant answer:')
                if 'docs' in message.content:
                    for i, doc in enumerate(message.content['docs']):
                        st.write(f'**Document {i + 1}/{len(message.content["docs"])}**')
                        st.write(f'- **Source:** {doc["metadata"]["source"]}')
                        st.write(f'- **Page:** {doc["metadata"]["page"]}')
                        st.write(f'- **Content:** {doc["content"]}')

        elif message.type in [MessageType.STR, MessageType.MARKDOWN]:
            if stream:
                st.write_stream(stream_text(message.content))
            else:
                st.write(message.content)


def load_chat():
    for message in st.session_state[HISTORY]:
        write_message(message, stream=False)

    while not st.session_state[QUEUE].empty():
        message = st.session_state[QUEUE].get()
        if message.type not in [MessageType.OPTIONS]:
            st.session_state[HISTORY].append(message)
        if message.type == MessageType.OPTIONS:
            st.session_state[BUTTONS] = message.content
        else:
            write_message(message, stream=True)

    if BUTTONS in st.session_state:
        buttons = st.session_state[BUTTONS]
        cols = st.columns(1)
        for i, option in enumerate(buttons):
            if cols[0].button(option):
                with st.chat_message("user"):
                    st.write(option)
                message = Message(t=MessageType.STR, content=option, is_user=True, timestamp=datetime.now())
                st.session_state.history.append(message)
                payload = Payload(action=PayloadAction.USER_MESSAGE,
                                  message=option)
                ws = st.session_state[WEBSOCKET]
                ws.send(json.dumps(payload, cls=PayloadEncoder))
                del st.session_state[BUTTONS]
                break
