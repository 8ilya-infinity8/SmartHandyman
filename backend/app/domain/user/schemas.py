from typing import Optional

from fastapi_users import schemas
from pydantic import validator


class UserRead(schemas.BaseUser[int]):
    # expose the username in read operations
    username: str


class UserCreate(schemas.BaseUserCreate):
    # users must supply a username at registration; Pydantic will refuse
    # missing or blank values.
    username: str

    @validator("username")
    def username_not_blank(cls, v):
        if not v.strip():
            raise ValueError("username cannot be blank")
        return v


class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None

    @validator("username")
    def username_not_blank(cls, v):
        if v is not None and not v.strip():
            raise ValueError("username cannot be blank")
        return v
