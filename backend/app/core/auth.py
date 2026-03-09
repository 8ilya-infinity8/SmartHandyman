from typing import AsyncGenerator, Optional

from app.config import settings
from app.database.models.user import User
from app.database.session import get_async_session
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin, exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.password import PasswordHelper
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from passlib.context import CryptContext
from starlette.requests import Request

PASSWORD_CONTEXT = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
)

PASSWORD_HELPER = PasswordHelper(PASSWORD_CONTEXT)


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
        self.password_helper = PASSWORD_HELPER

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None,
    ):
        print(f"User {user.email} has registered.")

    async def create(self, user_create, safe: bool = False, **kwargs):
        username = getattr(user_create, "username", None)
        if not username or not username.strip():
            raise ValueError("username must be provided")
        return await super().create(user_create, safe=safe, **kwargs)

    async def update(self, user: User, update_dict: dict, **kwargs):
        if "username" in update_dict and not update_dict["username"]:
            raise ValueError("username cannot be empty")
        return await super().update(user, update_dict, **kwargs)

    async def authenticate(
        self, credentials: OAuth2PasswordRequestForm
    ) -> Optional[User]:
        """Support login using either email or username."""
        user = None
        # try email lookup first; some backends raise UserNotExists, others
        # return None, so handle both cases.
        user = None
        try:
            user = await self.user_db.get_by_email(credentials.username)
        except exceptions.UserNotExists:
            user = None

        # if email lookup didn't yield a user, attempt username lookup by
        # building the same kind of SQLAlchemy statement used in
        # ``SQLAlchemyUserDatabase.get_by_email``.
        if user is None:
            # avoid importing sqlalchemy at the top; do it lazily here
            from sqlalchemy import func, select

            statement = select(self.user_db.user_table).where(
                func.lower(self.user_db.user_table.username)
                == func.lower(credentials.username)
            )
            user = await self.user_db._get_user(statement)

        if user is None:
            # no user found by either identifier; dummy hash to mitigate
            # timing attacks and return.
            self.password_helper.hash(credentials.password)
            return None

        verified, updated_hash = self.password_helper.verify_and_update(
            credentials.password, user.hashed_password
        )
        if not verified:
            return None
        if updated_hash is not None:
            await self.user_db.update(user, {"hashed_password": updated_hash})
        return user


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
