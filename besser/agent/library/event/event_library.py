"""
The collection of preexisting events.

Events are functions embedded in :class:`~besser.agent.core.transition.Transition` that, when called and return a `True`
value, trigger the transitions.
"""

from typing import Any, Callable, TYPE_CHECKING

from besser.agent.core.intent.intent import Intent
from besser.agent.platforms.github.github_webhooks_events import GitHubEvent
from besser.agent.platforms.gitlab.gitlab_webhooks_events import GitLabEvent

if TYPE_CHECKING:
    from besser.agent.core.session import Session


def auto(session: 'Session', event_params: dict) -> bool:
    """This event always returns True.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: always true
    """
    return True


def intent_matched(session: 'Session', params: dict) -> bool:
    target_intent: Intent = params['intent']
    predicted_intent = session.get('predicted_intent')
    # TODO: USE FLAG!!!!!!!!!!
    if predicted_intent is not None:
        matched_intent: Intent = session.get('predicted_intent').intent
        return target_intent.name == matched_intent.name
    return False


def github_event_matched(session: 'Session', event_params: dict) -> bool:
    """This event checks if the first event of the session is the expected event

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the 2 event are the same, false otherwise
    """
    if session.flags['event']:
        target_event: GitHubEvent = event_params['event']
        received_event: GitHubEvent = session.events.pop()
        session.events.append(received_event)
        return target_event.name == received_event.name and target_event.action == received_event.action


def gitlab_event_matched(session: 'Session', event_params: dict) -> bool:
    """This event checks if the first event of the session is the expected event

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the 2 event are the same, false otherwise
    """
    if session.flags['event']:
        target_event: GitLabEvent = event_params['event']
        received_event: GitLabEvent = session.events.pop()
        session.events.append(received_event)
        return target_event.name == received_event.name and target_event.action == received_event.action


def variable_matches_operation(session: 'Session', event_params: dict) -> bool:
    """This event checks if for a specific comparison operation, using a stored session value
    and a given target value, returns true.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the comparison operation of the given values returns true
    """
    # TODO: REFACTOR WITH NEW EVENTS
    var_name: str = event_params['var_name']
    target_value: Any = event_params['target']
    operation: Callable[[Any, Any], bool] = event_params['operation']
    current_value: Any = session.get(var_name)
    return operation(current_value, target_value)


def file_received(session: 'Session', event_params: dict) -> bool:
    """This event only returns True if a user just sent a file.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the user has sent a file and (if specified) the received file type corresponds to the allowed
        types as defined in "allowed_types"
    """
    # TODO: REFACTOR WITH NEW EVENTS
    if session.flags['file']:
        if "allowed_types" in event_params.keys():
            if session.file.type in event_params["allowed_types"] or session.file.type == event_params["allowed_types"]:
                return True
            return False
        return True
    return False
