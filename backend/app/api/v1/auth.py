from app.core.auth import auth_backend, fastapi_users
from app.domain.user.schemas import UserCreate, UserRead
from fastapi import APIRouter

router = APIRouter()

router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    # outer prefix is already '/api/v1/auth', so we only need '/jwt'
    prefix="/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    # registration sits directly under '/api/v1/auth'
    prefix="",
    tags=["auth"],
)
