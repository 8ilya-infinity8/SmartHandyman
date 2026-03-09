from typing import List

from app.api.deps import get_current_user, get_db
from app.database.models.chat import Chat
from app.database.models.user import User
from app.domain.chat.dto import ChatCreate, ChatRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=List[ChatRead])
async def get_chats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.owner_id == user.id))
    return result.scalars().all()


@router.post("", response_model=ChatRead)
async def create_chat(
    chat: ChatCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    new_chat = Chat(
        title=chat.title or "Новый чат",
        owner_id=user.id,
    )

    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)

    return new_chat


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Chat).where(Chat.id == chat_id))
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if chat.owner_id != user.id:
        raise HTTPException(status_code=403)

    await db.delete(chat)
    await db.commit()

    return {"status": "deleted"}
