import inspect
import traceback
from functools import partial
from typing import Callable, TYPE_CHECKING, Union

from besser.agent.core.event import Event, Condition, ReceiveMessageEvent
from besser.agent.exceptions.exceptions import StateNotFound, ConflictingAutoTransitionError
from besser.agent.exceptions.logger import logger
from besser.agent.library.event.event_library import variable_matches_operation, intent_matched

if TYPE_CHECKING:
    from besser.agent.core.session import Session
    from besser.agent.core.state import State


class TransitionBuilder:

    def __init__(self, source: 'State', event: Event = None, condition: Condition = None):
        self.source: 'State' = source
        self.event: Event = event
        self.condition: Condition = condition

    def with_condition(
            self,
            function: Union[
                Callable[['Session'], bool],
                Callable[['Session', dict], bool]
            ],
            params: dict = None
    ):
        if self.condition is not None:
            # to avoid doing: state.when_intent_matched(intent1).with_condition(...).go_to(state2)
            # why we do not make a conjunction ?
            raise ValueError('You are replacing the condition!!!!')

        sig = inspect.signature(function)
        func_params = list(sig.parameters.keys())
        condition_function: Callable[['Session'], bool] = None
        # shouldn't we use Parameter type annotations for that ?
        if func_params == ['session']:
            condition_function = function
        elif func_params == ['session', 'params'] and params:
            condition_function = partial(function, params=params)
        else:
            raise ValueError('Wrong Event Condition Function Signature!')
        self.condition = Condition(condition_function, params)
        return self

    def go_to(self, dest: 'State') -> None:
        if dest not in self.source._agent.states:
            raise StateNotFound(self.source._agent, dest)

        for transition in self.source.transitions:
            if transition.is_auto():
                raise ConflictingAutoTransitionError(self.source._agent, self.source)

        self.source.transitions.append(Transition(
            name=self.source._t_name(),
            source=self.source,
            dest=dest,
            event=self.event,
            condition=self.condition
        ))
        self.source._check_global_state(dest)


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

    def is_intent_matched(self, session: 'Session') -> bool:
        print('is_intent_matched not implemented')

    def is_variable_matching_operation(self, session: 'Session') -> bool:
        print('is_variable_matching_operation not implemented')

    def is_auto(self) -> bool:
        """Check if the transition event is `auto` (i.e. a transition that does not need any event to be triggered).

        Returns:
            bool: true if the transition's intent matches with the
            target one, false
        """
        return self.event is None and self.condition is None

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