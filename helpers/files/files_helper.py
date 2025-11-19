import os
from typing import List
from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from starlette import status
from models import Module, Material, File, MaterialFile
from AI.document_processor import document_processor
from AI.transcription_service import transcription_service
from core.config import settings
from .file_processing_helper import combine_contents, process_single_file


async def get_material(db, material_id: int, module_id: int, course_id: int):
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
    return material


async def get_files(db, file_ids: List[int]):
    result = await db.execute(
        select(File).where(File.id.in_(file_ids))
    )
    files = result.scalars().all()
    if len(files) != len(file_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some files not found"
        )
    return files


async def process_files(db, material_id: int, files: List[File]):
    """Обработка всех файлов: создание связей и извлечение контента"""
    material_files = []
    extracted_texts = []
    transcriptions = []

    for file in files:
        existing = await db.execute(
            select(MaterialFile).where(
                and_(
                    MaterialFile.material_id == material_id,
                    MaterialFile.file_id == file.id
                )
            )
        )
        if existing.scalar_one_or_none():
            print(f"⚠️ File {file.filename} already attached, skipping")
            continue

        material_file = MaterialFile(material_id=material_id, file_id=file.id)
        db.add(material_file)
        material_files.append(material_file)

        file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        file_extension = os.path.splitext(file.filename)[1].lower()

        text, transcript = await process_single_file(
            file_path,
            file_extension,
            document_processor,
            transcription_service
        )

        if text:
            extracted_texts.append(text)
        if transcript:
            transcriptions.append(transcript)

    return material_files, extracted_texts, transcriptions


async def update_material_content(
        material: Material,
        extracted_texts: List[str],
        transcriptions: List[str]
):
    combined_text, combined_transcript = combine_contents(
        material.text_content,
        extracted_texts,
        material.transcript,
        transcriptions
    )
    if combined_text:
        material.text_content = combined_text
        print(f"✅ Updated text_content ({len(combined_text)} chars)")
    if combined_transcript:
        material.transcript = combined_transcript
        print(f"✅ Updated transcript ({len(combined_transcript)} chars)")


async def load_material_files_with_relations(db, material_files: List[MaterialFile]):
    result = []
    for mf in material_files:
        loaded = await db.execute(
            select(MaterialFile)
            .options(
                selectinload(MaterialFile.file),
                selectinload(MaterialFile.material)
            )
            .where(MaterialFile.id == mf.id)
        )
        result.append(loaded.scalar_one())
    return result
