import json

from besser.agent.core.file import File
from besser.agent.core.session import Session
from besser.agent.core.transition.event import Event
from besser.agent.exceptions.logger import logger


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
        self._message: str = message
        self.human: bool = human  # TODO Do this here or higher?

    def is_matching(self, event: 'Event') -> bool:
        if isinstance(event, self.__class__):
            return event._name.startswith(self._name)

    def predict_intent(self, session: 'Session'):
        pass


class ReceiveTextEvent(ReceiveMessageEvent):
    def __init__(self, text: str = None, session_id: str = None, human: bool = False):
        super().__init__(text, session_id, human)
        self._name = 'receive_message_text'
        self.text = text

    def predict_intent(self, session: 'Session'):
        self._message = session._agent.process(session=session, message=self._message, is_user_message=True)
        # message is not stored in session dictionary, but in event (self.text)
        session.set('message', self._message)  # TODO: Message is not being stored in DB
        logger.info(f'Received message: {self._message}')
        session.set('predicted_intent', session._agent._nlp_engine.predict_intent(session))
        logger.info(f'Detected intent: {session.get("predicted_intent").intent.name}')
        session._agent._monitoring_db_insert_intent_prediction(session)
        for parameter in session.get("predicted_intent").matched_parameters:
            logger.info(f"Parameter '{parameter.name}': {parameter.value}, info = {parameter.info}")
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
