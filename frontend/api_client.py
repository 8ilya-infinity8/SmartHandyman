import httpx
import streamlit as st

BASE_URL = "http://localhost:8000/api/v1"


def _get_headers():
    headers = {"Content-Type": "application/json"}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def login(email: str, password: str) -> dict:
    """Perform login and return the json response (contains access_token)."""
    url = f"{BASE_URL}/auth/jwt/login"
    data = {"username": email, "password": password}
    with httpx.Client() as client:
        r = client.post(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return r.json()


def get_chats() -> list:
    url = f"{BASE_URL}/chats"
    with httpx.Client() as client:
        r = client.get(url, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def create_chat(title: str) -> dict:
    url = f"{BASE_URL}/chats"
    payload = {"title": title}
    with httpx.Client() as client:
        r = client.post(url, json=payload, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def get_messages(chat_id: int) -> list:
    url = f"{BASE_URL}/messages/chat/{chat_id}"
    with httpx.Client() as client:
        r = client.get(url, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def send_message(chat_id: int, content: str, role: str = "user") -> dict:
    url = f"{BASE_URL}/messages"
    payload = {"chat_id": chat_id, "content": content, "role": role}
    with httpx.Client() as client:
        r = client.post(url, json=payload, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def register(email: str, username: str, password: str) -> dict:
    """Create a new user account."""
    url = f"{BASE_URL}/auth/register"
    payload = {"email": email, "username": username, "password": password}
    with httpx.Client() as client:
        r = client.post(url, json=payload, headers=_get_headers())
        # registration may return 201 or similar; raise if error
        r.raise_for_status()
        return r.json()
