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

    A transition can have an event and/or a condition, and will be triggered when the target event (if any) was received
    and the condition (if any) is satisfied.

    Args:
        name (str): the transition name
        source (State): the source state of the transition (from where it is triggered)
        dest (State): the destination state of the transition (where the agent moves to)
        event (Event): the event that triggers the transition
        condition (Condition): the condition that triggers the transition

    Attributes:
        name (str): The transition name
        source (State): The source state of the transition (from where it is triggered)
        event (Event): The event that triggers the transition
        condition (Condition): The condition that triggers the transition
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

        Example: `receive_message_text (Intent Matching - hello_intent): [initial_state] --> [hello_state]`

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
        """Check if the transition is `auto` (i.e. no event nor condition linked to it).

        Returns:
            bool: true if the transition is auto, false otherwise
        """
        return self.event is None and self.condition is None

    def is_event(self) -> bool:
        """Check if the transition waits for an event.

        Returns:
            bool: true if the transition's event is not None
        """
        return self.event is not None

    def evaluate(self, session: 'Session', target_event: Event) -> bool:
        """Evaluate the transition, i.e., check if the transition's event was received and the transition condition is
        satisfied.

        Args:
            session (Session): the current user session
            target_event (Event): the event to evaluate

        Returns:
            bool: true if the target event matches the transition event and the transition condition is satisfied, false otherwise
        """
        return self.event.is_matching(target_event) and self.is_condition_true(session)

    def is_condition_true(self, session: 'Session') -> bool:
        """Evaluate the transition's condition.

        Args:
            session (Session): the current user session

        Returns:
            bool: true if the transition's condition is satisfied, false otherwise
        """
        try:
            if self.condition is None:
                return True
            return self.condition(session)
        except Exception as e:
            logger.error(f"An error occurred while executing '{self.condition.function.__name__}' condition from state "
                         f"'{self.source.name}'. See the attached exception:")
            traceback.print_exc()
        return False