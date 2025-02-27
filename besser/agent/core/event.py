from abc import ABC
from functools import partial
from typing import Callable, TYPE_CHECKING, Any

from besser.agent.core.file import File
from besser.agent.core.intent.intent import Intent
from besser.agent.exceptions.logger import logger
from besser.agent.library.event.event_library import intent_matched, variable_matches_operation

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Condition:

    def __init__(self, function: Callable[['Session'], bool]):
        self.function: Callable[['Session'], bool] = function

    def __call__(self, session: 'Session') -> bool:
        return self.function(session)

    def __str__(self):
        return self.function.__name__

class IntentMatcher(Condition):

    def __init__(self, intent: Intent):
        super().__init__(partial(intent_matched, params={'intent': intent}))
        self._intent = intent

    def __str__(self):
        return f"Intent Matching ({self._intent.name}):"

class VariableOperationMatcher(Condition):

    def __init__(self, var_name: str,
            operation: Callable[[Any, Any], bool],
            target: Any):
        super().__init__(partial(variable_matches_operation, params={'var_name': var_name, 'operation': operation, 'target': target}))
        self._var_name = var_name
        self._operation = operation
        self._target = target

    def __str__(self):
        return f"({self._var_name} " \
               f"{self._operation.__name__} " \
               f"{self._target}): "

class Event(ABC):

    def __init__(self, name: str, session_id: str = None):
        self._name: str = name
        self._session_id: str = session_id

    @property
    def name(self):
        """str: The name of the event"""
        return self._name


    def is_matching(self, event: 'Event') -> bool:
        # TODO: Actually check on the payload
        # TODO: Make abstract to force specific implem for each event type ?
        if isinstance(event, self.__class__):
            return self._name == event._name

    def is_broadcasted(self) -> bool:
        return self._session_id is None

    @property
    def session_id(self):
        return self._session_id


class DummyEvent(Event):

    def __init__(self):
        super().__init__('dummy')


class ReceiveMessageEvent(Event):
    def __init__(self, message: str = None, session_id: str = None, human: bool = True):
        super().__init__('receive_message', session_id)
        self.message: str = message
        self.human: bool = human  # TODO Do this here or higher?

    def predict_intent(self, session: 'Session'):
        self.message = session._agent.process(session=session, message=self.message, is_user_message=True)
        session.set('message', self.message)  # TODO: Message is not being stored in DB
        logger.info(f'Received message: {self.message}')
        session.set('predicted_intent', session._agent._nlp_engine.predict_intent(session))
        logger.info(f'Detected intent: {session.get("predicted_intent").intent.name}')
        session._agent._monitoring_db_insert_intent_prediction(session)
        for parameter in session.get("predicted_intent").matched_parameters:
            logger.info(f"Parameter '{parameter.name}': {parameter.value}, info = {parameter.info}")
        # session.current_state.receive_intent(session)


class ReceiveFileEvent(Event):
    def __init__(self, file=None, session_id: str = None, human: bool = True):
        super().__init__('receive_file', session_id)
        self.file: File = file
        self.human: bool = human  # TODO Do this here or higher?
