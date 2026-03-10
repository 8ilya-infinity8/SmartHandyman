import streamlit as st

# Минимальный root-скрипт: редиректим на страницу логина.
st.set_page_config(
    page_title="Smart Handyman",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* Скрываем служебные страницы app, Login, Register
       в стандартном навигационном меню Streamlit.
       Порядок элементов: app, Login, Register, Chat List, Chat. */
    div[data-testid="stSidebarNav"] ul li:nth-child(1),
    div[data-testid="stSidebarNav"] ul li:nth-child(2),
    div[data-testid="stSidebarNav"] ul li:nth-child(3) {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.switch_page("pages/00_Login.py")
