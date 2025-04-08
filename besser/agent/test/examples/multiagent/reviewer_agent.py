# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import logging

from besser.agent.core.agent import Agent
from besser.agent.library.transition.events.base_events import ReceiveTextEvent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.llm.llm_openai_api import LLMOpenAI
from besser.agent.platforms.websocket import WEBSOCKET_PORT

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('reviewer_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('../config.ini')
agent.set_property(WEBSOCKET_PORT, 8012)
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
code_review_state = agent.new_state('code_review_state')

# INTENTS

issues_intent = agent.new_intent('new_function_intent', [
    'issues'
])

ok_intent = agent.new_intent('yes_intent', [
    'ok',
])


# STATES BODIES' DEFINITION + TRANSITIONS

initial_state.when_event(ReceiveTextEvent()) \
             .with_condition(lambda session: not session.event.human) \
             .go_to(code_review_state)


def code_review_body(session: Session):
    code: str = session.event.message
    answer: str = gpt.predict(
        message=f"You are a code reviewer. Given the following code, try to find if there are syntax errors.\n"
                f"If you think there are no errors, just reply 'ok'.\n\n"
                f"{code}"
    )
    websocket_platform.reply(session, answer)


code_review_state.set_body(code_review_body)
code_review_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
