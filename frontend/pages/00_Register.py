import streamlit as st
from api_client import register

# dark chat-like theme
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #343541;
    }
    div.stButton>button {
        background-color: #10a37f;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Smart Handyman - Register")

if "token" in st.session_state and st.session_state.get("token"):
    st.success("You are already logged in.")
    st.write("Use the sidebar to go to the chat list.")
else:
    # simple styled box similar to login page
    st.markdown(
        """
        <div style='max-width:400px; margin:auto; padding:20px; border:1px solid #333; border-radius:8px;'>
        """,
        unsafe_allow_html=True,
    )
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    password2 = st.text_input("Confirm password", type="password")
    if st.button("Register"):
        if not email or not username or not password:
            st.error("All fields are required.")
        elif password != password2:
            st.error("Passwords do not match.")
        else:
            try:
                resp = register(email, username, password)
                st.success(
                    "Registration successful! You can now log in by selecting the Login page from the sidebar."
                )
            except Exception as e:
                st.error(f"Registration failed: {e}")
    st.markdown("</div>", unsafe_allow_html=True)
