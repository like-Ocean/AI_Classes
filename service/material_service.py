from typing import List
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from models import User, Module, Material, File, MaterialFile
from schemas.course import MaterialCreateRequest, MaterialUpdateRequest
from service.course_service import check_course_access
from AI.document_processor import document_processor
from AI.ocr_service import ocr_service
import os
from core.config import settings


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
        transcript=data.transcript,
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
        course_id: int,
        module_id: int,
        material_id: int,
        file_ids: List[int],
        user: User,
        db: AsyncSession
):
    """Прикрепление файлов с автоматическим извлечением текста"""
    print(f"\n{'=' * 60}")
    print(f"🔵 ATTACH FILES TO MATERIAL")
    print(f"Material ID: {material_id}, File IDs: {file_ids}")
    print(f"{'=' * 60}\n")

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

    print(f"📋 Material found: {material.title}")
    print(f"   Current text_content: {material.text_content[:50] if material.text_content else 'None'}...")

    result = await db.execute(
        select(File).where(File.id.in_(file_ids))
    )
    files = result.scalars().all()
    if len(files) != len(file_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some files not found"
        )

    print(f"📁 Found {len(files)} files")

    material_files = []
    extracted_texts = []

    for file in files:
        print(f"\n--- Processing file: {file.filename} ---")
        print(f"   File path: {file.file_path}")
        print(f"   File ID: {file.id}")

        # Проверяем, не прикреплён ли уже
        existing = await db.execute(
            select(MaterialFile).where(
                and_(
                    MaterialFile.material_id == material_id,
                    MaterialFile.file_id == file.id
                )
            )
        )
        if existing.scalar_one_or_none():
            print(f"   ⚠️ File already attached, skipping")
            continue

        # Прикрепляем файл
        material_file = MaterialFile(
            material_id=material_id,
            file_id=file.id
        )
        db.add(material_file)
        material_files.append(material_file)
        print(f"   ✅ MaterialFile created")

        # Формируем полный путь
        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        file_extension = os.path.splitext(file.filename)[1].lower()

        print(f"   Full path: {file_path}")
        print(f"   Extension: {file_extension}")
        print(f"   File exists: {os.path.exists(file_path)}")

        if not os.path.exists(file_path):
            print(f"   ❌ ERROR: File does not exist at path!")
            continue

        # Извлекаем текст
        extracted_text = None

        if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
            print(f"   🔍 Processing image with OCR: {file.filename}")
            try:
                extracted_text = await ocr_service.extract_with_formulas(file_path)
                print(f"   OCR result: {len(extracted_text) if extracted_text else 0} chars")
            except Exception as e:
                print(f"   ❌ OCR error: {str(e)}")
        else:
            print(f"   📄 Extracting text from document: {file.filename}")
            try:
                extracted_text = await document_processor.extract_text_from_file(
                    file_path, file_extension
                )
                print(f"   Extraction result: {len(extracted_text) if extracted_text else 0} chars")
            except Exception as e:
                print(f"   ❌ Extraction error: {str(e)}")

        if extracted_text:
            extracted_texts.append(extracted_text)
            print(f"   ✅ Extracted {len(extracted_text)} characters")
            print(f"   Preview: {extracted_text[:100]}...")
        else:
            print(f"   ⚠️ No text extracted")

    print(f"\n{'=' * 60}")
    print(f"📊 EXTRACTION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total files processed: {len(material_files)}")
    print(f"Texts extracted: {len(extracted_texts)}")

    if extracted_texts:
        # Объединяем тексты
        if material.text_content and material.text_content != "string":
            combined_text = material.text_content + "\n\n--- Следующий файл ---\n\n" + "\n\n--- Следующий файл ---\n\n".join(
                extracted_texts)
        else:
            combined_text = "\n\n--- Следующий файл ---\n\n".join(extracted_texts)

        print(f"Combined text length: {len(combined_text)}")
        print(f"Preview: {combined_text[:200]}...")

        # Обновляем материал
        material.text_content = combined_text
        print(f"✅ Updated material.text_content")
    else:
        print(f"⚠️ No texts to save")

    print(f"{'=' * 60}\n")

    # Сохраняем в БД
    await db.commit()
    print(f"💾 Database committed")

    await db.refresh(material)
    print(f"🔄 Material refreshed from DB")
    print(f"Final text_content length: {len(material.text_content) if material.text_content else 0}")

    # Загружаем связи
    material_files_with_relations = []
    for mf in material_files:
        result = await db.execute(
            select(MaterialFile)
            .options(
                selectinload(MaterialFile.file),
                selectinload(MaterialFile.material)
            )
            .where(MaterialFile.id == mf.id)
        )
        mf_loaded = result.scalar_one()
        material_files_with_relations.append(mf_loaded)

    return material_files_with_relations


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
