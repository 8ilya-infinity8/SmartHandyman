import streamlit as st

# This file is kept for reference; Streamlit will automatically scan
# the pages/ directory and create a multi-page app.  You can use this
# file to set configuration or global state.

st.set_page_config(
    page_title="Smart Handyman",
    layout="wide",
)

# global CSS for dark "chat" theme with sliding sidebar
st.markdown(
    """
    <style>
    /* dark background */
    .reportview-container, .main {
        background-color: #343541;
        color: #ffffff;
    }
    div.stButton>button {
        background-color: #10a37f;
        color: white;
    }
    /* sidebar styling (use data-testid for stability) */
    div[data-testid="stSidebar"] {
        background-color: #202123;
        transition: transform 0.3s ease-in-out;
        width: 300px;
        position: fixed;
        left: 0;
        top: 0;
        bottom: 0;
        transform: translateX(-250px);
        z-index: 1000;
    }
    /* expand on hover */
    div[data-testid="stSidebar"]:hover {
        transform: translateX(0);
    }
    
    /* chat input style */
    .chat-input {
        width: 100%;
        padding: 12px;
        border-radius: 20px;
        border: none;
        box-shadow: 0 0 5px rgba(0,0,0,0.2);
        background: #40414f;
        color: #fff;
    }
    .chat-send {
        background-color: #10a37f !important;
        color: white !important;
        border-radius: 20px !important;
    }
    /* message bubbles */
    .bubble {
        padding: 10px 15px;
        border-radius: 18px;
        margin: 5px 0;
        max-width: 70%;
        display: inline-block;
        clear: both;
    }
    .bubble.user {background-color: #10a37f; color: #fff; float: right;}
    .bubble.assistant {background-color: #444654; color: #fff; float: left;}
    /* sidebar hover expand */
    .css-k1ih3n:hover {transform: translateX(0);}
    .css-k1ih3n {transform: translateX(-250px);}
    </style>
    """,
    unsafe_allow_html=True,
)

st.write("Welcome to Smart Handyman frontend. Use the sidebar to navigate.")
