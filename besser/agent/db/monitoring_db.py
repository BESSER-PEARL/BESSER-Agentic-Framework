from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

import json
import pandas as pd
from sqlalchemy import Connection, create_engine, Column, String, Integer, UniqueConstraint, ForeignKey, DateTime, \
    Float, MetaData, insert, Table, select, Executable, CursorResult, desc, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

from besser.agent.core.message import Message
from besser.agent.core.session import Session
from besser.agent.core.state import State
from besser.agent.core.transition.event import Event
from besser.agent.core.transition.transition import Transition
from besser.agent.exceptions.logger import logger
from besser.agent.db import DB_MONITORING_DIALECT, DB_MONITORING_PORT, DB_MONITORING_HOST, DB_MONITORING_DATABASE, \
    DB_MONITORING_USERNAME, DB_MONITORING_PASSWORD
from besser.agent.library.transition.events.base_events import ReceiveMessageEvent, ReceiveFileEvent
from besser.agent.library.transition.events.github_webhooks_events import GitHubEvent
from besser.agent.library.transition.events.gitlab_webhooks_events import GitLabEvent
from besser.agent.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction
from besser.agent.nlp.intent_classifier.llm_intent_classifier import LLMIntentClassifier

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent


TABLE_SESSION = 'session'
"""The name of the database table that contains the session records"""

TABLE_INTENT_PREDICTION = 'intent_prediction'
"""The name of the database table that contains the intent prediction records"""

TABLE_PARAMETER = 'parameter'
"""The name of the database table that contains the parameter records"""

TABLE_TRANSITION = 'transition'
"""The name of the database table that contains the transition records"""

TABLE_CHAT = 'chat'
"""The name of the database table that contains the chat records"""

TABLE_EVENT = 'event'
"""The name of the database table that contains the event records"""


