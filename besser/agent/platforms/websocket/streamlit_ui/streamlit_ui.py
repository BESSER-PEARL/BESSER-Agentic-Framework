import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path
import os

import streamlit as st
from streamlit.runtime import Runtime
from streamlit.web import cli as stcli

from besser.agent.platforms.websocket.streamlit_ui.chat import load_chat
from besser.agent.platforms.websocket.streamlit_ui.initialization import initialize
from besser.agent.platforms.websocket.streamlit_ui.message_input import message_input
from besser.agent.platforms.websocket.streamlit_ui.sidebar import sidebar
from besser.agent.platforms.websocket.streamlit_ui.login import login_page


def main():
    # Check STREAMLIT_DB environment variable. If it's set to a truthy value
    # ('1', 'true', 'yes'), keep the normal login flow. If it's not set or
    # set to a non-true value, skip the login page and proceed directly to
    # the main app UI.
    streamlit_db_enabled = str(os.environ.get("STREAMLIT_DB", "")).lower() in ("true", "1", "yes", "on")

    if streamlit_db_enabled:
        # Normal behavior: require authentication via login_page
        if not st.session_state.get("authenticated", False):
            login_page()
            # If login was successful, rerun the app to load main page
            if st.session_state.get("authenticated", False):
                st.rerun()
            st.stop()
    try:
        # We get the websocket host and port from the script arguments
        agent_name = sys.argv[1]
    except Exception as e:
        # If they are not provided, we use default values
        agent_name = 'Agent Demo'
    st.header(agent_name)
    st.markdown("[Github](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework)")

    initialize()
    sidebar()
    load_chat()
    message_input()
    st.stop()


if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
