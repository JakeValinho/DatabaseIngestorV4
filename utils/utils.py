import streamlit as st

def log(message):
    """Simple logger that stores messages in Streamlit session."""
    if "log_messages" not in st.session_state:
        st.session_state.log_messages = []
    st.session_state.log_messages.append(message)

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be used as a filename by removing problematic characters.
    
    Args:
        name (str): The string to sanitize
        
    Returns:
        str: A sanitized string safe for use in filenames
    """
    # Remove quotes
    safe_name = name.replace("'", "").replace('"', "")
    # Keep only alphanumeric characters and certain safe symbols
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c in (' ', '-', '_'))
    # Remove trailing whitespace
    return safe_name.rstrip()
