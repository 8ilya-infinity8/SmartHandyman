import streamlit as st
from api_client import get_messages, send_message, upload_file
from components.chat_message import render_message

st.set_page_config(page_title="Chat", layout="wide")

if "token" not in st.session_state or not st.session_state.get("token"):
    st.warning("Please log in first.")
    st.stop()

chat_id = st.session_state.get("chat_id")
if not chat_id:
    st.warning("No chat selected. Please choose a chat from the chat list.")
    st.stop()

st.markdown(
    """
    <style>
    /* App background similar to ChatGPT/DeepSeek */
    .stApp {
        background-color: #050816;
    }

    /* Main chat layout */
    .chat-main-wrapper {
        max-width: 420px;
        width: min(420px, 100%);
        margin: 0 auto;
        padding: 1.5rem 1rem 6rem;
    }

    .chat-header-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e5e7eb;
        margin-bottom: 0.75rem;
    }

    .chat-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
        margin-bottom: 1.25rem;
    }

    /* Messages area */
    .chat-container {
        background: radial-gradient(circle at top left, #1f2937, #020617);
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.3);
        padding: 1.25rem 1rem;
        max-height: 65vh;
        overflow-y: auto;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.65);
        max-width: 420px;
        width: min(420px, 100%);
        margin: 0 auto;
    }

    .chat-empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #9ca3af;
    }

    .chat-empty-state h2 {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #e5e7eb;
    }

    /* Message rows and bubbles */
    .chat-row {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
        align-items: flex-start;
    }

    .user-row {
        flex-direction: row-reverse;
    }

    .avatar-circle {
        width: 32px;
        height: 32px;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        color: #e5e7eb;
        background: linear-gradient(135deg, #0ea5e9, #22c55e);
        flex-shrink: 0;
    }

    .assistant-row .avatar-circle {
        background: linear-gradient(135deg, #4b5563, #6b7280);
    }

    .chat-bubble {
        max-width: 72%;
        padding: 0.8rem 1rem;
        border-radius: 1rem;
        font-size: 1.02rem;
        line-height: 1.6;
        border: 1px solid transparent;
    }

    .assistant-bubble {
        background: rgba(15, 23, 42, 0.9);
        color: #e5e7eb;
        border-color: rgba(75, 85, 99, 0.8);
    }

    .user-bubble {
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #ecfdf3;
        border-color: rgba(34, 197, 94, 0.8);
    }

    .message-text {
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    .message-image {
        margin-top: 0.5rem;
        max-width: 260px;
        border-radius: 0.75rem;
        border: 1px solid rgba(148, 163, 184, 0.5);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }

    /* Input area fixed at bottom */
    .chat-input-wrapper {
        position: fixed;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 0.75rem 1.2rem 1.25rem;
        background: linear-gradient(to top, rgba(3, 7, 18, 0.96), rgba(3, 7, 18, 0.65));
        backdrop-filter: blur(14px);
        z-index: 999;
    }

    .chat-input-inner {
        max-width: 420px;
        width: min(420px, 100%);
        margin: 0 auto;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        justify-content: center;
    }

    .chat-input-box {
        flex: 1;
    }

    div.stTextInput>div>input {
        border-radius: 999px;
        padding: 0.7rem 1rem;
        background: #020617;
        color: #e5e7eb;
        border: 1px solid rgba(148, 163, 184, 0.6);
        font-size: 0.95rem;
    }

    div.stTextInput>div>input::placeholder {
        color: #6b7280;
    }

    .upload-label {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.15rem;
    }

    div.stButton>button {
        border-radius: 999px;
        padding: 0.55rem 1.1rem;
        font-size: 0.9rem;
        font-weight: 600;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #ecfdf3;
        border: none;
        box-shadow: 0 10px 25px rgba(34, 197, 94, 0.45);
    }

    div.stButton>button:hover {
        background: linear-gradient(135deg, #16a34a, #15803d);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="chat-main-wrapper">
        <div class="chat-header-title">Chat {chat_id}</div>
        <div class="chat-subtitle">
            Ask anything about your tasks, repairs, or ideas — I&apos;ll respond like a smart handyman assistant.
        </div>
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
        <div class="chat-empty-state">
            <h2>How can I help you today?</h2>
            <p>Describe your problem or idea in detail — I&apos;ll walk you through the best solution step by step.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.markdown("</div></div>", unsafe_allow_html=True)

with st.form(key="message_form"):
    col_input, col_file, col_send = st.columns([6, 1.5, 1])

    with col_input:
        text = st.text_input(
            "Message",
            key="message_input",
            placeholder="Message SmartHandyman...",
            label_visibility="collapsed",
        )

    with col_file:
        uploaded_file = st.file_uploader(
            "Добавить файл",
            type=["jpg", "jpeg", "png"],
        )

    attachment_url = None
    attachment_name = None
    if uploaded_file:
        attachment_name = uploaded_file.name
        try:
            result = upload_file(
                "chat-images", uploaded_file.getvalue(), uploaded_file.name
            )
            attachment_url = result.get("url")
        except Exception as e:
            st.error(f"Upload failed: {e}")

    with col_send:
        send = st.form_submit_button("Send")

    if send:
        if text.strip() or attachment_url:
            try:
                to_send = text
                if attachment_url and attachment_name:
                    # специальный маркер, который потом превращаем в бейдж
                    prefix = f"[ATTACHMENT]{attachment_name}|"
                    to_send = prefix + (text or "")
                send_message(chat_id, to_send, attachment_url=attachment_url)
            except Exception as e:
                st.error(f"Failed to send: {e}")
        else:
            st.error("Message cannot be empty")

# Render fixed input bar over the form controls
st.markdown(
    """
    <div class="chat-input-wrapper">
        <div class="chat-input-inner">
            <div class="chat-input-box">
                <!-- The actual Streamlit text_input is bound above;
                     this element only defines the layout footprint. -->
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
