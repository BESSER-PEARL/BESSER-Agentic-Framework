"""Definition of the agent properties within the ``websocket_platform`` section:"""

from besser.agent.core.property import Property


# --- Streamlit DB properties ---

SECTION_STREAMLIT_DB = 'streamlit_db'

DB_STREAMLIT = Property(SECTION_STREAMLIT_DB, 'db.streamlit', bool, None)
"""
Enable Streamlit user database persistence.

name: ``db.streamlit``
type: ``bool``
default value: ``None``
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
default value: ``None``
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
default value: ``None``
"""

DB_STREAMLIT_USERNAME = Property(SECTION_STREAMLIT_DB, 'db.streamlit.username', str, None)
"""
Database username for Streamlit user database.

name: ``db.streamlit.username``
type: ``str``
default value: ``None``
"""

DB_STREAMLIT_PASSWORD = Property(SECTION_STREAMLIT_DB, 'db.streamlit.password', str, None)
"""
Database password for Streamlit user database.

name: ``db.streamlit.password``
type: ``str``
default value: ``None``
"""
