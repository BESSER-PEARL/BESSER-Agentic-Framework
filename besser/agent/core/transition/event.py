from abc import ABC
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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

    def store_in_db(self):
        pass
        # implement on each event
