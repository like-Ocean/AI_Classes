from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from models import Material, Module, LessonProgress, CourseProgress, Course
from .course_loader import get_materials_progress


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
        user_id: int,
        course_id: int,
        db: AsyncSession
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


async def get_course_with_progress_data(course: Course, user_id: int, db: AsyncSession):
    material_ids = [m.id for module in course.modules for m in module.materials]
    progress_map = await get_materials_progress(user_id, material_ids, db)

    completed, total = await calculate_course_progress(user_id, course.id, db)
    overall_progress = (completed / total * 100) if total > 0 else 0

    modules_data = []
    for module in course.modules:
        completed_in_module = sum(
            1 for material in module.materials if progress_map.get(material.id)
        )
        total_in_module = len(module.materials)
        module_progress = (
            (completed_in_module / total_in_module * 100)
            if total_in_module > 0 else 0
        )

        module_dict = {
            "id": module.id,
            "title": module.title,
            "position": module.position,
            "course_id": module.course_id,
            "progress_percentage": round(module_progress, 2),
            "completed_materials": completed_in_module,
            "total_materials": total_in_module
        }
        modules_data.append(module_dict)

    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "img_url": course.img_url,
        "creator": course.creator,
        "created_at": course.created_at,
        "modules": modules_data,
        "overall_progress": round(overall_progress, 2),
        "completed_materials": completed,
        "total_materials": total
    }
