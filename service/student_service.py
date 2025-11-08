from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
from datetime import datetime
from schemas.course import CourseResponse
from math import ceil
from models import (
    Course, Module, Material, User, CourseApplication,
    CourseEnrollment, CourseProgress, LessonProgress, MaterialFile
)
from models.Enums import ApplicationStatus


# COURSE CATALOG

async def get_available_courses(
        user: User, db: AsyncSession,
        search: Optional[str] = None,
        page: int = 1, page_size: int = 20
):
    query = select(Course).options(selectinload(Course.creator))
    if search:
        search_filter = or_(
            Course.title.ilike(f"%{search}%"),
            Course.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    total_pages = ceil(total / page_size) if total > 0 else 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Course.created_at.desc())

    result = await db.execute(query)
    courses = list(result.scalars().all())

    course_ids = [c.id for c in courses]

    enrollments_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id.in_(course_ids)
            )
        )
    )
    enrollments = {e.course_id: e for e in enrollments_result.scalars().all()}

    applications_result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id.in_(course_ids)
            )
        )
    )
    applications = {a.course_id: a for a in applications_result.scalars().all()}

    courses_data = []
    for course in courses:
        course_dict = {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "img_url": course.img_url,
            "creator": course.creator,
            "created_at": course.created_at,
            "is_enrolled": course.id in enrollments,
            "application_status": applications[course.id].status if course.id in applications else None
        }
        courses_data.append(course_dict)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "courses": courses_data
    }


async def get_course_public_detail(course_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(Course).options(
            selectinload(Course.creator),
            selectinload(Course.modules)
        ).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()

    application_result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id == course_id
            )
        )
    )
    application = application_result.scalar_one_or_none()

    course.modules.sort(key=lambda m: m.position)

    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        img_url=course.img_url,
        creator=course.creator,
        created_at=course.created_at,
        is_enrolled=enrollment is not None,
        application_status=application.status if application else None
    )


# APPLICATIONS

async def apply_for_course(course_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already enrolled in this course"
        )

    application_result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id == course_id,
                CourseApplication.status == ApplicationStatus.pending
            )
        )
    )
    if application_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending application for this course"
        )

    application = CourseApplication(
        user_id=user.id,
        course_id=course_id,
        status=ApplicationStatus.pending
    )

    db.add(application)
    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.course).selectinload(Course.creator)
        )
        .where(CourseApplication.id == application.id)
    )
    application_with_course = result.scalar_one()

    return application_with_course


async def get_my_applications(user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.user_id == user.id)
        .order_by(CourseApplication.applied_at.desc())
    )
    return list(result.scalars().all())


async def cancel_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.id == application_id,
                CourseApplication.user_id == user.id
            )
        )
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending applications"
        )

    await db.delete(application)
    await db.commit()


# MY COURSES

async def get_my_courses(user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.course))
        .where(CourseEnrollment.user_id == user.id)
        .order_by(CourseEnrollment.id.desc())
    )
    enrollments = result.scalars().all()

    courses_data = []
    for enrollment in enrollments:
        progress_result = await db.execute(
            select(CourseProgress).where(
                and_(
                    CourseProgress.user_id == user.id,
                    CourseProgress.course_id == enrollment.course_id
                )
            )
        )
        progress = progress_result.scalar_one_or_none()
        course_dict = {
            "id": enrollment.course.id,
            "title": enrollment.course.title,
            "description": enrollment.course.description,
            "img_url": enrollment.course.img_url,
            "progress": None
        }
        if progress:
            progress_percentage = (
                (progress.completed_items / progress.total_items * 100)
                if progress.total_items > 0 else 0
            )
            course_dict["progress"] = {
                "id": progress.id,
                "course_id": progress.course_id,
                "user_id": progress.user_id,
                "completed_items": progress.completed_items,
                "total_items": progress.total_items,
                "progress_percentage": round(progress_percentage, 2),
                "last_accessed_at": progress.last_accessed_at
            }

        courses_data.append(course_dict)

    return {"courses": courses_data}


async def get_enrolled_course_detail(course_id: int, user: User, db: AsyncSession):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    enrollment = enrollment_result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.creator),
            selectinload(Course.modules)
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one()
    course.modules.sort(key=lambda m: m.position)

    return course


