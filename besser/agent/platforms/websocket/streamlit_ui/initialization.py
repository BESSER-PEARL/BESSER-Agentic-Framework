import queue
import sys
import threading

import streamlit as st
import websocket
from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx

from besser.agent.platforms.websocket.streamlit_ui.session_management import session_monitoring
from besser.agent.platforms.websocket.streamlit_ui.vars import (
    SESSION_MONITORING_INTERVAL,
    SUBMIT_TEXT,
    HISTORY,
    QUEUE,
    WEBSOCKET,
    SESSION_MONITORING,
    SUBMIT_AUDIO,
    SUBMIT_FILE,
    WS_HOST,
    WS_PORT,
    WEBSOCKET_READY,
)
from besser.agent.platforms.websocket.streamlit_ui.websocket_callbacks import (
    on_open,
    on_error,
    on_message,
    on_close,
    on_ping,
    on_pong,
)


def _resolve_host_port():
    try:
        host = sys.argv[2]
        port = sys.argv[3]
    except Exception:
        host = 'localhost'
        port = '8765'
    return host, port


def _start_websocket(host: str, port: str):
    try:
        if st.session_state.get("username"):
            ws = websocket.WebSocketApp(
                f"ws://{host}:{port}/",
                header={"X-User-ID": st.session_state["username"]},
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_ping=on_ping,
                on_pong=on_pong,
            )
        else:
            ws = websocket.WebSocketApp(
                f"ws://{host}:{port}/",
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_ping=on_ping,
                on_pong=on_pong,
            )
        websocket_thread = threading.Thread(target=ws.run_forever)
        add_script_run_ctx(websocket_thread)
        websocket_thread.start()
        st.session_state[WEBSOCKET] = ws
        st.session_state[WEBSOCKET_READY] = False
        return ws
    except Exception as exc:
        st.error(
            f"Could not connect to the WebSocket server at ws://{host}:{port}/. "
            "Please ensure the server is running and the host and port are correct."
        )
        print(f"WebSocket connection error: {exc}")
        return None


def ensure_websocket_connection(force_reconnect: bool = False):
    if force_reconnect and WEBSOCKET in st.session_state:
        ws = st.session_state.get(WEBSOCKET)
        if ws:
            try:
                ws.close()
            except Exception as exc:
                # Ignore errors when closing the websocket, as it may already be closed or invalid.
                print(f"Error closing websocket: {exc}")
        st.session_state.pop(WEBSOCKET, None)
        st.session_state[WEBSOCKET_READY] = False

    ws = st.session_state.get(WEBSOCKET)
    if ws:
        sock = getattr(ws, 'sock', None)
        if sock and sock.connected:
            return ws

    host = st.session_state.get(WS_HOST)
    port = st.session_state.get(WS_PORT)
    if not host or not port:
        host, port = _resolve_host_port()
        st.session_state[WS_HOST] = host
        st.session_state[WS_PORT] = port

    return _start_websocket(host, port)


def reconnect_websocket():
    return ensure_websocket_connection(force_reconnect=True)


def initialize():
    if SUBMIT_TEXT not in st.session_state:
        st.session_state[SUBMIT_TEXT] = False

    if SUBMIT_AUDIO not in st.session_state:
        st.session_state[SUBMIT_AUDIO] = False

    if SUBMIT_FILE not in st.session_state:
        st.session_state[SUBMIT_FILE] = False

    if HISTORY not in st.session_state:
        st.session_state[HISTORY] = []

    if QUEUE not in st.session_state:
        st.session_state[QUEUE] = queue.Queue()

    if "fetched_user_messages" not in st.session_state:
        st.session_state["fetched_user_messages"] = False

    if WEBSOCKET_READY not in st.session_state:
        st.session_state[WEBSOCKET_READY] = False

    if WS_HOST not in st.session_state or WS_PORT not in st.session_state:
        host, port = _resolve_host_port()
        st.session_state[WS_HOST] = host
        st.session_state[WS_PORT] = port

    if WEBSOCKET not in st.session_state:
        ensure_websocket_connection()
    if SESSION_MONITORING not in st.session_state:
        session_monitoring_thread = threading.Thread(target=session_monitoring,
                                                     kwargs={'interval': SESSION_MONITORING_INTERVAL})
        add_script_run_ctx(session_monitoring_thread)
        session_monitoring_thread.start()
        st.session_state[SESSION_MONITORING] = session_monitoring_thread
