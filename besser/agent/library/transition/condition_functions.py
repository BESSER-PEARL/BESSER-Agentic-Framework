"""
The collection of preexisting condition functions.

Functions embedded in :class:`~besser.agent.core.transition.condition.Condition` that, when called and return a `True`
value, trigger the transitions.
"""

from typing import Any, Callable, TYPE_CHECKING

from besser.agent.core.intent.intent import Intent

if TYPE_CHECKING:
    from besser.agent.core.session import Session


def intent_matched(session: 'Session', params: dict) -> bool:
    target_intent: Intent = params['intent']
    predicted_intent = session.get('predicted_intent')  # TODO : GET PRED INTENT FROM EVENT
    if predicted_intent is not None:
        matched_intent: Intent = session.get('predicted_intent').intent
        return target_intent.name == matched_intent.name
    return False


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
    # TODO: why though ? we can only deprecate it and still provide it similarly to the intent_matched one
    var_name: str = event_params['var_name']
    target_value: Any = event_params['target']
    operation: Callable[[Any, Any], bool] = event_params['operation']
    current_value: Any = session.get(var_name)
    return operation(current_value, target_value)


def file_type(session: 'Session', event_params: dict) -> bool:
    """This event only returns True if a user sent a file of an allowed type.

    Args:
        session (Session): the current user session
        event_params (dict): the event parameters

    Returns:
        bool: True if the user has sent a file and the received file type corresponds to the allowed
        types as defined in "allowed_types"
    """
    if "allowed_types" in event_params.keys():
        if session.event.file.type in event_params["allowed_types"] or session.event.file.type == event_params["allowed_types"]:
            return True
        return False
    return True
