import streamlit as st
from api_client import get_messages, send_message
from components.chat_message import render_message
from components.sidebar_chats import render_sidebar

st.set_page_config(page_title="Chats")

if "token" not in st.session_state or not st.session_state.get("token"):
    st.warning("Please log in first.")
    st.stop()

st.title("Chats")

render_sidebar()

chat_id = st.session_state.get("chat_id")
if chat_id:
    st.subheader(f"Chat {chat_id}")
    try:
        msgs = get_messages(chat_id)
    except Exception as e:
        st.error(f"Failed to load messages: {e}")
        msgs = []

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

    with st.form(key="message_form"):
        text = st.text_input(
            "", key="message_input", placeholder="Type your message..."
        )
        send = st.form_submit_button("Send")
        if send:
            if text.strip():
                try:
                    send_message(chat_id, text)
                except Exception as e:
                    st.error(f"Failed to send: {e}")
            else:
                st.error("Message cannot be empty")
else:
    # main area mimic deepseek empty state
    st.markdown(
        """
        <div style='text-align:center; margin-top:100px;'>
            <h1 style='color:#10a37f;'>Welcome to SmartHandyman</h1>
            <p style='color:#aaa;'>Select a chat from the sidebar or create a new one.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