async def get_module_with_progress(
        course_id: int, module_id: int,
        user: User, db: AsyncSession
):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
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

    material_ids = [m.id for m in module.materials]
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id.in_(material_ids)
            )
        )
    )
    progress_map = {p.lesson_id: p for p in progress_result.scalars().all()}

    module.materials.sort(key=lambda m: m.position)

    materials_data = []
    completed_count = 0

    for material in module.materials:
        progress = progress_map.get(material.id)
        is_completed = progress is not None

        if is_completed:
            completed_count += 1

        material_dict = {
            "material_id": material.id,
            "title": material.title,
            "type": material.type,
            "position": material.position,
            "is_completed": is_completed,
            "completed_at": progress.completed_at if progress else None
        }
        materials_data.append(material_dict)

    progress_percentage = (
        (completed_count / len(module.materials) * 100)
        if module.materials else 0
    )

    return {
        "id": module.id,
        "title": module.title,
        "position": module.position,
        "course_id": module.course_id,
        "materials": materials_data,
        "progress_percentage": round(progress_percentage, 2)
    }


async def get_course_modules_with_progress(course_id: int, user: User, db: AsyncSession):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

    result = await db.execute(
        select(Module)
        .options(selectinload(Module.materials))
        .where(Module.course_id == course_id)
        .order_by(Module.position)
    )
    modules = result.scalars().all()

    material_ids = []
    for module in modules:
        material_ids.extend([m.id for m in module.materials])

    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id.in_(material_ids)
            )
        )
    )
    progress_map = {p.lesson_id: p for p in progress_result.scalars().all()}

    modules_data = []
    total_materials = 0
    total_completed = 0

    for module in modules:
        module.materials.sort(key=lambda m: m.position)

        materials_data = []
        completed_count = 0

        for material in module.materials:
            progress = progress_map.get(material.id)
            is_completed = progress is not None

            if is_completed:
                completed_count += 1
                total_completed += 1

            total_materials += 1

            material_dict = {
                "material_id": material.id,
                "title": material.title,
                "type": material.type,
                "position": material.position,
                "is_completed": is_completed,
                "completed_at": progress.completed_at if progress else None
            }
            materials_data.append(material_dict)

        progress_percentage = (
            (completed_count / len(module.materials) * 100)
            if module.materials else 0
        )

        module_dict = {
            "id": module.id,
            "title": module.title,
            "position": module.position,
            "course_id": module.course_id,
            "materials": materials_data,
            "progress_percentage": round(progress_percentage, 2)
        }
        modules_data.append(module_dict)

    overall_progress = (
        (total_completed / total_materials * 100)
        if total_materials > 0 else 0
    )

    return {
        "course_id": course_id,
        "modules": modules_data,
        "overall_progress": round(overall_progress, 2)
    }


# PROGRESS

async def mark_material_completed(
        course_id: int, module_id: int,
        material_id: int, user: User,
        db: AsyncSession
):
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == user.id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )
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

    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == material_id
            )
        )
    )
    existing_progress = progress_result.scalar_one_or_none()
    if existing_progress:
        return existing_progress

    progress = LessonProgress(user_id=user.id, lesson_id=material_id)

    db.add(progress)
    await db.commit()
    await db.refresh(progress)

    await update_course_progress(user.id, course_id, db)

    return progress


async def update_course_progress(user_id: int, course_id: int, db: AsyncSession):
    total_materials_result = await db.execute(
        select(func.count(Material.id)).join(Module)
        .where(Module.course_id == course_id)
    )
    total_materials = total_materials_result.scalar()

    completed_materials_result = await db.execute(
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
    completed_materials = completed_materials_result.scalar()

    progress_result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.user_id == user_id,
                CourseProgress.course_id == course_id
            )
        )
    )
    progress = progress_result.scalar_one_or_none()
    if progress:
        progress.completed_items = completed_materials
        progress.total_items = total_materials
        progress.last_accessed_at = datetime.utcnow()
    else:
        progress = CourseProgress(
            user_id=user_id, course_id=course_id,
            completed_items=completed_materials,
            total_items=total_materials
        )
        db.add(progress)

    await db.commit()
