from abc import ABC
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class Event(ABC):
    """The event abstract class.

    An agent can receive events through its platforms. An agent can define transitions from one state to another based
    on the reception of specific events.

    This class serves as a template to implement events.

    Args:
        name (str): the event name
        session_id (str or None): the id of the session the event was sent to (can be none)
        timestamp (datetime): the timestamp indicating the event reception instant

    Attributes:
        _name (str): the event name
        _session_id (str or None): the id of the session the event was sent to (can be none)
        _timestamp (datetime): the timestamp indicating the event reception instant
    """

    def __init__(self, name: str, session_id: str or None = None, timestamp: datetime = None):
        self._name: str = name
        self._session_id: str or None = session_id
        self._timestamp: datetime = timestamp

    @property
    def name(self):
        """str: The name of the event"""
        return self._name

    @property
    def session_id(self):
        """str or None: The id of the session the event was sent to."""
        return self._session_id

    @property
    def timestamp(self):
        """datetime: The timestamp indicating the event reception instant."""
        return self._session_id

    def is_matching(self, event: 'Event') -> bool:
        """Check whether an event matches another one.

        This function can be overridden. Default behavior only checks if the event names are equal.

        Args:
            event (Event): the target event to compare

        Returns:
            bool: true if both events match, false otherwise
        """
        if isinstance(event, self.__class__):
            return self._name == event._name

    def is_broadcasted(self) -> bool:
        """Whether the event is broadcasted to all agent sessions or not (i.e., sent to a specific session)

        Returns:
            bool: true if the event is broadcasted, false otherwise
        """
        return self._session_id is None

    def log(self) -> str:
        """Create a log message for the event.

        This function can be overridden. Default message is the event name

        Returns:
            str: the log message
        """
        return self._name

    def store_in_db(self):
        pass
        # implement on each event
        # TODO: Create new DB table for events
