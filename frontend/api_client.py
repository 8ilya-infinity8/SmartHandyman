import os

import httpx
import streamlit as st

# Базовый URL backend-а читаем из переменной окружения, чтобы в Docker
# фронт умел ходить на сервис "backend", а локально — на localhost.
BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")


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


def delete_chat(chat_id: int) -> None:
    """Delete a chat owned by the current user."""
    url = f"{BASE_URL}/chats/{chat_id}"
    with httpx.Client() as client:
        r = client.delete(url, headers=_get_headers())
        r.raise_for_status()


def get_messages(chat_id: int) -> list:
    url = f"{BASE_URL}/messages/chat/{chat_id}"
    with httpx.Client() as client:
        r = client.get(url, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def send_message(
    chat_id: int, content: str, role: str = "user", attachment_url: str | None = None
) -> dict:
    url = f"{BASE_URL}/messages"
    payload = {"chat_id": chat_id, "content": content, "role": role}
    if attachment_url:
        payload["attachment_url"] = attachment_url
    with httpx.Client() as client:
        r = client.post(url, json=payload, headers=_get_headers())
        r.raise_for_status()
        return r.json()


def upload_file(bucket: str, file_bytes: bytes, filename: str) -> dict:
    """Upload raw bytes to a bucket. Returns object metadata with a URL."""
    url = f"{BASE_URL}/storage/upload"
    files = {"file": (filename, file_bytes)}
    data = {"bucket": bucket}
    # For multipart uploads we must NOT force "Content-Type: application/json",
    # otherwise FastAPI cannot parse the form-data and returns 422.
    # Build auth headers manually without content-type so httpx sets it.
    headers = {}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client() as client:
        r = client.post(url, files=files, data=data, headers=headers)
        r.raise_for_status()
        return r.json()


def list_bucket(bucket: str) -> list:
    url = f"{BASE_URL}/storage/list/{bucket}"
    with httpx.Client() as client:
        r = client.get(url, headers=_get_headers())
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
