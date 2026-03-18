from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine, URL

from besser.agent.exceptions.logger import logger

if TYPE_CHECKING:
    from besser.agent.core.agent import Agent
    from besser.agent.nlp.llm.llm import LLM


class DBHandler:
    """Relational database handler for agent business data.

    The handler reads SQL database definitions from ``db.sql`` in the agent
    configuration and opens connections lazily when they are first needed.
    """

    _REQUIRED_DB_FIELDS = {'dialect', 'host', 'port', 'database', 'username', 'password'}
    _SQL_COMMAND_PATTERN = re.compile(r'^\s*(?:/\*.*?\*/\s*|--.*?(?:\n|\r\n?)\s*)*([a-zA-Z]+)', re.DOTALL)

    def __init__(self, agent: 'Agent'):
        self._agent: 'Agent' = agent
        self._db_configs: dict[str, dict[str, Any]] = self._extract_db_configs(agent.config)
        self._engines: dict[str, Engine] = {}
        self._connections: dict[str, Connection] = {}

    @property
    def db_names(self) -> list[str]:
        """Return configured database names from ``db.sql`` (e.g., ``db1``, ``db2``)."""
        return sorted(self._db_configs.keys())

    def _extract_db_configs(self, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
        db_configs: dict[str, dict[str, Any]] = {}
        prefix = 'db.sql.'

        for key, value in config.items():
            if not key.startswith(prefix):
                continue
            remainder = key[len(prefix):]
            if '.' not in remainder:
                continue
            db_name, property_name = remainder.split('.', 1)
            db_configs.setdefault(db_name, {})[property_name] = value

        return db_configs

    def _validate_db_config(self, db_name: str, db_config: dict[str, Any]) -> bool:
        missing = sorted(field for field in self._REQUIRED_DB_FIELDS if db_config.get(field) is None)
        if missing:
            logger.error(
                "Missing required DB properties for '%s': %s. Expected under 'db.sql.%s'.",
                db_name,
                ', '.join(missing),
                db_name,
            )
            return False
        return True

    def _build_db_url(self, db_name: str) -> URL | str | None:
        try:
            db_config = self._db_configs[db_name]
            dialect = str(db_config['dialect'])

            if dialect.startswith('sqlite'):
                return URL.create(drivername=dialect, database=str(db_config['database']))

            return URL.create(
                drivername=dialect,
                username=str(db_config['username']),
                password=str(db_config['password']),
                host=str(db_config['host']),
                port=int(db_config['port']),
                database=str(db_config['database']),
            )
        except Exception as exc:
            logger.error("Could not build DB URL for '%s': %s", db_name, exc)
            return None

    def connect_to_db(self, db_name: str) -> Connection | None:
        """Get or create an active SQLAlchemy connection for a configured DB."""
        if db_name in self._connections:
            return self._connections[db_name]

        if db_name not in self._db_configs:
            logger.error(
                "Unknown database '%s'. Available databases: %s",
                db_name,
                ', '.join(self.db_names) or 'none',
            )
            return None

        db_config = self._db_configs[db_name]
        if not self._validate_db_config(db_name, db_config):
            return None

        url = self._build_db_url(db_name)
        if url is None:
            return None

        try:
            engine = create_engine(url)
            connection = engine.connect()
            self._engines[db_name] = engine
            self._connections[db_name] = connection
            return connection
        except Exception as exc:
            logger.error("Could not connect to database '%s': %s", db_name, exc)
            return None

    def close_all(self) -> None:
        """Close all opened DB connections."""
        for db_name, connection in list(self._connections.items()):
            try:
                connection.close()
            except Exception as exc:
                logger.error("Error closing DB connection '%s': %s", db_name, exc)

        for db_name, engine in list(self._engines.items()):
            try:
                engine.dispose()
            except Exception as exc:
                logger.error("Error disposing DB engine '%s': %s", db_name, exc)

        self._connections.clear()
        self._engines.clear()

    def query(self, db_name: str, query: str, llm: 'LLM | None' = None) -> Any:
        """Execute a SQL query.

        If ``llm`` is provided, ``query`` is treated as natural language and first
        translated into SQL using the schema of ``db_name`` as context.
        """
        sql_query = self._resolve_sql_query(db_name=db_name, query=query, llm=llm)
        if sql_query is None:
            return None
        return self._execute_sql(db_name=db_name, sql_query=sql_query)

    def select(self, db_name: str, query: str, llm: 'LLM | None' = None) -> Any:
        """Execute a SELECT query (read-only).

        The SQL command must be ``SELECT``.
        """
        sql_query = self._resolve_sql_query(
            db_name=db_name,
            query=query,
            llm=llm,
            required_sql_command='select',
        )
        if sql_query is None:
            return None
        return self._execute_sql(db_name=db_name, sql_query=sql_query)

    def insert(self, db_name: str, query: str, llm: 'LLM | None' = None) -> Any:
        """Execute an INSERT query.

        The SQL command must be ``INSERT``.
        """
        sql_query = self._resolve_sql_query(
            db_name=db_name,
            query=query,
            llm=llm,
            required_sql_command='insert',
        )
        if sql_query is None:
            return None
        return self._execute_sql(db_name=db_name, sql_query=sql_query)

    def update(self, db_name: str, query: str, llm: 'LLM | None' = None) -> Any:
        """Execute an UPDATE query.

        The SQL command must be ``UPDATE``.
        """
        sql_query = self._resolve_sql_query(
            db_name=db_name,
            query=query,
            llm=llm,
            required_sql_command='update',
        )
        if sql_query is None:
            return None
        return self._execute_sql(db_name=db_name, sql_query=sql_query)

    def delete(self, db_name: str, query: str, llm: 'LLM | None' = None) -> Any:
        """Execute a DELETE query.

        The SQL command must be ``DELETE``.
        """
        sql_query = self._resolve_sql_query(
            db_name=db_name,
            query=query,
            llm=llm,
            required_sql_command='delete',
        )
        if sql_query is None:
            return None
        return self._execute_sql(db_name=db_name, sql_query=sql_query)

    def _resolve_sql_query(
            self,
            db_name: str,
            query: str,
            llm: 'LLM | None' = None,
            required_sql_command: str | None = None,
            ) -> str | None:
        sql_query = query

        # Only perform NL-to-SQL translation when an LLM is explicitly provided.
        if llm is not None:
            sql_query = self._nl_to_sql(
                db_name=db_name,
                nl_query=query,
                llm=llm,
            )
            if sql_query is None:
                return None
            logger.debug("Translated NL query for '%s': %s", db_name, sql_query)

        if required_sql_command is not None:
            if not self._validate_sql_command(sql_query=sql_query, required_sql_command=required_sql_command):
                return None

        return sql_query

    def _execute_sql(self, db_name: str, sql_query: str) -> Any:
        connection = self.connect_to_db(db_name)
        if connection is None:
            return None

        try:
            result = connection.execute(text(sql_query))
            if result.returns_rows:
                rows = result.fetchall()
                columns = list(result.keys())
                if not rows:
                    return None
                if len(rows) == 1 and len(columns) == 1:
                    return rows[0][0]
                if len(rows) == 1:
                    return dict(zip(columns, rows[0]))
                return [dict(zip(columns, row)) for row in rows]

            connection.commit()
            return result.rowcount
        except Exception as exc:
            logger.error("SQL execution failed on '%s': %s", db_name, exc)
            try:
                connection.rollback()
            except Exception as rollback_exc:
                logger.error("Rollback failed on '%s': %s", db_name, rollback_exc)
            return None

    def _schema_description(self, db_name: str) -> str:
        connection = self.connect_to_db(db_name)
        if connection is None:
            return ''
        inspector = inspect(connection)
        table_names = inspector.get_table_names()

        if not table_names:
            return 'No tables found.'

        lines: list[str] = []
        for table_name in table_names:
            lines.append(f"Table: {table_name}")
            for column in inspector.get_columns(table_name):
                column_name = column.get('name')
                column_type = str(column.get('type'))
                nullable = column.get('nullable')
                lines.append(f"  - {column_name} ({column_type}), nullable={nullable}")
        return '\n'.join(lines)

    @staticmethod
    def _looks_like_sql(query: str) -> bool:
        normalized = query.strip().lower()
        sql_starts = ('select', 'insert', 'update', 'delete', 'with', 'create', 'drop', 'alter', 'truncate')
        return normalized.startswith(sql_starts)

    def _sql_command(self, sql_query: str) -> str | None:
        match = self._SQL_COMMAND_PATTERN.match(sql_query)
        if not match:
            logger.error('Could not detect SQL command from query.')
            return None
        return match.group(1).lower()

    def _validate_sql_command(self, sql_query: str, required_sql_command: str) -> bool:
        command = self._sql_command(sql_query)
        if command is None:
            return False
        required = required_sql_command.lower()
        if command != required:
            logger.error(
                "Invalid SQL command '%s'. This operation only accepts '%s'.",
                command,
                required,
            )
            return False
        return True

    def _default_llm(self) -> 'LLM | None':
        llms = self._agent.nlp_engine._llms
        if not llms:
            return None
        first_llm_name = next(iter(llms))
        return llms[first_llm_name]

    def _nl_to_sql(
            self,
            db_name: str,
            nl_query: str,
            llm: 'LLM',
    ) -> str | None:
        schema = self._schema_description(db_name)
        if schema == '':
            logger.error("Could not retrieve DB schema for '%s'.", db_name)
            return None
        system_message = (
            'You are an SQL query generator. '
            'Return exactly one valid SQL statement for the provided schema and user request. '
            'Return SQL only, with no explanations, markdown, or code fences.'
        )
        prompt = (
            f"Database schema:\n{schema}\n\n"
            f"User request:\n{nl_query}\n\n"
            "SQL statement:"
        )
        try:
            llm_response = llm.predict(message=prompt, system_message=system_message)
        except Exception as exc:
            logger.error("LLM prediction failed when translating natural language to SQL: %s", exc)
            return None
        if llm_response is None:
            logger.error('LLM returned an empty response when translating natural language to SQL.')
            return None
        return self._extract_sql(llm_response)

    @staticmethod
    def _extract_sql(text_response: str) -> str | None:
        fenced_match = re.search(r"```(?:sql)?\s*(.*?)```", text_response, flags=re.IGNORECASE | re.DOTALL)
        if fenced_match:
            sql = fenced_match.group(1).strip()
        else:
            sql = text_response.strip()

        sql = sql.strip().strip('`').strip()
        if not sql:
            logger.error('Could not extract SQL from LLM response.')
            return None

        return sql
