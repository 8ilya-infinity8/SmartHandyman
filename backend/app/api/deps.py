from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_async_session
from app.database.models.user import User
from app.core.auth import current_user


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


async def get_current_user(user: User = Depends(current_user)) -> User:
    return user
