from functools import partial
from typing import Callable, Any

from besser.agent.core.intent.intent import Intent
from besser.agent.core.transition.condition import Condition
from besser.agent.library.transition.condition_functions import intent_matched, variable_matches_operation


class IntentMatcher(Condition):

    def __init__(self, intent: Intent):
        super().__init__(partial(intent_matched, params={'intent': intent}))
        self._intent = intent

    def __str__(self):
        return f"Intent Matching - {self._intent.name}"


class VariableOperationMatcher(Condition):

    def __init__(
            self,
            var_name: str,
            operation: Callable[[Any, Any], bool],
            target: Any
    ):
        super().__init__(partial(variable_matches_operation, params={'var_name': var_name, 'operation': operation, 'target': target}))
        self._var_name = var_name
        self._operation = operation
        self._target = target

    def __str__(self):
        return f"{self._var_name} " \
               f"{self._operation.__name__} " \
               f"{self._target}"
