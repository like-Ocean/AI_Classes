from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import Course
from typing import Dict, Set
from models import (
    LessonProgress, TestAttempt, Material,
    Module, CourseProgress, MaterialFile
)
from datetime import datetime


async def load_course_with_creator(course_id: int, db: AsyncSession):
    result = await db.execute(
        select(Course)
        .options(selectinload(Course.creator))
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    return course


async def load_course_with_modules(course_id: int, db: AsyncSession):
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.creator),
            selectinload(Course.modules)
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    course.modules.sort(key=lambda m: m.position)
    return course


async def get_materials_progress(
        user_id: int, material_ids: list[int],
        db: AsyncSession
) -> Dict[int, LessonProgress]:
    if not material_ids:
        return {}
    result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(material_ids)
            )
        )
    )
    return {p.lesson_id: p for p in result.scalars().all()}


async def get_passed_tests(
        user_id: int,
        test_ids: list[int],
        db: AsyncSession
) -> Set[int]:
    if not test_ids:
        return set()
    result = await db.execute(
        select(TestAttempt.test_id).where(
            and_(
                TestAttempt.test_id.in_(test_ids),
                TestAttempt.user_id == user_id,
                TestAttempt.passed == True
            )
        )
    )
    return {row[0] for row in result.all()}


async def calculate_course_progress(
        user_id: int,
        course_id: int,
        db: AsyncSession
) -> tuple[int, int]:
    total_result = await db.execute(
        select(func.count(Material.id))
        .join(Module)
        .where(Module.course_id == course_id)
    )
    total_materials = total_result.scalar()

    completed_result = await db.execute(
        select(func.count(LessonProgress.id))
        .join(Material, LessonProgress.lesson_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(
                Module.course_id == course_id,
                LessonProgress.user_id == user_id
            )
        )
    )
    completed_materials = completed_result.scalar()

    return completed_materials, total_materials


async def update_course_progress_record(
        user_id: int, course_id: int, db: AsyncSession
):
    completed, total = await calculate_course_progress(user_id, course_id, db)
    result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id
            )
        )
    )
    progress = result.scalar_one_or_none()

    if progress:
        progress.completed_items = completed
        progress.total_items = total
        progress.last_accessed_at = datetime.utcnow()
    else:
        progress = CourseProgress(
            user_id=user_id,
            course_id=course_id,
            completed_items=completed,
            total_items=total
        )
        db.add(progress)

    await db.commit()


async def load_module_with_materials(course_id: int, module_id: int, db: AsyncSession):
    result = await db.execute(
        select(Module)
        .options(
            selectinload(Module.materials)
            .selectinload(Material.material_files)
            .selectinload(MaterialFile.file),
            selectinload(Module.materials)
            .selectinload(Material.tests)
        )
        .where(and_(Module.id == module_id, Module.course_id == course_id))
    )
    module = result.scalar_one_or_none()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found in this course"
        )
    module.materials.sort(key=lambda m: m.position)
    return module


async def load_course_modules_with_materials(course_id: int, db: AsyncSession):
    result = await db.execute(
        select(Module)
        .options(selectinload(Module.materials))
        .where(Module.course_id == course_id)
        .order_by(Module.position)
    )
    modules = list(result.scalars().all())
    for module in modules:
        module.materials.sort(key=lambda m: m.position)

    return modules
