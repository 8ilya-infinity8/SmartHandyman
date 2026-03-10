import os
import uuid

from app.api.deps import get_current_user, get_db
from app.database.models.storage_object import StorageObject
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/storage", tags=["storage"])

BASE_BUCKET_DIR = "/app/backend/buckets"
os.makedirs(BASE_BUCKET_DIR, exist_ok=True)


async def ensure_bucket(bucket: str) -> str:
    if "/" in bucket or ".." in bucket:
        raise HTTPException(400, "Invalid bucket name")

    path = os.path.join(BASE_BUCKET_DIR, bucket)
    os.makedirs(path, exist_ok=True)
    return path


@router.post("/upload")
async def upload_file(
    bucket: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bucket_path = await ensure_bucket(bucket)

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(bucket_path, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    obj = StorageObject(
        bucket=bucket,
        name=filename,
        content_type=file.content_type,
        # сохраняем абсолютный путь в БД для совместимости со старой схемой
        # и чтобы выполнить not-null constraint на колонке path
        path=file_path,
        owner_id=user.id,
    )

    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return {
        "id": obj.id,
        "url": f"/api/v1/storage/object/{obj.id}",
    }


@router.get("/object/{object_id}")
async def get_object(
    object_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(StorageObject).where(StorageObject.id == object_id)
    )

    obj = result.scalar_one_or_none()

    if not obj:
        raise HTTPException(404, "Object not found")

    file_path = os.path.join(BASE_BUCKET_DIR, obj.bucket, obj.name)

    if not os.path.exists(file_path):
        raise HTTPException(404, "File missing on disk")

    return FileResponse(file_path, media_type=obj.content_type)
