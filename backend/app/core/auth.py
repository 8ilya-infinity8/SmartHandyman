from typing import AsyncGenerator, Optional

from app.config import settings
from app.database.models.user import User
from app.database.session import get_async_session
from fastapi import Depends
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.context import CryptContext
from starlette.requests import Request

# ==============================
# Password Context (Argon2) - CRITICAL
# ==============================

PASSWORD_CONTEXT = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

PASSWORD_HELPER = PasswordHelper(PASSWORD_CONTEXT)

# ==============================
# JWT Transport
# ==============================

bearer_transport = BearerTransport(tokenUrl="api/v1/auth/jwt/login")


# ==============================
# JWT Strategy
# ==============================


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY,
        lifetime_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ==============================
# User DB Dependency
# ==============================


async def get_user_db(
    session=Depends(get_async_session),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, User)


# ==============================
# User Manager
# ==============================


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    def __init__(self, user_db: SQLAlchemyUserDatabase):
        super().__init__(user_db)
        # CRITICAL: Override the password_helper to use argon2
        self.password_helper = PASSWORD_HELPER

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ):
        print(f"User {user.email} has registered.")


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


# ==============================
# FastAPI Users Instance
# ==============================

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user()
