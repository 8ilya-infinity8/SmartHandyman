import streamlit as st
from api_client import get_messages, send_message
from components.chat_message import render_message

st.set_page_config(page_title="Chat")

if "token" not in st.session_state or not st.session_state.get("token"):
    st.warning("Please log in first.")
    st.stop()

chat_id = st.session_state.get("chat_id")
if not chat_id:
    st.warning("No chat selected. Please choose a chat from the chat list.")
    st.stop()

st.title(f"Chat {chat_id}")

st.markdown(
    """
    <style>
    div.stTextInput>div>input {
        border-radius: 20px;
        padding: 12px;
        background: #40414f;
        color: #fff;
    }
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        padding: 10px;
        background: #363740;
        border-radius: 10px;
    }
    div.stButton>button.chat-send {
        background-color: #10a37f !important;
        color: white !important;
        border-radius: 20px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    msgs = get_messages(chat_id)
except Exception as e:
    st.error(f"Failed to load messages: {e}")
    msgs = []

st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
if msgs:
    for m in msgs:
        render_message(m)
else:
    st.markdown(
        """
        <div style='text-align:center; color:#bbb; margin-top:40px;'>
            <h2>How can I help you?</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

with st.form(key="message_form"):
    text = st.text_input("", key="message_input", placeholder="Type your message...")
    send = st.form_submit_button("Send")
    if send:
        if text.strip():
            try:
                send_message(chat_id, text)
            except Exception as e:
                st.error(f"Failed to send: {e}")
        else:
            st.error("Message cannot be empty")
