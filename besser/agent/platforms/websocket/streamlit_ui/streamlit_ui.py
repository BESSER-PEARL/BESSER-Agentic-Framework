import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import streamlit as st
from streamlit.web import cli as stcli

from besser.agent.platforms.websocket.streamlit_ui.chat import load_chat
from besser.agent.platforms.websocket.streamlit_ui.initialization import initialize
from besser.agent.platforms.websocket.streamlit_ui.message_input import message_input
from besser.agent.platforms.websocket.streamlit_ui.sidebar import sidebar
from besser.agent.platforms.websocket.streamlit_ui.login import login_page
from besser.agent.platforms.websocket.streamlit_ui.user_profile import user_profile


def main():
    if not st.session_state.get("authenticated", False):
        login_page()
        # If login was successful, rerun the app to load main page
        if st.session_state.get("authenticated", False):
            st.rerun()
        st.stop()

    st.title("Welcome to the Agent Platform")

    if "page" not in st.session_state:
        st.session_state["page"] = None
    # Control whether to display the initial choice buttons
    st.session_state.setdefault("show_choices", True)

    if st.session_state["page"] is None and st.session_state.get("show_choices", True):
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Edit Your User Profile"):
                st.session_state["page"] = "user_profile"
                st.session_state["show_choices"] = False
                # Force an immediate rerun so the choice buttons disappear
                st.rerun()

        with col2:
            if st.button("Chat with Agent"):
                st.session_state["page"] = "chat"
                st.session_state["show_choices"] = False
                # Force an immediate rerun so the choice buttons disappear
                st.rerun()

    if st.session_state["page"] == "user_profile":
        if user_profile():  # Assuming user_profile returns True when changes are saved
            st.session_state["page"] = None
            st.session_state["show_choices"] = True
            # Rerun to update UI (show the choice buttons again)
            st.rerun()
    elif st.session_state["page"] == "chat":
        try:
            # We get the agent name from the script arguments
            agent_name = sys.argv[1]
        except Exception:
            # If it is not provided, use a default value
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
