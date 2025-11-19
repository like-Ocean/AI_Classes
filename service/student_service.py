from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
from schemas.course import CourseResponse
from math import ceil
from models import (
    Course, Module, Material, User, CourseApplication,
    CourseEnrollment, CourseProgress, LessonProgress
)
from models.Enums import ApplicationStatus
from helpers.students.access_helper import (
    check_course_enrollment, require_course_enrollment,
    get_material_with_validation, get_module_materials,
    check_previous_material_completed, check_material_lock
)
from helpers.students.course_loader import (
    load_course_with_modules, load_course_with_creator,
    get_materials_progress, get_passed_tests,
    update_course_progress_record,
    load_module_with_materials, load_course_modules_with_materials
)

# TODO: всё работает вроде, нужно только удалить дубликаты
#  и разобраться с тем как возвращать курсы и модули.(с прогрессом или без)

# MATERIAL ACCESS

async def check_material_access(
        course_id: int, module_id: int,
        material_id: int, user: User,
        db: AsyncSession
) -> dict:
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
    course = await load_course_with_modules(course_id, db)
    enrollment = await check_course_enrollment(course_id, user, db, raise_error=False)
    application_result = await db.execute(
        select(CourseApplication).where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id == course_id
            )
        )
    )
    application = application_result.scalar_one_or_none()
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


# APPLICATIONS (используется в роутах)

async def apply_for_course(course_id: int, user: User, db: AsyncSession):
    course = await load_course_with_creator(course_id, db)
    enrollment = await check_course_enrollment(course_id, user, db, raise_error=False)
    if enrollment:
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


# MY COURSES (используется в роутах)

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
    await require_course_enrollment(course_id, user, db)
    course = await load_course_with_modules(course_id, db)
    return course


# MODULE WITH PROGRESS
async def get_module_with_progress(
        course_id: int, module_id: int,
        user: User, db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
    module = await load_module_with_materials(course_id, module_id, db)
    material_ids = [m.id for m in module.materials]
    progress_map = await get_materials_progress(user.id, material_ids, db)
    test_ids = [t.id for m in module.materials for t in m.tests]
    passed_test_ids = await get_passed_tests(user.id, test_ids, db)

    materials_data = []
    completed_count = 0

    for i, material in enumerate(module.materials):
        progress = progress_map.get(material.id)
        is_completed = progress is not None

        if is_completed:
            completed_count += 1

        is_locked, lock_reason = check_material_lock(
            material, i, module.materials,
            progress_map, passed_test_ids
        )

        material_dict = {
            "material_id": material.id,
            "title": material.title,
            "type": material.type.value,
            "position": material.position,
            "is_completed": is_completed,
            "completed_at": progress.completed_at if progress else None,
            "is_locked": is_locked,
            "lock_reason": lock_reason,
            "has_tests": len(material.tests) > 0
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


async def get_course_modules_with_progress(
        course_id: int, user: User, db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
    modules = await load_course_modules_with_materials(course_id, db)
    material_ids = [m.id for module in modules for m in module.materials]
    progress_map = await get_materials_progress(user.id, material_ids, db)
    modules_data = []
    total_materials = 0
    total_completed = 0
    for module in modules:
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


# PROGRESS TRACKING

async def mark_material_completed(
        course_id: int, module_id: int,
        material_id: int, user: User,
        db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
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
    await update_course_progress_record(user_id, course_id, db)