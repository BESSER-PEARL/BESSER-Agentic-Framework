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

STREAMLIT_CHAT_DEFAULT_SIZE = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.size', int, 16)
"""
Default chat font size used by Streamlit chat UI when no profile-specific style is applied.

name: ``streamlit.chat.default.size``

type: ``int``

default value: ``16``
"""

STREAMLIT_CHAT_DEFAULT_FONT = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.font', str, 'sans')
"""
Default chat font family key used by Streamlit chat UI.

name: ``streamlit.chat.default.font``

type: ``str``

default value: ``sans``
"""

STREAMLIT_CHAT_DEFAULT_LINE_SPACING = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.line_spacing', float, 1.5)
"""
Default chat line spacing used by Streamlit chat UI.

name: ``streamlit.chat.default.line_spacing``

type: ``float``

default value: ``1.5``
"""

STREAMLIT_CHAT_DEFAULT_ALIGNMENT = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.alignment', str, 'left')
"""
Default chat text alignment used by Streamlit chat UI.

name: ``streamlit.chat.default.alignment``

type: ``str``

default value: ``left``
"""

STREAMLIT_CHAT_DEFAULT_COLOR = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.color', str, 'inherit')
"""
Default chat text color used by Streamlit chat UI.

name: ``streamlit.chat.default.color``

type: ``str``

default value: ``inherit``
"""

STREAMLIT_CHAT_DEFAULT_CONTRAST = Property(SECTION_WEBSOCKET, 'streamlit.chat.default.contrast', str, 'medium')
"""
Default chat contrast level used by Streamlit chat UI.

name: ``streamlit.chat.default.contrast``

type: ``str``

default value: ``medium``
"""
