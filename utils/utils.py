import streamlit as st

def log(message):
    """Simple logger that stores messages in Streamlit session."""
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    st.session_state.log_messages.append(message)
