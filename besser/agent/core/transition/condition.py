from typing import Callable, TYPE_CHECKING

from besser.agent.core.session import Session

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Condition:

    def __init__(self, function: Callable[['Session'], bool]):
        self.function: Callable[['Session'], bool] = function

    def __call__(self, session: 'Session') -> bool:
        return self.function(session)

    def __str__(self):
        return self.function.__name__
