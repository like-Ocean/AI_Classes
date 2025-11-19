from typing import List
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from models import User, Module, Material, MaterialFile
from schemas.course import MaterialCreateRequest, MaterialUpdateRequest
from service.course_service import check_course_access
from helpers.files.files_helper import (
    get_files, get_material, load_material_files_with_relations,
    process_files, update_material_content
)


async def create_material(
        course_id: int, module_id: int,
        data: MaterialCreateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Module).where(
            and_(Module.id == module_id, Module.course_id == course_id)
        )
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found in this course"
        )

    material = Material(
        module_id=module_id,
        type=data.type,
        title=data.title,
        content_url=data.content_url,
        text_content=None,
        transcript=None,
        position=data.position
    )

    db.add(material)
    await db.commit()
    await db.refresh(material)

    return material


async def update_material(
        course_id: int, module_id: int,
        material_id: int,
        data: MaterialUpdateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .join(Module)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module"
        )

    if data.type is not None:
        material.type = data.type
    if data.title is not None:
        material.title = data.title
    if data.content_url is not None:
        material.content_url = data.content_url
    if data.text_content is not None:
        material.text_content = data.text_content
    if data.transcript is not None:
        material.transcript = data.transcript
    if data.position is not None:
        material.position = data.position

    await db.commit()
    await db.refresh(material)

    return material


async def delete_material(
        course_id: int, module_id: int,
        material_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .join(Module)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module"
        )

    await db.delete(material)
    await db.commit()


async def attach_files_to_material(
        course_id: int, module_id: int,
        material_id: int, file_ids: List[int],
        user: User, db: AsyncSession
):
    """Прикрепление файлов с автоматическим извлечением текста"""
    print(f"🔵 ATTACH FILES TO MATERIAL")
    print(f"Material ID: {material_id}, File IDs: {file_ids}")
    print(f"{'=' * 60}\n")

    await check_course_access(course_id, user, db)
    material = await get_material(db, material_id, module_id, course_id)
    files = await get_files(db, file_ids)
    material_files, extracted_texts, transcriptions = await process_files(
        db, material_id, files
    )
    if extracted_texts or transcriptions:
        await update_material_content(
            material, extracted_texts, transcriptions
        )
    await db.commit()
    await db.refresh(material)

    return await load_material_files_with_relations(db, material_files)


async def detach_file_from_material(
        course_id: int, module_id: int,
        material_id: int, file_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .join(Module)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module"
        )

    result = await db.execute(
        select(MaterialFile).where(
            and_(
                MaterialFile.material_id == material_id,
                MaterialFile.file_id == file_id
            )
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
