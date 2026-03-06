DB Handler
==========

Besides the :doc:`monitoring_db`, BAF now provides a DB handler to query relational databases from your agent logic.

**The DB handler reads one or more DB credentials from the ``db.sql`` section in your agent properties file and opens connections lazily** (only when a query is executed).

Initialize the DB Handler
-------------------------

Create the handler once when defining the agent:

.. code:: python

    from besser.agent.core.agent import Agent
    from besser.agent.db import DBHandler

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
            dialect: postgresql
            host: localhost
            port: 5432
            database: analytics_db
            username: user
            password: pass

Query a DB in a State Body
--------------------------

The handler is available in sessions as ``session.db_handler``.

.. code:: python

    from besser.agent.core.session import Session

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

API References
--------------

- DBHandler: :class:`besser.agent.db.db_handler.DBHandler`
- Agent.use_db_handler(): :meth:`besser.agent.core.agent.Agent.use_db_handler`
- Session.db_handler: :attr:`besser.agent.core.session.Session.db_handler`
- DBHandler.query(): :meth:`besser.agent.db.db_handler.DBHandler.query`
