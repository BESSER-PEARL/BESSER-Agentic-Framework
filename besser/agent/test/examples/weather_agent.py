# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging
import random

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('weather_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# STATES

s0 = agent.new_state('s0', initial=True)
weather_state = agent.new_state('weather_state')

# ENTITIES

city_entity = agent.new_entity('city_entity', entries={
    'Barcelona': ['BCN', 'barna'],
    'Madrid': [],
    'Luxembourg': ['LUX']
})

# INTENTS

weather_intent = agent.new_intent('weather_intent', [
    'what is the weather in CITY?',
    'what is the weather like in CITY?',
    'weather in CITY',
])
weather_intent.parameter('city1', 'CITY', city_entity)

# STATES BODIES' DEFINITION + TRANSITIONS


def s0_body(session: Session):
    session.reply(
        "Welcome! 👋\n"
        "I can tell you the weather in a city.\n"
        "Just type something like:\n"
        "- 'What is the weather in Barcelona?'\n"
    )


s0.set_body(s0_body)
s0.when_intent_matched(weather_intent).go_to(weather_state)


def weather_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.event.predicted_intent
    city = predicted_intent.get_parameter('city1')
    temperature = round(random.uniform(0, 30), 2)
    if city.value is None:
        session.reply("Sorry, I didn't get the city")
    else:
        session.reply(f"The weather in {city.value} is {temperature}°C")
        if temperature < 15:
            session.reply('🥶')
        else:
            session.reply('🥵')


weather_state.set_body(weather_body)
weather_state.go_to(s0)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