class MonitoringDB:
    """This class is an interface to connect to a database where user interactions with the agent are stored to monitor
    the agent for later analysis.

    Attributes:
        conn (sqlalchemy.Connection): The connection to the monitoring database
        connected (bool): Whether there is an active connection to the monitoring database or not
    """

    def __init__(self):
        self.conn: Connection = None
        self.connected: bool = False

    def connect_to_db(self, agent: 'Agent') -> None:
        """Connect to the monitoring database.

        Args:
            agent (Agent): The agent that contains the database-related properties.
        """
        try:
            dialect = agent.get_property(DB_MONITORING_DIALECT)
            username = agent.get_property(DB_MONITORING_USERNAME)
            password = agent.get_property(DB_MONITORING_PASSWORD)
            host = agent.get_property(DB_MONITORING_HOST)
            port = agent.get_property(DB_MONITORING_PORT)
            database = agent.get_property(DB_MONITORING_DATABASE)
            url = f"{dialect}://{username}:{password}@{host}:{port}/{database}"
            engine = create_engine(url)
            self.conn = engine.connect()
            self.connected = True
        except Exception as e:
            logger.error(f"An error occurred while trying to connect to the monitoring DB in agent '{agent.name}'. "
                          f"See the attached exception:")
            logger.error(e)

    def initialize_db(self) -> None:
        """Initialize the monitoring database, creating the tables if necessary."""
        Base = declarative_base()  # Define a declarative base

        # Define the table schemas
        class TableSession(Base):
            __tablename__ = TABLE_SESSION
            id = Column(Integer, primary_key=True, autoincrement=True)
            agent_name = Column(String, nullable=False)
            session_id = Column(String, nullable=False)
            platform_name = Column(String, nullable=False)
            timestamp = Column(DateTime, nullable=False)
            variables = Column(String, nullable=True)
            __table_args__ = (
                UniqueConstraint('agent_name', 'session_id'),
            )

        class TableIntentPrediction(Base):
            __tablename__ = TABLE_INTENT_PREDICTION
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            message = Column(String, nullable=False)
            timestamp = Column(DateTime, nullable=False)
            intent_classifier = Column(String, nullable=False)
            intent = Column(String, nullable=False)
            score = Column(Float, nullable=False)

        class TableParameter(Base):
            __tablename__ = TABLE_PARAMETER
            id = Column(Integer, primary_key=True, autoincrement=True)
            intent_prediction_id = Column(Integer, ForeignKey(f'{TABLE_INTENT_PREDICTION}.id'), nullable=False)
            name = Column(String, nullable=False)
            value = Column(String)
            info = Column(String)

        class TableTransition(Base):
            __tablename__ = TABLE_TRANSITION
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            source_state = Column(String, nullable=False)
            dest_state = Column(String, nullable=False)
            event = Column(String, nullable=True)
            condition = Column(String, nullable=True)
            timestamp = Column(DateTime, nullable=False)

        class TableChat(Base):
            __tablename__ = TABLE_CHAT
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=False)
            type = Column(String, nullable=False)
            content = Column(JSONB, nullable=False)  # JSONB allows to handle the dictionary (TTS messages)
            is_user = Column(Boolean, nullable=False)
            timestamp = Column(DateTime, nullable=False)

        class TableEvent(Base):
            __tablename__ = TABLE_EVENT
            id = Column(Integer, primary_key=True, autoincrement=True)
            session_id = Column(Integer, ForeignKey(f'{TABLE_SESSION}.id'), nullable=True)
            event = Column(String, nullable=False)
            info = Column(String, nullable=True)
            timestamp = Column(DateTime, nullable=False)

        Base.metadata.create_all(self.conn)
        self.conn.commit()

    def insert_session(self, session: Session) -> None:
        """Insert a new session record into the sessions table of the monitoring database.

        Args:
            session (Session): the session to insert into the database
        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt = insert(table).values(
            agent_name=session._agent.name,
            session_id=session.id,
            platform_name=session.platform.__class__.__name__,
            timestamp=datetime.now(),
            variables="{}"
        )
        self.run_statement(stmt)
    def store_session_variables(self, session: Session) -> None:
        """
        Stores the current session variables (dictionary) as a JSON string in the monitoring database,
        replacing the old value for the given session.

        Args:
            session (Session): The session whose variables should be stored.
        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        session_dict = session.get_dictionary()
        json_variables = json.dumps(session_dict)
        stmt = (
            table.update()
            .where(
                table.c.agent_name == session._agent.name,
                table.c.platform_name == session.platform.__class__.__name__,
                table.c.session_id == session.id
            )
            .values(variables=json_variables)
        )
        self.run_statement(stmt)

    def load_session_variables(self, session: Session) -> None:
        """
        Loads the session variables from the monitoring database, transforms the JSON string into a dictionary,
        and sets each key-value pair in the session using session.set(key, value).

        Args:
            session (Session): The session whose variables should be loaded.
        """
        session_entry = self.select_session(session)
        if session_entry.empty:
            return
        variables_json = session_entry.iloc[0]['variables']
        try:
            variables_dict = json.loads(variables_json) if variables_json else {}
            for key, value in variables_dict.items():
                session.set(key, value)
        except Exception as e:
            logger.error(f"Error loading session variables: {e}")

    def insert_intent_prediction(
            self,
            session: Session,
            state: State,
            predicted_intent: IntentClassifierPrediction
    ) -> None:
        """Insert a new intent prediction record into the intent predictions table of the monitoring database.

        Args:
            session (Session): the session containing the predicted intent to insert into the database
            state (State): the state where the intent prediction took place (the session's current state may have
                changed since the intent prediction, so we need it as argument)
            predicted_intent (IntentClassifierPrediction): the intent prediction
        """
        table = Table(TABLE_INTENT_PREDICTION, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        if state not in session._agent.nlp_engine._intent_classifiers and predicted_intent.intent.name == 'fallback_intent':
            intent_classifier = 'None'
        elif isinstance(session._agent.nlp_engine._intent_classifiers[state], LLMIntentClassifier):
            intent_classifier = state.ic_config.llm_name
        else:
            intent_classifier = session._agent.nlp_engine._intent_classifiers[state].__class__.__name__,
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            message=predicted_intent.matched_sentence,
            timestamp=datetime.now(),
            intent_classifier=intent_classifier,
            intent=predicted_intent.intent.name,
            score=float(predicted_intent.score)
        )
        result = self.conn.execute(stmt.returning(table.c.id))  # Not committed until all parameters have been inserted
        intent_prediction_id = int(result.fetchone()[0])
        table = Table(TABLE_PARAMETER, MetaData(), autoload_with=self.conn)
        rows_to_insert = [
            {
                'intent_prediction_id': intent_prediction_id,
                'name': matched_parameter.name,
                'value': matched_parameter.value,
                'info': str(matched_parameter.info),
            } for matched_parameter in predicted_intent.matched_parameters
        ]
        if rows_to_insert:
            stmt = insert(table).values(rows_to_insert)
            self.run_statement(stmt)
        else:
            self.conn.commit()

    def insert_transition(self, session: Session, transition: Transition) -> None:
        """Insert a new transition record into the transitions table of the monitoring database.

        Args:
            session (Session): the session the transition belongs to
            transition (Transition): the transition to insert into the database
        """
        table = Table(TABLE_TRANSITION, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        if transition.is_event():
            event = transition.event.name
        else:
            event = ''
        if transition.condition:
            condition = str(transition.condition)
        else:
            condition = ''
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            source_state=transition.source.name,
            dest_state=transition.dest.name,
            event=event,
            condition=condition,
            timestamp=datetime.now(),
        )
        self.run_statement(stmt)

    def insert_chat(self, session: Session, message: Message) -> None:
        """Insert a new record into the chat table of the monitoring database.

        Args:
            session (Session): the session the transition belongs to
            message (Message): the message to insert into the database
        """
        table = Table(TABLE_CHAT, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)
        stmt = insert(table).values(
            session_id=int(session_entry['id'][0]),
            type=message.type.value,
            content=str(message.content),
            is_user=message.is_user,
            timestamp=message.timestamp,
        )
        self.run_statement(stmt)

    def insert_event(self, session: Session or None, event: Event) -> None:
        """Insert a new record into the event table of the monitoring database.

        Args:
            session (Session or None): the session the event belongs to, or None if the event is not associated to a
                session
            event (Event): the event to insert into the database
        """
        # TODO: We need to store agent id for broadcasted events
        table = Table(TABLE_EVENT, MetaData(), autoload_with=self.conn)
        if session is not None:
            session_id = int(self.select_session(session)['id'][0])
        else:
            session_id = None
        if isinstance(event, ReceiveMessageEvent):
            info = event.message
        elif isinstance(event, ReceiveFileEvent):
            info = event.file.name
        elif isinstance(event, GitHubEvent):
            info = {'category': event._category, 'action': event.action, 'payload': event.payload}
        elif isinstance(event, GitLabEvent):
            info = {'category': event._category, 'action': event.action, 'payload': event.payload}
        else:
            info = ''
        stmt = insert(table).values(
            session_id=session_id,
            event=event.name,
            info=str(info),
            timestamp=datetime.now()
        )
        self.run_statement(stmt)

    def select_session(self, session: Session) -> pd.DataFrame:
        """Retrieves a session record from the sessions table of the database.

        Args:
            session (Session): the session to get from the database

        Returns:
            pandas.DataFrame: the session record, should be a 1 row DataFrame

        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt = select(table).where(
            table.c.agent_name == session._agent.name,
            table.c.platform_name == session.platform.__class__.__name__,
            table.c.session_id == session.id
        )
        return pd.read_sql_query(stmt, self.conn)
    def session_exists(self, agent_name: str, platform_name: str, session_id: str) -> bool:
        """
        Checks whether there is an entry with the given agent_name, platform_name, and session_id in the sessions table.

        Args:
            agent_name (str): The agent name to check.
            platform_name (str): The platform name to check.
            session_id (str): The session ID to check.

        Returns:
            bool: True if the session exists, False otherwise.
        """
        table = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt = select(table).where(
            table.c.agent_name == agent_name,
            table.c.platform_name == platform_name,
            table.c.session_id == session_id
        )
        result = self.conn.execute(stmt)
        return result.first() is not None

    def delete_session(self, session: Session) -> None:
        """
        Deletes the session information, chat messages, and transitions related to the given session from the monitoring database.

        Args:
            session (Session): The session to delete.
        """
        # Get session DB id
        table_session = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt_session_id = select(table_session.c.id).where(
            table_session.c.agent_name == session._agent.name,
            table_session.c.platform_name == session.platform.__class__.__name__,
            table_session.c.session_id == session.id
        )
        result_session_id = self.conn.execute(stmt_session_id).first()
        if not result_session_id:
            logger.error(f"Session not found for deletion: {session.id}")
            return
        session_db_id = result_session_id[0]

        # Delete chat messages
        table_chat = Table(TABLE_CHAT, MetaData(), autoload_with=self.conn)
        stmt_delete_chat = table_chat.delete().where(table_chat.c.session_id == session_db_id)
        self.run_statement(stmt_delete_chat)

        # Delete transitions
        table_transition = Table(TABLE_TRANSITION, MetaData(), autoload_with=self.conn)
        stmt_delete_transition = table_transition.delete().where(table_transition.c.session_id == session_db_id)
        self.run_statement(stmt_delete_transition)

        # Delete session itself
        stmt_delete_session = table_session.delete().where(table_session.c.id == session_db_id)
        self.run_statement(stmt_delete_session)
    
    def get_last_state_of_session(self, agent_name: str, platform_name: str, session_id: str) -> str | None:
        """
        Retrieves the last dest_state for a given session from the transition table.

        Args:
            agent_name (str): The agent name.
            platform_name (str): The platform name.
            session_id (str): The session ID.

        Returns:
            str | None: The last dest_state value, or None if not found.
        """
        # Get session id
        table_session = Table(TABLE_SESSION, MetaData(), autoload_with=self.conn)
        stmt_session = select(table_session.c.id).where(
            table_session.c.agent_name == agent_name,
            table_session.c.platform_name == platform_name,
            table_session.c.session_id == session_id
        )
        result_session = self.conn.execute(stmt_session).first()
        if not result_session:
            return None
        session_db_id = result_session[0]

        # Get last dest_state from transition table
        table_transition = Table(TABLE_TRANSITION, MetaData(), autoload_with=self.conn)
        stmt_transition = (
            select(table_transition.c.dest_state)
            .where(table_transition.c.session_id == session_db_id)
            .order_by(desc(table_transition.c.timestamp))
            .limit(1)
        )
        result_transition = self.conn.execute(stmt_transition).first()
        return result_transition[0] if result_transition else None

    def select_chat(
        self,
        session: Session,
        n: Optional[int] = None,
        until_timestamp: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Retrieves chat records from the chat table of the database for a given session.

        Args:
            session (Session): the session to get chat records from the database
            n (Optional[int]): the number of latest chat records to retrieve. If None, retrieves all records.
            until_timestamp (Optional[datetime]): if provided, retrieves only chat records up to this timestamp.
        Returns:
            pandas.DataFrame: the chat records for the given session
        """

        table = Table(TABLE_CHAT, MetaData(), autoload_with=self.conn)
        session_entry = self.select_session(session)

        base_stmt = select(table).where(
            table.c.session_id == int(session_entry["id"][0])
        )

        if until_timestamp is not None:
            base_stmt = base_stmt.where(table.c.timestamp <= until_timestamp)

        if n:
            subq = (
                base_stmt
                .order_by(desc(table.c.timestamp), desc(table.c.id))
                .limit(n)
                .subquery()
            )
            stmt = select(subq).order_by(subq.c.timestamp, subq.c.id)

        else:
            # all rows, ordered chronologically
            stmt = base_stmt.order_by(table.c.timestamp, table.c.id)

        return pd.read_sql_query(stmt, self.conn)

    def run_statement(self, stmt: Executable) -> CursorResult[Any] | None:
        """Executes a SQL statement.

        Args:
            stmt (sqlalchemy.Executable): the SQL statement

        Returns:
            sqlalchemy.CursorResult[Any] | None: the result of the SQL statement
        """
        try:
            result = self.conn.execute(stmt)
            self.conn.commit()
            return result
        except Exception as e:
            logger.error(e)
            self.conn.rollback()
            return None

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Gets all the content of a database table (i.e., SELECT * FROM table_name).

        Args:
            table_name: the name of the table

        Returns:
            pandas.DataFrame: the table in a dataframe
        """
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql_query(query, self.conn)

    def close_connection(self) -> None:
        """Close the connection to the monitoring database"""
        self.conn.close()
        self.conn.engine.dispose()
        self.connected = False
