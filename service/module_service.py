from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from helpers.teacher.test_list_helper import load_module_tests
from models import User, Module, Material, MaterialFile
from schemas.course import ModuleCreateRequest, ModuleUpdateRequest
from service.course_service import check_course_access


async def create_module(
        course_id: int, data: ModuleCreateRequest,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    module = Module(
        course_id=course_id,
        title=data.title,
        position=data.position
    )

    db.add(module)
    await db.commit()
    await db.refresh(module)

    return module


async def get_module_detail(
        course_id: int, module_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Module)
        .options(
            selectinload(Module.materials)
            .selectinload(Material.material_files)
            .selectinload(MaterialFile.file)
        )
        .where(and_(Module.id == module_id, Module.course_id == course_id))
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found in this course"
        )

    module.materials.sort(key=lambda mat: mat.position)
    for material in module.materials:
        material.files = material.material_files

    return module


async def update_module(
        course_id: int, module_id: int,
        data: ModuleUpdateRequest,
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

    if data.title is not None:
        module.title = data.title
    if data.position is not None:
        module.position = data.position

    await db.commit()
    await db.refresh(module)

    return module


async def delete_module(
        course_id: int, module_id: int,
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

    await db.delete(module)
    await db.commit()


async def get_module_tests(
        course_id: int, module_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    tests = await load_module_tests(course_id, module_id, db)
    tests_data = []
    for test in tests:
        test_dict = {
            "id": test.id,
            "title": test.title,
            "material_id": test.material_id,
            "module_id": module_id,
            "num_questions": len(test.questions),
            "time_limit_seconds": test.time_limit_seconds,
            "pass_threshold": test.pass_threshold,
            "status": test.status,
            "generated_by_nn": test.generated_by_nn
        }
        tests_data.append(test_dict)

    return {
        "tests": tests_data,
        "total": len(tests_data)
    }
