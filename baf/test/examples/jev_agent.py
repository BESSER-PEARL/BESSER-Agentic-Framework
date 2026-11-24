# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging

from baf.core.agent import Agent
from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.nlp.intent_classifier.intent_classifier_configuration import JevIntentClassifierConfiguration
from baf.nlp.jev.jev import Jev, Noul, Choice, Score

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('jev_agent')
# Load agent properties stored in a dedicated file (set nlp.typesafe.api_key)
agent.load_properties('config.yaml')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# Create the Jev client (TypeSafe AI). Pin a version (e.g. 'jev-1.13.0') if you tune thresholds on its probabilities
jev = Jev(agent=agent, model='jev-latest')

# Jev classifies the intents of every state, with calibrated probabilities
agent.set_default_ic_config(JevIntentClassifierConfiguration(
    use_intent_descriptions=True,
    use_training_sentences=True,
    none_option=True
))

# STATES

initial_state = agent.new_state('initial_state', initial=True)
ticket_state = agent.new_state('ticket_state')

# INTENTS

hello_intent = agent.new_intent(
    name='hello_intent',
    training_sentences=['hi', 'hello'],
    description='The user greets you'
)

support_intent = agent.new_intent(
    name='support_intent',
    training_sentences=['I was charged twice', 'the app crashes when I log in'],
    description='The user reports a problem or asks for help with an order, a payment or the app'
)


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Hi! Tell me about your problem and I will route your ticket.')


initial_state.set_body(initial_body)
initial_state.when_intent_matched(hello_intent).go_to(initial_state)
initial_state.when_intent_matched(support_intent).go_to(ticket_state)


def ticket_body(session: Session):
    # Ask Jev several typed questions about the same message in one request
    response = jev.ask(session.event.message, {
        'refund': Noul('Does the message ask for a refund?'),
        'department': Choice('Which department should handle this ticket?', {
            'billing': 'Payments, invoices, refunds',
            'technical': 'Bugs, crashes, login problems',
            'sales': 'Prices, plans, new purchases',
        }),
        'urgency': Score('How urgent is this ticket?', [
            'Can wait a week',
            'Needs an answer this week',
            'Needs an answer today',
        ]),
    })
    department = response['department']
    urgency = response['urgency']
    if department.confidence is not None and department.confidence < 0.5:
        session.reply('I am not sure which team should handle this. A human will take a look.')
    else:
        session.reply(f'Routing your ticket to {department.choice} '
                      f'(urgency: {urgency.legend[round(urgency.score)]}).')
    if response['refund'].noul > 0.8:
        session.reply('I see you want a refund. The billing team will contact you.')


ticket_state.set_body(ticket_body)
ticket_state.go_to(initial_state)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
