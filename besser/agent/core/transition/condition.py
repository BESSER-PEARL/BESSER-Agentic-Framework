from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Condition:

    def __init__(self, function: Callable[['Session'], bool]):
        self.function: Callable[['Session'], bool] = function

    def __call__(self, session: 'Session') -> bool:
        return self.function(session)

    def __str__(self):
        return self.function.__name__


class Conjunction(Condition):

    def __init__(self, cond1: Condition, cond2: Condition):
        def conjunction(session: Session) -> bool:
            return cond1.function(session) and cond2.function(session)
        super().__init__(conjunction)
        self.log: str = f"{cond1} and {cond2}"

    def __str__(self):
        return self.log
