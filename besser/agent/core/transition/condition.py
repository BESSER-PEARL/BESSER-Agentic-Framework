import functools
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Condition:
    """ The condition class.

    A condition embeds a boolean function. An agent can define transitions from one state to another based on the
    fulfillment of a condition.

    Args:
        function (Callable[[Session], bool]): the condition function. It takes the user session as parameter.

    Attributes:
        function (Callable[[Session], bool]): the condition function. It takes the user session as parameter.
    """

    def __init__(self, function: Callable[['Session'], bool]):
        self.function: Callable[['Session'], bool] = function

    def __call__(self, session: 'Session') -> bool:
        return self.function(session)

    def __str__(self):
        if isinstance(self.function, functools.partial):
            return self.function.func.__name__
        return self.function.__name__


class Conjunction(Condition):
    """A conjunction is the union of 2 conditions. A conjunction condition is fulfilled when the 2 conditions are
    fulfilled.

    Args:
        cond1 (Condition): the first condition of the conjunction
        cond2 (Condition): the second condition of the conjunction

    Attributes:
        log (str): the log message of the conjunction condition
    """

    def __init__(self, cond1: Condition, cond2: Condition):
        def conjunction(session: Session) -> bool:
            return cond1.function(session) and cond2.function(session)
        super().__init__(conjunction)
        self.log: str = f"{cond1} and {cond2}"

    def __str__(self):
        return self.log
