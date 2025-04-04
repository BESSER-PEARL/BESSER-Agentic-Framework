# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging

from besser.agent.core.agent import Agent
from besser.agent.core.session import Session
from besser.agent.exceptions.logger import logger
from besser.agent.platforms.gitlab.gitlab_objects import Issue
from besser.agent.library.transition.events.gitlab_webhooks_events import IssuesOpened, GitLabEvent, IssueCommentCreated, IssuesUpdated

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

agent = Agent('issue_thanking_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.ini')
# Define the platform your agent will use
gitlab_platform = agent.use_gitlab_platform()

# STATES

idle = agent.new_state('idle', initial=True)
issue_state = agent.new_state('issue_opened')


# STATES BODIES' DEFINITION + TRANSITIONS


def global_fallback_body(session: Session):
    print('Greetings from global fallback')


# Assigned to all agent states (overriding all currently assigned fallback bodies).
agent.set_global_fallback_body(global_fallback_body)


def idle_body(session: Session):
    pass


idle.set_body(idle_body)
# The following transitions allow to flush the events created by the actions of the agent
idle.when_event(IssuesOpened()).go_to(issue_state)
idle.when_event(IssuesUpdated()).go_to(idle)
idle.when_event(IssueCommentCreated()).go_to(idle)


def issue_body(session: Session):
    event: GitLabEvent = session.event
    user_repo = event.payload['project']['path_with_namespace'].split('/')
    issue_iid = event.payload['object_attributes']['iid']
    issue: Issue = gitlab_platform.get_issue(
        user=user_repo[0],
        repository=user_repo[1],
        issue_number=issue_iid)
    gitlab_platform.comment_issue(issue,
        'Hey,\n\nThanks for opening an issue!<br>We will look at that as soon as possible.')


issue_state.set_body(issue_body)
issue_state.go_to(idle)

# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
