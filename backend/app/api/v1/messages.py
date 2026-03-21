import base64
from typing import List

from app.api.deps import get_current_user, get_db
from app.api.v1.assistant import RepairRequest, run_repair_assistant
from app.database.models.chat import Chat
from app.database.models.message import Message
from app.database.models.storage import StorageObject
from app.database.models.user import User
from app.domain.chat.message_dto import MessageCreate, MessageRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/messages", tags=["messages"])


async def load_image_base64_from_storage(
    db: AsyncSession,
    attachment_url: str,
):
    try:
        object_id = int(attachment_url.split("/")[-1])

        result = await db.execute(
            select(StorageObject).where(StorageObject.id == object_id)
        )

        obj = result.scalar_one_or_none()

        if not obj:
            return None

        with open(obj.path, "rb") as f:
            data = f.read()

        return base64.b64encode(data).decode()

    except Exception:
        return None


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
    """
    Создание нового сообщения и автоматический вызов ассистента
    для сообщений от пользователя.
    Поддерживает картинки (attachment_url) и показывает "⏳ Thinking..." в чате.
    """
    # --- 1. Проверка чата ---
    chat_result = await db.execute(select(Chat).where(Chat.id == message.chat_id))
    chat = chat_result.scalar_one_or_none()

    if not chat:
        raise HTTPException(status_code=404)

    if chat.owner_id != user.id:
        raise HTTPException(status_code=403)

    # --- 2. Сохраняем сообщение пользователя ---
    new_message = Message(
        chat_id=message.chat_id,
        role=message.role,
        content=message.content,
        attachment_url=message.attachment_url,
    )

    db.add(new_message)
    await db.commit()
    await db.refresh(new_message)

    # --- 3. Подготовка картинки (если есть) ---
    image_base64 = None
    if message.attachment_url:
        image_base64 = await load_image_base64_from_storage(db, message.attachment_url)

    # --- 4. Если это сообщение пользователя, вызываем ассистента ---
    if message.role == "user":
        # 4a. Вставляем временное сообщение "Thinking..."
        assistant_message = Message(
            chat_id=message.chat_id, role="assistant", content="⏳ Thinking..."
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        # 4b. Подготавливаем payload для ассистента
        assistant_payload = RepairRequest(
            question=message.content, image_base64=image_base64, qa=None
        )

        # 4c. Вызываем ассистента
        assistant_response = await run_repair_assistant(assistant_payload, user=user)

        # 4d. Превращаем ответ ассистента в текст для чата
        instructions = getattr(assistant_response, "instructions", {})
        shopping = getattr(assistant_response, "shopping", {"list": []})

        assistant_text = ""

        if "steps" in instructions:
            assistant_text += "🔧 Инструкция:\n"
            for i, step in enumerate(instructions["steps"], 1):
                assistant_text += f"{i}. {step}\n"

        if shopping.get("list"):
            assistant_text += "\n🛒 Что понадобится:\n"
            for item in shopping["list"]:
                assistant_text += f"- {item.get('name', 'товар')}\n"

        assistant_message.content = assistant_text
        await db.commit()
        await db.refresh(assistant_message)

    return new_message
