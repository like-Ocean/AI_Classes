import os
import hashlib
import aiofiles
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile, HTTPException, status
from typing import List
from models import File, MaterialFile, Material
from core.config import settings


def get_file_hash(content: bytes):
    return hashlib.sha256(content).hexdigest()


def get_unique_filename(original_filename: str, file_hash: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = Path(original_filename).suffix
    return f"{timestamp}_{file_hash[:16]}{ext}"


async def validate_file(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension {ext} is not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    file_size = 0
    chunk_size = 1024 * 1024

    await file.seek(0)
    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024 * 1024)} MB"
            )

    await file.seek(0)


async def save_file(file: UploadFile, db: AsyncSession) -> File:
    await validate_file(file)

    content = await file.read()
    await file.seek(0)

    file_hash = get_file_hash(content)

    result = await db.execute(
        select(File).where(File.file_hash == file_hash)
    )
    existing_file = result.scalar_one_or_none()

    if existing_file:
        return existing_file

    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)

    unique_filename = get_unique_filename(file.filename, file_hash)
    file_path = upload_path / unique_filename

    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    db_file = File(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=str(file_path),
        file_url=f"/uploads/{unique_filename}",
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        file_hash=file_hash
    )

    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return db_file


async def attach_files_to_material(
        material_id: int,
        file_ids: List[int],
        db: AsyncSession
):
    result = await db.execute(
        select(Material).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    result = await db.execute(
        select(File).where(File.id.in_(file_ids))
    )
    files = result.scalars().all()

    if len(files) != len(file_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some files not found"
        )

    material_files = []
    for file_id in file_ids:
        existing = await db.execute(
            select(MaterialFile).where(
                MaterialFile.material_id == material_id,
                MaterialFile.file_id == file_id
            )
        )
        if existing.scalar_one_or_none():
            continue

        material_file = MaterialFile(
            material_id=material_id,
            file_id=file_id
        )
        db.add(material_file)
        material_files.append(material_file)

    await db.commit()

    for mf in material_files:
        await db.refresh(mf)

    return material_files


async def detach_file_from_material(
        material_id: int,
        file_id: int,
        db: AsyncSession
):
    result = await db.execute(
        select(MaterialFile).where(
            MaterialFile.material_id == material_id,
            MaterialFile.file_id == file_id
        )
    )
    material_file = result.scalar_one_or_none()

    if not material_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not attached to this material"
        )

    await db.delete(material_file)
    await db.commit()


async def delete_file(file_id: int, db: AsyncSession):
    result = await db.execute(
        select(File).where(File.id == file_id)
    )
    file = result.scalar_one_or_none()

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    result = await db.execute(
        select(MaterialFile).where(MaterialFile.file_id == file_id)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete file that is attached to materials"
        )

    file_path = Path(file.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.delete(file)
    await db.commit()
