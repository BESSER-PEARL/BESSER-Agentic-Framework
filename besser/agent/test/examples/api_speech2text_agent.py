# Besser Agentic Framework Google SR Speech-to-text example agent

# imports
import logging
import base64

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent import nlp

from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI

from besser.agent.nlp.speech2text.api_speech2text import APISpeech2Text
from besser.agent.nlp.nlp_engine import NLPEngine

from besser.agent.core.file import File
from besser.agent.library.transition.events.base_events import ReceiveFileEvent


# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('Google Speech-to-Text Agent')

# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# set agent properties (or define them in the config file)

# other models
#agent.set_property(nlp.NLP_STT_HF_MODEL, 'openai/whisper-tiny')
agent.set_property(nlp.NLP_STT_SR_ENGINE, 'Google Speech Recognition')

# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# Define NLP Engine
eng = NLPEngine(agent)

# LuxASR SpeechToText
stt = APISpeech2Text(eng)

# Create the LLM
gpt = LLMOpenAI(
    agent=agent,
    name='gpt-4o-mini',
    parameters={},
    num_previous_messages=10,
    #global_context='You only answer and speak Luxembourgish.'
)

# States
initial_state = agent.new_state('initial_state', initial=True)
stt_state = agent.new_state('stt_state')  # for messages and speech
stt_file_state = agent.new_state('stt_file_state')  # for audio files uploaded through the UI


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Moien, so w.e.g. eppes!')


initial_state.set_body(initial_body)
initial_state.when_file_received(allowed_types=("audio/wav", "audio/mpeg", "audio/mp4")).go_to(
    stt_file_state)  # Only Allow Wav, MP3, MP4 files
initial_state.when_no_intent_matched().go_to(stt_state)


def stt_body(session: Session):
    session.reply("User: " + session.event.message)
    answer = gpt.predict(session.event.message)
    session.reply(answer)


stt_state.set_body(stt_body)
stt_state.go_to(initial_state)


# Execute when a file is received
def stt_file_body(session: Session):
    event: ReceiveFileEvent = session.event
    file: File = event.file

    # convert file to byte representation
    base64_content = file._base64
    # Decode the base64 string into bytes
    file_bytes = base64.b64decode(base64_content)
    # add to logger
    logger.info(f"Successfully decoded {len(file_bytes)} bytes for Speech2Text.")

    # call HF Speech2Text and get transcription
    text= stt.speech2text(file_bytes)
    session.reply("User: " + text)
    answer = gpt.predict(text)
    session.reply(answer)


stt_file_state.set_body(stt_file_body)
stt_file_state.go_to(initial_state)


if __name__ == '__main__':
    agent.run()