import json
import threading
import time
from collections import deque
from datetime import datetime
from typing import Any, TYPE_CHECKING

from pandas import DataFrame
from websocket import WebSocketApp

from besser.agent.core.event import ReceiveMessageEvent, Event
from besser.agent.core.message import Message, MessageType, get_message_type
from besser.agent.core.transition import Transition
from besser.agent.core.file import File
from besser.agent.exceptions.logger import logger
from besser.agent.db import DB_MONITORING
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.agent.nlp.rag.rag import RAGMessage
from besser.agent.platforms.payload import PayloadEncoder, Payload, PayloadAction

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.core.state import State
    from besser.agent.platforms.platform import Platform


class Session:
    """A user session in an agent execution.

    When a user starts interacting with an agent, a session is assigned to him/her to store user related information, such
    as the current state of the agent, the conversation history, the detected intent with its parameters or any user's
    private data. A session can be accessed from the body of the states to read/write user information.

    Args:
        session_id (str): The session id, which must unique among all agent sessions
        agent (Agent): The agent the session belongs to
        platform (Platform): The platform where the session has been created

    Attributes:
        _id (str): The session id, which must unique among all agent sessions
        _agent (str): The agent the session belongs to
        _platform (str): The platform where the session has been created
        _current_state (str): The current state in the agent for this session
        _dictionary (str): Storage of private data for this session
        _message (str): The last message sent to the agent by this session
        _predicted_intent (str): The last predicted intent for this session
        _file: File or None: The last file sent to the agent.
        _event: Any or None: The last event to trigger a transition.
        flags (dict[str, bool]): A dictionary of boolean flags.
            A `predicted_intent flag` is set to true when an intent is received. When the evaluation of the
            current state's transitions is done, the flag is set to false. It may happen that a transition different
            from the one associated with this intent is triggered (e.g. one evaluating some condition). In the following
            state, if there is a transition associated with the same intent, it should not be triggered as the time for
            this intent passed (unless the same intent is detected, in such case the flag will be set to true again).
            Another flag `file_flag` is used for the same purpose but for files sent by the user
            Another flag `event_flag` is used for the same purpose but for external events
        agent_connections (dict[str, WebSocketApp]): WebSocket client connections to other agent's WebSocket platforms.
            These connections enable an agent to send messages to other agents.
        _events: deque[Any]: The queue of received external events to process
    """

    def __init__(
            self,
            session_id: str,
            agent: 'Agent',
            platform: 'Platform',
    ):
        self._id: str = session_id
        self._agent: 'Agent' = agent
        self._platform: 'Platform' = platform
        self._current_state: 'State' = self._agent.initial_state()
        self._dictionary: dict[str, Any] = {}
        # self._message: str or None = None
        # self._predicted_intent: IntentClassifierPrediction or None = None
        # self._file: File or None = None
        self._event: Event = None
        # self.flags: dict[str, bool] = {
        #     # 'predicted_intent': False,
        #     # 'file': False,
        #     'event': False
        # }
        self.agent_connections: dict[str, WebSocketApp] = {}
        self._events: deque[Event] = deque()

    @property
    def id(self):
        """str: The session id."""
        return self._id

    @property
    def platform(self):
        """Platform: The session platform."""
        return self._platform

    @property
    def current_state(self):
        """State: The current agent state of the session."""
        return self._current_state

    # @property
    # def message(self):
    #     """str: The last message sent to the agent."""
    #     return self._message
    #
    # @message.setter
    # def message(self, message):
    #     """
    #     Set the last message sent to the agent.
    #     Args:
    #         message (str): the message to set in the session
    #     """
    #     # TODO: IF STORE_CHAT_HISTORY...
    #     self.save_message(Message(t=MessageType.STR, content=message, is_user=True, timestamp=datetime.now()))
    #     self._message = message
    #
    # @property
    # def file(self):
    #     """str: The last file sent to the agent."""
    #     return self._file
    #
    # @file.setter
    # def file(self, file: File):
    #     """
    #     Set the last file sent to the agent.
    #     Args:
    #         file (File): the file to set in the session
    #     """
    #     # TODO: Files are not stored in the DB
    #     self._file = file
    #     self.flags['file'] = True

    @property
    def event(self):
        """Event: The last event matched by the agent."""
        return self._event

    @event.setter
    def event(self, event: Event):
        """
        Set the last event matched by the agent.
        Args:
            event (Event): the event to set in the session
        """
        # TODO: Event are not stored in the DB
        self._event = event

    # @property
    # def predicted_intent(self):
    #     """str: The last predicted intent for this session."""
    #     return self._predicted_intent
    #
    # @predicted_intent.setter
    # def predicted_intent(self, predicted_intent: IntentClassifierPrediction):
    #     """Set the last predicted intent for this session.
    #
    #     Args:
    #         predicted_intent (File): the last predicted intent
    #     """
    #     self._predicted_intent = predicted_intent
    #     self.flags['predicted_intent'] = True

    @property
    def events(self):
        """dequeue[Event]: The queue of pending events for this session"""
        return self._events

    def get_chat_history(self, n: int = None) -> list[Message]:
        """Get the history of messages between this session and its agent.

        Args:
            n (int or None): the number of messages to get (from the most recents). If none is provided, gets all the
                messages

        Returns:
            list[Message]: the conversation history
        """
        chat_history: list[Message] = []
        if self._agent.get_property(DB_MONITORING) and self._agent._monitoring_db.connected:
            chat_df: DataFrame = self._agent._monitoring_db.select_chat(self, n=n)
            for i, row in chat_df.iterrows():
                t = get_message_type(row['type'])
                chat_history.append(Message(t=t, content=row['content'], is_user=row['is_user'], timestamp=row['timestamp']))
        else:
            logger.warning('Could not retrieve the chat history from the database.')
        return chat_history

    def save_message(self, message: Message) -> None:
        """Save a message in the dedicated chat DB

        Args:
            message (Message): the message to save
        """
        self._agent._monitoring_db_insert_chat(self, message)

    def set(self, key: str, value: Any) -> None:
        """Set an entry to the session private data storage.

        Args:
            key (str): the entry key
            value (Any): the entry value
        """
        self._dictionary[key] = value

    def get(self, key: str) -> Any:
        """Get an entry of the session private data storage.

        Args:
            key (str): the entry key

        Returns:
            Any: the entry value, or None if the key does not exist
        """
        if key not in self._dictionary:
            return None
        return self._dictionary[key]

    def delete(self, key: str) -> None:
        """Delete an entry of the session private data storage.

        Args:
            key (str): the entry key
        """
        try:
            del self._dictionary[key]
        except Exception as e:
            return None

    def move(self, transition: Transition) -> None:
        """Move to another agent state.

        Args:
            transition (Transition): the transition that points to the agent state to move
        """
        logger.info(transition.log())
        self._agent._monitoring_db_insert_transition(self, transition)
        if any(transition.dest is global_state for global_state in self._agent.global_state_component):
            self.set("prev_state", self.current_state)
        self._current_state = transition.dest
        self._current_state.run(self)

    def reply(self, message: str) -> None:
        """An agent message (usually a reply to a user message) is sent to the session platform to show it to the user.

        Args:
            message (str): the agent reply
        """
        # Multi-platform
        self._platform.reply(self, message)

    def create_agent_connection(self, url) -> None:
        """Create a WebSocket connection to a specific WebSocket URL.

        Args:
            url (str): the WebSocket server's URL
        """
        finished = False

        def on_message(ws, payload_str):
            payload: Payload = Payload.decode(payload_str)
            if payload.action == PayloadAction.AGENT_REPLY_STR.value:
                event: ReceiveMessageEvent = ReceiveMessageEvent.create_event_from(
                    message=payload.message,
                    session=self,
                    human=False)
                event.predict_intent(self)
                self._agent.receive_event(event)
        def on_open(ws):
            nonlocal finished
            finished = True

        def on_close(ws, close_status_code, close_msg):
            del self.agent_connections[url]

        def on_error(ws, error):
            nonlocal finished
            finished = True

        ws = WebSocketApp(url, on_message=on_message, on_open=on_open, on_close=on_close, on_error=on_error)
        websocket_thread = threading.Thread(target=ws.run_forever)
        websocket_thread.start()
        self.agent_connections[url] = ws
        while not finished:
            # Wait until the connection is open
            time.sleep(0.01)

    def send_message_to_websocket(self, url: str, message: Any) -> None:
        """Send a message to a WebSocket Server, generally used to send a message to an agent through the WebSocket
        platform.

        Args:
            url (str): the WebSocket URL (i.e., the target agent's WebSocket platform URL)
            message (Any): the message to send to the WebSocket server
        """
        logger.info(f'Sending message to {url}')
        if url not in self.agent_connections:
            self.create_agent_connection(url)
        if url not in self.agent_connections:
            logger.error(f'Could not connect to {url}')
            return
        ws = self.agent_connections[url]
        payload = Payload(action=PayloadAction.AGENT_REPLY_STR,
                          message=message)
        ws.send(json.dumps(payload, cls=PayloadEncoder))

    def run_rag(self, message: str = None, llm_prompt: str = None, llm_name: str = None, k: int = None, num_previous_messages: int = None) -> RAGMessage:
        """Run the RAG engine.

        Args:
            message (str): the input query for the RAG engine. If none is provided, the last user message will be used
                by default
            llm_prompt (str): the prompt containing the instructions for the LLM to generate an answer from the
                retrieved content. If none is provided, the RAG's default value will be used
            llm_name (str): the name of the LLM to use. If none is provided, the RAG's default value will be used
            k (int): number of chunks to retrieve from the vector store. If none is provided, the RAG's default value
                will be used
            num_previous_messages (int): number of previous messages of the conversation to add to the prompt context.
                If none is provided, the RAG's default value will be used. Necessary a connection to
                :class:`~besser.agent.db.monitoring_db.MonitoringDB`

        Returns:
            RAGMessage: the answer generated by the RAG engine
        """
        if self._agent.nlp_engine._rag is None:
            raise ValueError('Attempting to run RAG in an agent with no RAG engine.')
        return self._agent.nlp_engine._rag.run(self, message, llm_prompt, llm_name, k, num_previous_messages)
