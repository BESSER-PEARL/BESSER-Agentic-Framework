import json
from typing import TYPE_CHECKING

from besser.agent.core.file import File
from besser.agent.core.transition.event import Event
from besser.agent.exceptions.logger import logger
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

if TYPE_CHECKING:
    from besser.agent.core.session import Session


class DummyEvent(Event):

    def __init__(self):
        super().__init__('dummy')


class ReceiveMessageEvent(Event):
    @staticmethod
    def create_event_from(message: str = None, session: 'Session' = None, human: bool = True):
        event = None
        try:
            payload = json.loads(message)
            event = ReceiveJSONEvent(payload, session.id, human)
        except json.JSONDecodeError:
            text = message
            event = ReceiveTextEvent(text, session.id, human)
            event.predict_intent(session)
        finally:
            return event

    def __init__(self, message: str = None, session_id: str = None, human: bool = True):
        super().__init__('receive_message', session_id)
        self.message: str = message
        self.human: bool = human  # TODO Do this here or higher?

    def is_matching(self, event: 'Event') -> bool:
        if isinstance(event, self.__class__):
            return event._name.startswith(self._name)


class ReceiveTextEvent(ReceiveMessageEvent):
    def __init__(self, text: str = None, session_id: str = None, human: bool = False):
        super().__init__(text, session_id, human)
        self._name = 'receive_message_text'
        self.text = text
        self.predicted_intent: IntentClassifierPrediction = None

    def predict_intent(self, session: 'Session'):
        if self.predicted_intent is None or self.predicted_intent.state != session.current_state.name:
            # Only run intent prediction if it was not done before or done from another state
            self.message = session._agent.process(session=session, message=self.message, is_user_message=True)
            #logger.info(f'Received message: {self.message}')
            self.predicted_intent = session._agent._nlp_engine.predict_intent(session)
            # TODO: LOG AT THE EVENT LEVEL
            logger.info(f'Detected intent: {self.predicted_intent.intent.name}')
            session._agent._monitoring_db_insert_intent_prediction(session)
            # for parameter in session.get("predicted_intent").matched_parameters:
            # TODO: LOG AT THE EVENT LEVEL
            #     logger.info(f"Parameter '{parameter.name}': {parameter.value}, info = {parameter.info}")
            # session.current_state.receive_intent(session)


class ReceiveJSONEvent(ReceiveMessageEvent):
    def __init__(self, payload_object = None, session_id: str = None, human: bool = False):
        super().__init__(json.dumps(payload_object), session_id, human)
        self._name = 'receive_message_json'
        self.payload = payload_object


class ReceiveFileEvent(Event):
    def __init__(self, file=None, session_id: str = None, human: bool = True):
        super().__init__('receive_file', session_id)
        self.file: File = file
        self.human: bool = human  # TODO Do this here or higher?
