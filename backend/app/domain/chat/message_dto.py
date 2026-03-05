from datetime import datetime

from pydantic import BaseModel


class MessageCreate(BaseModel):
    chat_id: int
    content: str
    role: str = "user"


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    chat_id: int

    class Config:
        from_attributes = True
