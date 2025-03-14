# TODO: Ask for organization level webhook.
# TODO: Which API Key use ?
# TODO: Creation of a GitHub Bot account


import logging

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.library.event.event_library import github_event_matched
from besser.agent.platforms.github.github_webhooks_events import StarCreated, StarDeleted

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('BESSER_stargazer_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
github_platform = agent.use_github_platform()
telegram_platform = agent.use_telegram_platform()

repos = ['BESSER-PEARL/BESSER-Agentic-Framework',
         'BESSER-PEARL/BESSER']

# STATES

init = agent.new_state('init', initial=True)
idle = agent.new_state('idle')
star_state = agent.new_state('star_state')
unstar_state = agent.new_state('unstar_state')


# STATES BODIES' DEFINITION + TRANSITIONS


def global_fallback_body(session: Session):
    print('Greetings from global fallback')


# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


def init_body(session: Session):
    for repo in repos:
        payload = github_platform.getitem(f'/repos/'+repo)
        session.set(repo, payload['stargazers_count'])

init.set_body(init_body)
init.when_no_intent_matched_go_to(idle)


def idle_body(session: Session):
    pass


idle.set_body(idle_body)
idle.when_event_go_to(github_event_matched, star_state, {'event': StarCreated()})
idle.when_event_go_to(github_event_matched, unstar_state, {'event': StarDeleted()})


def star_body(session: Session):
    e: StarCreated = session.event
    repo = e.payload["repository"]["full_name"]
    sender = e.payload["sender"]["login"]
    star_count = session.get(repo)
    session.set(repo, star_count + 1)
    telegram_platform.reply(session,f'{sender} decided to star {repo}, it now has {star_count+1} stars')


star_state.set_body(star_body)
star_state.go_to(idle)


def unstar_body(session: Session):
    e: StarCreated = session.event
    repo = e.payload["repository"]["full_name"]
    sender = e.payload["sender"]["login"]
    star_count = session.get(repo)
    session.set(repo, star_count - 1)
    telegram_platform.reply(session, f'{sender} decided to unstar {repo}, it now has {star_count - 1} stars')


unstar_state.set_body(unstar_body)
unstar_state.go_to(idle)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
