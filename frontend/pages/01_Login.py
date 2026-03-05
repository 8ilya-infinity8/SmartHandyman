import streamlit as st
from api_client import login

# inject a bit of ChatGPT-like dark styling
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
st.title("Smart Handyman - Login")

if "token" in st.session_state and st.session_state["token"]:
    st.success("You are already logged in.")
    st.write("Go to Chat List page using the sidebar.")
else:
    st.markdown(
        """
        <div style='max-width:400px; margin:auto; padding:20px; border:1px solid #333; border-radius:8px;'>
        """,
        unsafe_allow_html=True,
    )
    email = st.text_input("Email")
    username = st.text_input("Username (if you already have one)")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        try:
            resp = login(email, password)
            token = resp.get("access_token")
            if token:
                st.session_state["token"] = token
                st.success(
                    "Login successful! Navigate to the Chat List page using the sidebar."
                )
            else:
                st.error("Login response did not contain token.")
        except Exception as e:
            st.error(f"Login failed: {e}")
    st.markdown("---")
    st.write("Don't have an account? Select the **Register** page from the sidebar.")
    st.markdown("</div>", unsafe_allow_html=True)
