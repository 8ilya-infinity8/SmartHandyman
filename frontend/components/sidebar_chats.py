import streamlit as st
from api_client import create_chat, get_chats


def render_sidebar():
    # top logo area
    st.sidebar.markdown(
        """
        <div style='padding:10px; text-align:center;'>
            <h2 style='color:#10a37f; margin:0;'>🔧 SmartHandyman</h2>
        </div>
        <hr style='border-color:#444;' />
        """,
        unsafe_allow_html=True,
    )
    # new chat button
    if st.sidebar.button("+ New Chat", key="new-chat-btn"):
        try:
            created = create_chat("")
            st.success(f"Created chat '{created.get('title')}'")
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
        label = c.get("title") or f"Chat {c.get('id')}"
        # ensure unique key using chat id
        if st.sidebar.button(label, key=f"chat-{c.get('id')}"):
            st.session_state["chat_id"] = c.get("id")
            # the user must now select the "Chat" page in the sidebar
            st.info("Chat selected; open the 'Chat' page from the sidebar.")
