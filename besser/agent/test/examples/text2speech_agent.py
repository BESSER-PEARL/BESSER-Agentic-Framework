# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

# Besser Agentic Framework Hugging Face Text-to-Speech example agent

# imports
import logging
import base64

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger

from besser.agent.nlp.text2speech.hf_text2speech import HFText2Speech

from besser.agent.core.file import File
from besser.agent.library.transition.events.base_events import ReceiveFileEvent


# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('Huggingface Text-to-Speech Agent')

# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')

# example models
# 'facebook/mms-tts-eng'
# 'microsoft/speecht5_tts'
# 'suno/bark-small'

# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

tts = HFText2Speech(agent=agent, model_name="facebook/mms-tts-eng")

# States
initial_state = agent.new_state('initial_state', initial=True)
tts_state = agent.new_state('tts_state')  # for messages
tts_file_state = agent.new_state('tts_file_state')  # for text files uploaded through the UI

# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Hi')


initial_state.set_body(initial_body)
initial_state.when_file_received(allowed_types="text/plain").go_to(tts_file_state)  # Only Allow text files
initial_state.when_no_intent_matched().go_to(tts_state)


def tts_body(session: Session):
    websocket_platform.reply_speech(session, session.event.message)


tts_state.set_body(tts_body)
tts_state.go_to(initial_state)

# Execute when a file is received
def tts_file_body(session: Session):
    event: ReceiveFileEvent = session.event
    file: File = event.file

    # convert file to byte representation
    base64_content = file._base64
    # Decode the base64 string into text
    file_text = base64.b64decode(base64_content).decode('utf-8')

    # call HF Speech2Text and get transcription
    session.reply(file_text)
    websocket_platform.reply_speech(session, file_text)


tts_file_state.set_body(tts_file_body)
tts_file_state.go_to(initial_state)


if __name__ == '__main__':
    agent.run()