# Besser Agentic Framework Luxembourgish speech-to-speech example agent (LuxASR STT and Piper TTS)

# imports
import logging
import base64
import os

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent import nlp
from besser.agent import db

from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI

from besser.agent.nlp.speech2text.luxasr_speech2text import LuxASRSpeech2Text
from besser.agent.nlp.text2speech.piper_text2speech import PiperText2Speech
from besser.agent.nlp.nlp_engine import NLPEngine

from besser.agent.core.file import File
from besser.agent.library.transition.events.base_events import ReceiveFileEvent, ReceiveMessageEvent
from besser.agent.library.transition.events.base_events import ReceiveJSONEvent

from besser.agent.db.monitoring_ui.monitoring_ui import start_ui
from besser.agent.test.examples.piper_text2speech_agent import initial_state

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('Luxembourgish Speech-to-Speech Agent')

# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# set agent properties (or define them in the config file)
agent.set_property(nlp.NLP_STT_MIME_TYPE, 'application/octet-stream')
agent.set_property(nlp.NLP_TTS_PIPER_MODEL, 'mbarnig/lb_rhasspy_piper_tts')

# More properties (optional)
#agent.set_property(nlp.NLP_STT_DIARIZATION, 'Enabled')  # set Diarization property
#agent.set_property(nlp.NLP_STT_OUT_FMT, 'text')  # set output format

# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# Run the Monitoring UI
#dirname = os.path.dirname(__file__)
#config_path = os.path.join(dirname, 'config.ini')
#start_ui(config_path, agent.get_property(db.DB_MONITORING_HOST), agent.get_property(db.DB_MONITORING_PORT))

# Define NLP Engine
eng = NLPEngine(agent)

# LuxASR SpeechToText
stt = LuxASRSpeech2Text(eng)
tts = PiperText2Speech(eng)


# Create the LLM
gpt = LLMOpenAI(
    agent=agent,
    name='gpt-4.1',
    parameters={},
    num_previous_messages=100,
    global_context='You only answer and speak Luxembourgish.'
)

# States
initial_state = agent.new_state('initial_state', initial=True)
awaiting_state = agent.new_state('awaiting_state') # for awaiting user input
sts_state = agent.new_state('sts_message_state')  # for messages and speech
sts_file_state = agent.new_state('sts_file_state')  # for audio files uploaded through the UI


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    answer = gpt.predict(
        f"You are a helpful assistant. Start the conversation with a short (2-15 words) greetings message. Make it original.")
    session.reply(answer)

initial_state.set_body(initial_body)
initial_state.go_to(awaiting_state)

def awaiting_body(session:Session):
    pass

awaiting_state.set_body(awaiting_body)
awaiting_state.when_file_received(allowed_types=("audio/wav", "audio/mpeg", "audio/mp4", "text/plain")).go_to(
    sts_file_state)  # Only Allow Wav, MP3, MP4 files
awaiting_state.when_event(ReceiveJSONEvent()).go_to(sts_state)  # when Audio is received through the UI
awaiting_state.when_no_intent_matched().go_to(sts_state)

def stt_message_body(session: Session):
    # only transcribe message if the user spoke
    if isinstance(session.event, ReceiveJSONEvent) or isinstance(session.event, ReceiveMessageEvent):
        session.reply("User: " + session.event.message)
    #session.reply("User: " + session.event.message)
    #print(session.get_chat_history(n=100)[-1].content)
    answer = gpt.chat(session)
    audio = tts.text2speech(answer)
    websocket_platform.reply_speech(session, audio)
    session.reply(answer)


sts_state.set_body(stt_message_body)
sts_state.go_to(awaiting_state)


# Execute when a file is received
def stt_file_body(session: Session):
    event: ReceiveFileEvent = session.event
    file: File = event.file

    # Determine MIME type
    ext = file.name.lower()
    # do only for text files
    if ext.endswith(".txt"):
        mime_type = "text/plain"
    elif ext.endswith(".wav"):
        mime_type = "audio/wav"
    elif ext.endswith(".mp3"):
        mime_type = "audio/mpeg"
    elif ext.endswith(".m4a"):
        mime_type = "audio/mp4"
    else:
        mime_type = "application/octet-stream"

    # only when audio files are uploaded
    if not mime_type == "text/plain":

        # set mime type property
        agent.set_property(nlp.NLP_STT_MIME_TYPE, mime_type)

        # convert file to byte representation
        base64_content = file._base64
        # Decode the base64 string into bytes
        file_bytes = base64.b64decode(base64_content)
        # add to logger
        logger.info(f"Successfully decoded {len(file_bytes)} bytes.")

        # call LuxASR Speech2Text and get transcription
        text= stt.speech2text(file_bytes)
        session.reply("User: " + text)
        answer = gpt.predict(text)
        #session.reply(answer)
        file_text = answer
    else:
        # convert file to byte representation
        base64_content = file._base64
        # Decode the base64 string into text
        file_text = base64.b64decode(base64_content).decode('utf-8')

    # call HF Speech2Text and get transcription
    audio = tts.text2speech(file_text)

    session.reply(file_text)
    websocket_platform.reply_speech(session, audio)


sts_file_state.set_body(stt_file_body)
sts_file_state.go_to(awaiting_state)


if __name__ == '__main__':
    agent.run()