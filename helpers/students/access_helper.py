from models import CourseEnrollment
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import Material, Module, LessonProgress, TestAttempt, User
from typing import Optional, Set


async def check_course_enrollment(
        course_id: int, user: User, db: AsyncSession, raise_error: bool = True
) -> CourseEnrollment | None:
    result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment and raise_error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

    return enrollment


async def require_course_enrollment(course_id: int, user: User, db: AsyncSession):
    return await check_course_enrollment(course_id, user, db, raise_error=True)


async def get_material_with_validation(
        course_id: int, module_id: int,
        material_id: int, db: AsyncSession
) -> Material:
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.tests))
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
            detail="Material not found"
        )

    return material


async def get_module_materials(module_id: int, db: AsyncSession) -> list[Material]:
    result = await db.execute(
        select(Material)
        .options(selectinload(Material.tests))
        .where(Material.module_id == module_id)
        .order_by(Material.position)
    )
    return list(result.scalars().all())


async def check_previous_material_completed(
        previous_material: Material,
        user: User, db: AsyncSession
):
    if previous_material.tests:
        for test in previous_material.tests:
            passed = await db.execute(
                select(TestAttempt).where(
                    and_(
                        TestAttempt.test_id == test.id,
                        TestAttempt.user_id == user.id,
                        TestAttempt.passed == True
                    )
                )
            )
            if not passed.scalar_one_or_none():
                return False
        return True

    progress = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == previous_material.id
            )
        )
    )
    return progress.scalar_one_or_none() is not None


def check_material_lock(
        material: Material, material_index: int,
        all_materials: list[Material],
        progress_map: dict, passed_test_ids: Set[int]
):
    if material_index == 0:
        return False, None

    previous_material = all_materials[material_index - 1]

    if previous_material.tests:
        has_passed_test = any(
            test.id in passed_test_ids
            for test in previous_material.tests
        )

        if not has_passed_test:
            return True, f"Complete the test in '{previous_material.title}' to unlock"

    else:
        if previous_material.id not in progress_map:
            return True, f"Complete '{previous_material.title}' to unlock"

    return False, None


async def check_material_access(
        course_id: int, module_id: int,
        material_id: int, user: User,
        db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
    material = await get_material_with_validation(
        course_id, module_id, material_id, db
    )
    all_materials = await get_module_materials(module_id, db)
    current_position = next(
        (i for i, m in enumerate(all_materials) if m.id == material_id),
        None
    )
    if current_position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in module"
        )
    if current_position > 0:
        previous_material = all_materials[current_position - 1]

        if not await check_previous_material_completed(previous_material, user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You must complete '{previous_material.title}' before accessing this material"
            )

    return {
        "access_granted": True,
        "material": material
    }
