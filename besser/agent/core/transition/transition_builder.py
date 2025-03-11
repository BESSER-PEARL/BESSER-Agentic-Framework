import inspect
from functools import partial
from typing import Union, Callable, TYPE_CHECKING

from besser.agent.core.session import Session
from besser.agent.core.state import State
from besser.agent.core.transition.event import Event
from besser.agent.core.transition.condition import Condition
from besser.agent.core.transition.transition import Transition
from besser.agent.exceptions.exceptions import StateNotFound, ConflictingAutoTransitionError

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
            # todo: why we do not make a conjunction ?
            raise ValueError('You are replacing the condition!')

        sig = inspect.signature(function)  #
        func_params = list(sig.parameters.keys())
        condition_function: Callable[['Session'], bool] = None
        # shouldn't we use Parameter type annotations for that ?
        if len(func_params) == 1:
            # session param
            condition_function = function
        elif len(func_params) == 2 and params:
            # (session, params) param
            condition_function = partial(function, params=params)
        else:
            raise ValueError('Wrong Event Condition Function Signature!')
        self.condition = Condition(condition_function)
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
