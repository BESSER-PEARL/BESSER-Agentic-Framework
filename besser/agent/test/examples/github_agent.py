# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.transition.events.github_webhooks_events import StarCreated, StarDeleted

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('stargazer_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
github_platform = agent.use_github_platform()


# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
star_state = agent.new_state('star_state')
unstar_state = agent.new_state('unstar_state')


# STATES BODIES' DEFINITION + TRANSITIONS

# EVENTS

star_created_event = StarCreated()
star_deleted_event = StarDeleted()

def global_fallback_body(session: Session):
    print('Greetings from global fallback')


# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


def init_body(session: Session):
    payload = github_platform.getitem(f'/repos/USER/REPO')
    session.set('star_count', payload['stargazers_count'])


init.set_body(init_body)
init.go_to(idle)


def idle_body(session: Session):
    print(f'The repo has {session.get("star_count")} stars currently')


idle.set_body(idle_body)
idle.when_event(star_deleted_event).go_to(unstar_state)
idle.when_event(star_created_event).go_to(star_state)

# idle.when_event_go_to(github_event_matched, star_state, {'event': StarCreated()})
# idle.when_event_go_to(github_event_matched, unstar_state, {'event': StarDeleted()})


def star_body(session: Session):
    star_count = session.get('star_count')
    session.set('star_count', star_count + 1)


star_state.set_body(star_body)
star_state.go_to(idle)


def unstar_body(session: Session):
    star_count = session.get('star_count')
    session.set('star_count', star_count - 1)


unstar_state.set_body(unstar_body)
unstar_state.go_to(idle)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
