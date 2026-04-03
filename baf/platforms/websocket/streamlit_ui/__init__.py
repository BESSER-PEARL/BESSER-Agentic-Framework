"""Definition of the agent properties within the ``websocket_platform`` section:"""

from baf.core.property import Property


# --- Streamlit DB properties ---

DB_STREAMLIT = Property('db.streamlit.enabled', bool, False)
"""
Enable Streamlit user database persistence.

name: ``db.streamlit.enabled``
type: ``bool``
default value: ``False``
"""

DB_STREAMLIT_DIALECT = Property('db.streamlit.dialect', str, 'postgresql')
"""
Database dialect for Streamlit user database.

name: ``db.streamlit.dialect``
type: ``str``
default value: ``postgresql``
"""

DB_STREAMLIT_HOST = Property('db.streamlit.host', str, None)
"""
Database host for Streamlit user database.

name: ``db.streamlit.host``
type: ``str``
default value: ``None``
"""

DB_STREAMLIT_PORT = Property('db.streamlit.port', int, 5432)
"""
Database port for Streamlit user database.

name: ``db.streamlit.port``
type: ``int``
default value: ``5432``
"""

DB_STREAMLIT_DATABASE = Property('db.streamlit.database', str, None)
"""
Database name for Streamlit user database.

name: ``db.streamlit.database``
type: ``str``
default value: ``None``
"""

DB_STREAMLIT_USERNAME = Property('db.streamlit.username', str, None)
"""
Database username for Streamlit user database.

name: ``db.streamlit.username``
type: ``str``
default value: ``None``
"""

DB_STREAMLIT_PASSWORD = Property('db.streamlit.password', str, None)
"""
Database password for Streamlit user database.

name: ``db.streamlit.password``
type: ``str``
default value: ``None``
"""
