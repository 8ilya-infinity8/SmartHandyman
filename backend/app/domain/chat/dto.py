from datetime import datetime

from pydantic import BaseModel


class ChatCreate(BaseModel):
    title: str | None = None


class ChatRead(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
