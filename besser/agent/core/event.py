from abc import ABC
from typing import Callable, TYPE_CHECKING

from besser.agent.exceptions.logger import logger


if TYPE_CHECKING:
    from besser.agent.core.session import Session


class Condition:

    def __init__(self, function: Callable[['Session'], bool], params: dict = None):
        if params is None:
            params = {}
        self.function: Callable[['Session'], bool] = function
        self.params: dict = params

    def evaluate(self, session: 'Session') -> bool:
        return self.function(session)


class Event(ABC):

    def __init__(self, name):
        self._name: str = name

    @property
    def name(self):
        """str: The name of the event"""
        return self._name

    def is_matching(self, event: 'Event') -> bool:
        # TODO: Actually check on the payload
        if isinstance(event, self.__class__):
            return self._name == event._name


class DummyEvent(Event):

    def __init__(self):
        super().__init__('dummy')


class ReceiveMessageEvent(Event):
    def __init__(self, message=None, human: bool = True):
        super().__init__('receive_message')
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
