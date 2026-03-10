import streamlit as st
from api_client import create_chat, delete_chat, get_chats


def render_sidebar():
    # apply sidebar typography
    st.sidebar.markdown(
        """
        <style>
        div[data-testid="stSidebar"] div[data-testid="stButton"] {
            display: flex;
            justify-content: center;
        }

        div[data-testid="stSidebar"] button {
            font-size: 0.95rem;
            padding: 0.25rem 0.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # top logo area
    st.sidebar.markdown(
        """
        <div style='padding:10px; text-align:center;'>
            <h2 style='color:#10a37f; margin:0;font-size:1.3rem;'>🔧 SmartHandyman</h2>
        </div>
        <hr style='border-color:#444;' />
        """,
        unsafe_allow_html=True,
    )
    # new chat button
    if st.sidebar.button("+ New Chat", key="new-chat-btn"):
        try:
            created = create_chat("")
            # сразу активируем новый чат, как в DeepSeek
            st.session_state["chat_id"] = created.get("id")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create chat: {e}")

    # list existing chats with simplistic grouping
    # (only once below, with unique keys)
    try:
        chats = get_chats()
    except Exception as e:
        st.error(f"Unable to fetch chats: {e}")
        return

    if chats:
        st.sidebar.markdown("<hr style='border-color:#444;' />", unsafe_allow_html=True)
        st.sidebar.markdown(
            "<div style='color:#888;font-size:12px;margin:4px 0;'>Recent</div>",
            unsafe_allow_html=True,
        )

    for c in chats:
        chat_id = c.get("id")
        label = c.get("title") or f"Chat {chat_id}"
        cols = st.sidebar.columns([4, 1])
        with cols[0]:
            if st.button(label, key=f"chat-{chat_id}"):
                st.session_state["chat_id"] = chat_id
                st.rerun()
        with cols[1]:
            if st.button("✕", key=f"del-chat-{chat_id}"):
                try:
                    delete_chat(chat_id)
                    if st.session_state.get("chat_id") == chat_id:
                        st.session_state["chat_id"] = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete chat: {e}")
