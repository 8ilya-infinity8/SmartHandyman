import streamlit as st


def render_message(msg: dict):
    """Display a single message dict with role and content using bubbles."""
    role = msg.get("role")
    content = msg.get("content")
    cls = "user" if role == "user" else "assistant"
    html = f"""
    <div class="bubble {cls}">{content}</div>
    """
    st.markdown(html, unsafe_allow_html=True)
