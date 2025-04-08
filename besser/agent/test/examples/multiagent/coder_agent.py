# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import logging

from besser.agent.core.agent import Agent
from besser.agent.library.transition.events.base_events import ReceiveJSONEvent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from besser.agent.platforms.websocket import WEBSOCKET_PORT

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('coder_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('../config.ini')
agent.set_property(WEBSOCKET_PORT, 8011)
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=False)

# Create the LLM
gpt = LLMOpenAI(
    agent=agent,
    name='gpt-4o-mini',
    parameters={},
    num_previous_messages=10
)

# STATES

initial_state = agent.new_state('initial_state', initial=True)
generate_code_state = agent.new_state('generate_code_state')
update_code_state = agent.new_state('update_code_state')
reply_code_state = agent.new_state('reply_code_state')

# INTENTS

ok_intent = agent.new_intent('yes_intent', [
    'ok',
])

# STATES BODIES' DEFINITION + TRANSITIONS

initial_state.when_event(ReceiveJSONEvent()) \
             .with_condition(lambda session: not session.event.human) \
             .go_to(generate_code_state)


def generate_code_body(session: Session):
    message = session.event.message
    new_code: str = gpt.predict(
        message=f"Given the following code:\n\n"
                f"{message['code']}\n\n"
                f"{message['request']}\n\n"
                f"Return only the code (full code with the additions)."
        )
    session.set('new_code', new_code)
    session.send_message_to_websocket(
        url='ws://localhost:8012',
        message=new_code
    )


generate_code_state.set_body(generate_code_body)
generate_code_state.when_intent_matched(ok_intent).go_to(reply_code_state)
# TODO : fix no_intent_matched
generate_code_state.when_no_intent_matched().got_to(update_code_state)


def update_code_body(session: Session):
    issues: str = session.event.message
    new_code: str = gpt.predict(
        message=f'Given the following code:\n\n'
                f'{session.get("new_code")}\n\n'
                f'Update it with the following requirements/fixing these issues (just reply with the new code):\n\n'
                f'{issues}'
    )
    session.set('new_code', new_code)
    session.send_message_to_websocket(
        url='ws://localhost:8012',
        message=new_code

    )


update_code_state.set_body(update_code_body)
update_code_state.when_intent_matched(ok_intent).go_to(reply_code_state)
# TODO : fix no_intent_matched
update_code_state.when_no_intent_matched().go_to(update_code_state)


def reply_code_body(session: Session):
    websocket_platform.reply(session, session.get('new_code'))


reply_code_state.set_body(reply_code_body)
reply_code_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
