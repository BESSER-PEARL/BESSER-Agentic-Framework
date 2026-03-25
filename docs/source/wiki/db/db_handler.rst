DB Handler
==========

Besides the :doc:`monitoring_db`, BAF now provides a DB handler to query relational databases from your agent logic.

**The DB handler reads one or more DB credentials from the ``db.sql`` section in your agent properties file and opens connections lazily** (only when a query is executed).

Initialize the DB Handler
-------------------------

Create the handler once when defining the agent:

.. code:: python

    from baf.core.agent import Agent
    from baf.db import DBHandler

    agent = Agent('weather_agent')
    agent.load_properties('config.yaml')

    # No DB connection is created yet
    db_handler: DBHandler = agent.use_db_handler()

You can define multiple DBs in configuration:

.. code:: yaml

    db:
      sql:
        - db1:
            dialect: postgresql
            host: localhost
            port: 5432
            database: weather_db
            username: user
            password: pass
        - db2:
            dialect: sqlite
            file: path/to/local_database.db

Query a DB in a State Body
--------------------------

The handler is available in sessions as ``session.db_handler``.

.. code:: python

    from baf.core.session import Session

    def weather_body(session: Session):
        city = 'Barcelona'

        # Raw SQL query
        temperature = session.db_handler.query(
            db_name='db1',
            query=f"SELECT temperature FROM weather WHERE city='{city}'"
        )

        session.reply(f"The weather in {city} is {temperature}°C.")

You can also provide a natural language query and an LLM to translate it into SQL:

.. code:: python

    temperature = session.db_handler.query(
        db_name='db1',
        query=f"Get the weather in {city}",
        llm=gpt,
    )

Operation-specific Queries
--------------------------

Besides ``query()``, the DB handler provides operation-specific methods:

- ``select()``: only accepts ``SELECT`` SQL
- ``insert()``: only accepts ``INSERT`` SQL
- ``update()``: only accepts ``UPDATE`` SQL
- ``delete()``: only accepts ``DELETE`` SQL

If the SQL command does not match the called method, the query is not executed, an error is logged,
and the method returns ``None``. This validation also applies when SQL is generated from natural
language with an LLM.

.. code:: python

    # SELECT
    rows = session.db_handler.select('db1', 'SELECT * FROM weather')

    # INSERT
    session.db_handler.insert(
        'db1',
        "INSERT INTO weather(city, temperature) VALUES ('Barcelona', 21)",
    )

    # UPDATE
    session.db_handler.update(
        'db1',
        "UPDATE weather SET temperature=22 WHERE city='Barcelona'",
    )

    # DELETE
    session.db_handler.delete(
        'db1',
        "DELETE FROM weather WHERE city='Barcelona'",
    )

API References
--------------

- DBHandler: :class:`baf.db.db_handler.DBHandler`
- Agent.use_db_handler(): :meth:`baf.core.agent.Agent.use_db_handler`
- Session.db_handler: :attr:`baf.core.session.Session.db_handler`
- DBHandler.query(): :meth:`baf.db.db_handler.DBHandler.query`
- DBHandler.select(): :meth:`baf.db.db_handler.DBHandler.select`
- DBHandler.insert(): :meth:`baf.db.db_handler.DBHandler.insert`
- DBHandler.update(): :meth:`baf.db.db_handler.DBHandler.update`
- DBHandler.delete(): :meth:`baf.db.db_handler.DBHandler.delete`
