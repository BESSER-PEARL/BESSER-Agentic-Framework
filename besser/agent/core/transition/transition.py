import traceback
from typing import TYPE_CHECKING

from besser.agent.core.transition.event import Event
from besser.agent.core.transition.condition import Condition
from besser.agent.exceptions.logger import logger

if TYPE_CHECKING:
    from besser.agent.core.session import Session
    from besser.agent.core.state import State


class Transition:
    """An agent transition from one state (source) to another (destination).

    A transition is triggered when an event occurs.

    Args:
        name (str): the transition name
        source (State): the source state of the transition (from where it is triggered)
        dest (State): the destination state of the transition (where the agent moves to)
        event (Callable[[Session, dict], bool]): the event that triggers the transition
        event_params (dict): the parameters associated to the event

    Attributes:
        name (str): The transition name
        source (State): The source state of the transition (from where it is triggered)
        dest (State): The destination state of the transition (where the agent moves to)
        event (Callable[[Session, dict], bool]): The event that triggers the transition
        event_params (dict): The parameters associated to the event
    """

    def __init__(
            self,
            name: str,
            source: 'State',
            dest: 'State',
            event: Event,
            condition: Condition
    ):
        self.name: str = name
        self.source: 'State' = source
        self.dest: 'State' = dest
        self.event: Event = event
        self.condition: Condition = condition

    def log(self) -> str:
        """Create a log message for the transition. Useful when transitioning from one state to another to track the
        agent state.

        Example: `intent_matched (hello_intent): [state_0] --> [state_1]`

        Returns:
            str: the log message
        """
        if self.is_auto():
            return f"auto: [{self.source.name}] --> [{self.dest.name}]"
        elif self.event is None:
            return f"({self.condition}): [{self.source.name}] --> [{self.dest.name}]"
        elif self.condition is None:
            return f"{self.event.name}: [{self.source.name}] --> [{self.dest.name}]"
        else:
            return f"{self.event.name} ({self.condition}): [{self.source.name}] --> [{self.dest.name}]"

    def is_auto(self) -> bool:
        """Check if the transition event is `auto` (i.e. a transition that does not need any event to be triggered).

        Returns:
            bool: true if the transition's intent matches with the
            target one, false
        """
        return self.event is None and self.condition is None

    def is_event(self) -> bool:
        """Check if the transition wait for an event.

        Returns:
            bool: true if the transition's event is not None
        """
        return self.event is not None

    def evaluate(self, session: 'Session', target_event: Event):
        return self.event.is_matching(target_event) and self.is_condition_true(session)

    def is_condition_true(self, session: 'Session') -> bool:
        try:
            if self.condition is None:
                return True
            return self.condition(session)
        except Exception as e:
            logger.error(f"An error occurred while executing '{self.condition.function.__name__}' condition from state "
                         f"'{self.source.name}'. See the attached exception:")
            traceback.print_exc()
        return False