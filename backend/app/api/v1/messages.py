from typing import List

from app.api.deps import get_current_user, get_db
from app.database.models.chat import Chat
from app.database.models.message import Message
from app.database.models.user import User
from app.domain.chat.message_dto import MessageCreate, MessageRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("/chat/{chat_id}", response_model=List[MessageRead])
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404)

    if chat.owner_id != user.id:
        raise HTTPException(status_code=403)

    result = await db.execute(
        select(Message).where(Message.chat_id == chat_id).order_by(Message.created_at)
    )

    return result.scalars().all()


@router.post("", response_model=MessageRead)
async def create_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    chat_result = await db.execute(select(Chat).where(Chat.id == message.chat_id))
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404)

    if chat.owner_id != user.id:
        raise HTTPException(status_code=403)

    new_message = Message(
        chat_id=message.chat_id,
        role=message.role,
        content=message.content,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    return new_message
