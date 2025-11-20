from besser.agent.core.property import Property

SECTION_WEBSOCKET = 'websocket_platform'

WEBSOCKET_HOST = Property(SECTION_WEBSOCKET, 'websocket.host', str, 'localhost')
"""
The WebSocket host address. An agent has a WebSocket server that has to establish connection with a WebSocket client.

name: ``websocket.host``

type: ``str``

default value: ``localhost``
"""

WEBSOCKET_PORT = Property(SECTION_WEBSOCKET, 'websocket.port', int, 8765)
"""
The WebSocket address port. The WebSocket address is composed by a host name and a port

name: ``websocket.port``

type: ``int``

default value: ``8765``
"""

WEBSOCKET_MAX_SIZE = Property(SECTION_WEBSOCKET, 'websocket.max_size', int, None)
"""
WebSocket's maximum size of incoming messages, in bytes. :obj:`None` disables the limit.

name: ``websocket.max_size``

type: ``int``

default value: ``None``
"""

STREAMLIT_HOST = Property(SECTION_WEBSOCKET, 'streamlit.host', str, 'localhost')
"""
The Streamlit UI host address. If you are using our default UI, you must define its address where you can access and 
interact with the agent.

name: ``streamlit.host``

type: ``str``

default value: ``localhost``
"""

STREAMLIT_PORT = Property(SECTION_WEBSOCKET, 'streamlit.port', int, 5000)
"""
The Streamlit UI address port. The Streamlit UI address is composed by a host name and a port

name: ``streamlit.port``

type: ``int``

default value: ``5000``
"""

# --- Streamlit DB properties ---

SECTION_STREAMLIT_DB = 'streamlit_db'

DB_STREAMLIT = Property(SECTION_STREAMLIT_DB, 'db.streamlit', bool, None)
"""
Enable Streamlit user database persistence.

name: ``db.streamlit``
type: ``bool``
default value: ``True``
"""

DB_STREAMLIT_DIALECT = Property(SECTION_STREAMLIT_DB, 'db.streamlit.dialect', str, 'postgresql')
"""
Database dialect for Streamlit user database.

name: ``db.streamlit.dialect``
type: ``str``
default value: ``postgresql``
"""

DB_STREAMLIT_HOST = Property(SECTION_STREAMLIT_DB, 'db.streamlit.host', str, None)
"""
Database host for Streamlit user database.

name: ``db.streamlit.host``
type: ``str``
default value: ``127.0.0.1``
"""

DB_STREAMLIT_PORT = Property(SECTION_STREAMLIT_DB, 'db.streamlit.port', int, 5432)
"""
Database port for Streamlit user database.

name: ``db.streamlit.port``
type: ``int``
default value: ``5432``
"""

DB_STREAMLIT_DATABASE = Property(SECTION_STREAMLIT_DB, 'db.streamlit.database', str, None)
"""
Database name for Streamlit user database.

name: ``db.streamlit.database``
type: ``str``
default value: ``mydatabase``
"""

DB_STREAMLIT_USERNAME = Property(SECTION_STREAMLIT_DB, 'db.streamlit.username', str, None)
"""
Database username for Streamlit user database.

name: ``db.streamlit.username``
type: ``str``
default value: ``myuser``
"""

DB_STREAMLIT_PASSWORD = Property(SECTION_STREAMLIT_DB, 'db.streamlit.password', str, None)
"""
Database password for Streamlit user database.

name: ``db.streamlit.password``
type: ``str``
default value: ``mysecretpassword``
"""
