import inspect
from functools import partial
from typing import Union, Callable, TYPE_CHECKING

from baf.core.transition.event import Event
from baf.core.transition.condition import Condition, Conjunction
from baf.core.transition.transition import Transition
from baf.exceptions.exceptions import StateNotFound, ConflictingAutoTransitionError

if TYPE_CHECKING:
    from baf.core.session import Session
    from baf.core.state import State


class TransitionBuilder:
    """A transition builder.

    This class is used to build agent transitions, allowing for a "fluent api" syntax where consecutive calls can be
    made on the same object.

    Args:
        source (State): the source state of the transition
        event (Event): the event linked to the transition (can be None)
        condition (Condition): the condition associated to the transition (can be None)

    Attributes:
        source (State): The source state of the transition
        event (Event): The event linked to the transition (can be None)
        condition (Condition): The condition associated to the transition (can be None)
    """

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
    ) -> 'TransitionBuilder':
        """Adds a condition to the transition builder.

        Args:
            function (Union[Callable[[Session], bool], Callable[[Session, dict], bool]]): the condition function to add
                to the transition. Allowed function arguments are (:class:`~baf.core.session.Session`) or
                (:class:`~baf.core.session.Session`, dict) to add parameters within the dict argument. The
                function must return a boolean value
            params (dict, optional): the parameters for the condition function, necessary if the function has
                (:class:`~baf.core.session.Session`, dict) arguments

        Returns:
            TransitionBuilder: the transition builder with the new condition added
        """
        sig = inspect.signature(function)  #
        func_params = list(sig.parameters.keys())
        condition_function: Callable[['Session'], bool] = None
        # shouldn't we use Parameter type annotations for that ?
        if len(func_params) == 1:
            # session param
            condition_function = function
        elif len(func_params) == 2 and params is not None:
            # (session, params) param
            condition_function = partial(function, params=params)
        else:
            raise ValueError('Wrong Event Condition Function Signature!')

        if self.condition is None:
            self.condition = Condition(condition_function)
        else:
            self.condition = Conjunction(self.condition, Condition(condition_function))
        return self

    def go_to(self, dest: 'State') -> None:
        """Set the destination state of the transition.

        Completes the transition builder and effectively adds the source state.

        Args:
            dest (State): the destination state
        """
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
