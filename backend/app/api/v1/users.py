from app.core.auth import fastapi_users
from app.domain.user.schemas import UserRead, UserUpdate
from fastapi import APIRouter

router = APIRouter()

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="",
    tags=["users"],
)
