from besser.agent.core.property import Property

WEBSOCKET_HOST = Property('platforms.websocket.host', str, 'localhost')
"""
The WebSocket host address. An agent has a WebSocket server that has to establish connection with a WebSocket client.

name: ``websocket.host``

type: ``str``

default value: ``localhost``
"""

WEBSOCKET_PORT = Property('platforms.websocket.port', int, 8765)
"""
The WebSocket address port. The WebSocket address is composed by a host name and a port

name: ``websocket.port``

type: ``int``

default value: ``8765``
"""

WEBSOCKET_MAX_SIZE = Property('platforms.websocket.max_size', int, None)
"""
WebSocket's maximum size of incoming messages, in bytes. :obj:`None` disables the limit.

name: ``platformswebsocket.max_size``

type: ``int``

default value: ``None``
"""

STREAMLIT_HOST = Property('platforms.websocket.streamlit.host', str, 'localhost')
"""
The Streamlit UI host address. If you are using our default UI, you must define its address where you can access and 
interact with the agent.

name: ``streamlit.host``

type: ``str``

default value: ``localhost``
"""

STREAMLIT_PORT = Property('platforms.websocket.streamlit.port', int, 5000)
"""
The Streamlit UI address port. The Streamlit UI address is composed by a host name and a port

name: ``streamlit.port``

type: ``int``

default value: ``5000``
"""

STREAMLIT_CHAT_DEFAULT_SIZE = Property('platforms.websocket.streamlit.chat.size', int, 16)
"""
Default chat font size used by Streamlit chat UI when no profile-specific style is applied.

name: ``streamlit.chat.size``

type: ``int``

default value: ``16``
"""

STREAMLIT_CHAT_DEFAULT_FONT = Property('platforms.websocket.streamlit.chat.font', str, 'sans')
"""
Default chat font family key used by Streamlit chat UI.

name: ``streamlit.chat.font``

type: ``str``

default value: ``sans``
"""

STREAMLIT_CHAT_DEFAULT_LINE_SPACING = Property('platforms.websocket.streamlit.chat.line_spacing', float, 1.5)
"""
Default chat line spacing used by Streamlit chat UI.

name: ``streamlit.chat.line_spacing``

type: ``float``

default value: ``1.5``
"""

STREAMLIT_CHAT_DEFAULT_ALIGNMENT = Property('platforms.websocket.streamlit.chat.alignment', str, 'left')
"""
Default chat text alignment used by Streamlit chat UI.

name: ``streamlit.chat.alignment``

type: ``str``

default value: ``left``
"""

STREAMLIT_CHAT_DEFAULT_COLOR = Property('platforms.websocket.streamlit.chat.color', str, 'inherit')
"""
Default chat text color used by Streamlit chat UI.

name: ``streamlit.chat.color``

type: ``str``

default value: ``inherit``
"""

STREAMLIT_CHAT_DEFAULT_CONTRAST = Property('platforms.websocket.streamlit.chat.contrast', str, 'medium')
"""
Default chat contrast level used by Streamlit chat UI.

name: ``streamlit.chat.contrast``

type: ``str``

default value: ``medium``
"""
