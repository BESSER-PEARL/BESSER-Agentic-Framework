
import streamlit as st
from besser.agent.platforms.websocket.streamlit_ui.user_db import UserDB

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if 'db' not in st.session_state:
        st.session_state['db'] = UserDB()
    db = st.session_state['db']
    col1, col2 = st.columns(2)
    login_clicked = col1.button("Login")
    guest_clicked = col2.button("Continue as Guest")
    if login_clicked:
        if not username or not password:
            st.error("Please enter both username and password.")
        elif db.user_exists(username):
            if db.authenticate(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Login successful!")
            else:
                st.error("Incorrect password for this username.")
        else:
            # Create new user
            db.add_user(username, password)
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Account created and logged in!")
    if guest_clicked:
        st.session_state["authenticated"] = True
        st.success("Continuing as Guest")