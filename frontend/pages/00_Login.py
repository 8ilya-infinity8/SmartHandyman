import streamlit as st
from api_client import login

st.set_page_config(
    page_title="SmartHandyman - Login",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #050816;
        color: #e5e7eb;
    }
    .login-card {
        max-width: 420px;
        margin: 7vh auto 0;
        padding: 2rem 1.6rem 1.5rem;
        border-radius: 18px;
        background: radial-gradient(circle at top left, #111827, #020617);
        border: 1px solid rgba(148, 163, 184, 0.35);
        box-shadow: 0 24px 65px rgba(0, 0, 0, 0.9);
    }
    .login-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
        text-align: center;
        color: #e5e7eb;
    }
    .login-subtitle {
        font-size: 0.9rem;
        color: #9ca3af;
        text-align: center;
        margin-bottom: 1.4rem;
    }
    div.stButton>button {
        width: 100%;
        border-radius: 999px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: #ecfdf3;
        border: none;
        box-shadow: 0 12px 30px rgba(34, 197, 94, 0.55);
    }
    div.stButton>button:hover {
        background: linear-gradient(135deg, #16a34a, #15803d);
    }
    .login-footer {
        margin-top: 1.2rem;
        font-size: 0.9rem;
        text-align: center;
        color: #9ca3af;
    }
    .login-footer a {
        color: #22c55e;
        text-decoration: none;
        font-weight: 500;
    }
    .login-footer a:hover {
        text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="login-card">
        <div class="login-title">SmartHandyman</div>
        <div class="login-subtitle">Sign in to start chatting with your handyman assistant.</div>
    """,
    unsafe_allow_html=True,
)

if "token" in st.session_state and st.session_state.get("token"):
    st.success("You are already logged in. Open the Chats page from the sidebar.")
else:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        try:
            resp = login(email, password)
            token = resp.get("access_token")
            if token:
                st.session_state["token"] = token
                st.success("Login successful! Open the Chats page from the sidebar.")
            else:
                st.error("Login response did not contain token.")
        except Exception as e:
            st.error(f"Login failed: {e}")

st.markdown(
    """
        <div class="login-footer">
            Впервые тут?
            <a href="/Register">зарегистрируйтесь</a>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

