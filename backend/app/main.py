from fastapi import FastAPI

from app.api.v1 import auth, chats, messages, users

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1/users")
