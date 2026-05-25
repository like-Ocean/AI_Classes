from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from typing import Optional
from math import ceil
from models import (
    Course,
    Module,
    Material,
    User,
    CourseApplication,
    CourseEnrollment,
    LessonProgress,
    MaterialFile,
    Test,
    TestAttempt,
    HomeworkAssignment,
    HomeworkSubmission,
)
from helpers.students.access_helper import (
    check_course_enrollment,
    require_course_enrollment,
    check_material_access,
)
from helpers.students.course_loader import (
    load_course_with_modules,
    get_materials_progress,
    load_module_with_materials,
)
from helpers.students.my_courses_helper import (
    load_user_enrollments,
    load_pending_applications,
    get_course_progress,
)
from helpers.students.progress_helper import (
    update_course_progress_record,
    get_course_with_progress_data,
)
from helpers.students.formatters import format_progress_data, format_course_card


# COURSE CATALOG
async def get_available_courses(
    user: User,
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    query = select(Course).options(selectinload(Course.creator))

    if search:
        search_filter = or_(
            Course.title.ilike(f"%{search}%"), Course.description.ilike(f"%{search}%")
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
                CourseEnrollment.course_id.in_(course_ids),
            )
        )
    )
    enrollments = {e.course_id: e for e in enrollments_result.scalars().all()}

    applications_result = await db.execute(
        select(CourseApplication)
        .where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id.in_(course_ids),
            )
        )
        .order_by(CourseApplication.applied_at.desc())
    )
    applications = {}
    for application in applications_result.scalars().all():
        if application.course_id not in applications:
            applications[application.course_id] = application

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
            "application_status": (
                applications[course.id].status if course.id in applications else None
            ),
        }
        courses_data.append(course_dict)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "courses": courses_data,
    }


async def get_course_public_detail(course_id: int, user: User, db: AsyncSession):
    course = await load_course_with_modules(course_id, db)
    enrollment = await check_course_enrollment(course_id, user, db, raise_error=False)
    application_result = await db.execute(
        select(CourseApplication)
        .where(
            and_(
                CourseApplication.user_id == user.id,
                CourseApplication.course_id == course_id,
            )
        )
        .order_by(CourseApplication.applied_at.desc())
        .limit(1)
    )
    application = application_result.scalar_one_or_none()
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "img_url": course.img_url,
        "creator": course.creator,
        "created_at": course.created_at,
        "is_enrolled": enrollment is not None,
        "application_status": application.status if application else None,
    }


# MY COURSES


async def get_my_courses(user: User, db: AsyncSession):
    enrollments = await load_user_enrollments(user.id, db)
    applications = await load_pending_applications(user.id, db)
    enrolled_course_ids = {e.course_id for e in enrollments}
    courses_data = []
    for enrollment in enrollments:
        progress = await get_course_progress(user.id, enrollment.course_id, db)
        progress_data = format_progress_data(progress)

        course_card = format_course_card(
            course=enrollment.course,
            progress_data=progress_data,
            application_status=None,
        )
        courses_data.append(course_card)

    for application in applications:
        if application.course_id not in enrolled_course_ids:
            course_card = format_course_card(
                course=application.course,
                progress_data=None,
                application_status=application.status,
            )
            courses_data.append(course_card)

    return {"courses": courses_data}


async def get_my_courses_progress(
    user: User,
    db: AsyncSession,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    page_size: int = 20,
):
    enrollments = await load_user_enrollments(user.id, db)
    if search:
        search_value = search.lower()
        enrollments = [
            e
            for e in enrollments
            if search_value in (e.course.title or "").lower()
            or search_value in (e.course.description or "").lower()
        ]

    if not enrollments:
        return {
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "courses": [],
        }

    course_ids = [e.course_id for e in enrollments]

    total_lessons_result = await db.execute(
        select(Module.course_id, func.count(Material.id))
        .join(Material, Material.module_id == Module.id)
        .where(Module.course_id.in_(course_ids))
        .group_by(Module.course_id)
    )
    total_lessons_map = {row[0]: row[1] for row in total_lessons_result.all()}

    total_tests_result = await db.execute(
        select(Module.course_id, func.count(Test.id))
        .join(Material, Material.module_id == Module.id)
        .join(Test, Test.material_id == Material.id)
        .where(Module.course_id.in_(course_ids))
        .group_by(Module.course_id)
    )
    total_tests_map = {row[0]: row[1] for row in total_tests_result.all()}

    total_homework_result = await db.execute(
        select(HomeworkAssignment.course_id, func.count(HomeworkAssignment.id))
        .where(HomeworkAssignment.course_id.in_(course_ids))
        .group_by(HomeworkAssignment.course_id)
    )
    total_homework_map = {row[0]: row[1] for row in total_homework_result.all()}

    completed_lessons_result = await db.execute(
        select(Module.course_id, func.count(LessonProgress.id))
        .join(Material, LessonProgress.lesson_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(Module.course_id.in_(course_ids), LessonProgress.user_id == user.id)
        )
        .group_by(Module.course_id)
    )
    completed_lessons_map = {row[0]: row[1] for row in completed_lessons_result.all()}

    completed_tests_result = await db.execute(
        select(Module.course_id, func.count(func.distinct(TestAttempt.test_id)))
        .join(Test, TestAttempt.test_id == Test.id)
        .join(Material, Test.material_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(
                Module.course_id.in_(course_ids),
                TestAttempt.user_id == user.id,
                TestAttempt.passed.is_(True),
            )
        )
        .group_by(Module.course_id)
    )
    completed_tests_map = {row[0]: row[1] for row in completed_tests_result.all()}

    completed_homework_result = await db.execute(
        select(HomeworkAssignment.course_id, func.count(HomeworkSubmission.id))
        .join(
            HomeworkSubmission,
            HomeworkSubmission.assignment_id == HomeworkAssignment.id,
        )
        .where(
            and_(
                HomeworkAssignment.course_id.in_(course_ids),
                HomeworkSubmission.student_id == user.id,
                HomeworkSubmission.review_result == "credit",
            )
        )
        .group_by(HomeworkAssignment.course_id)
    )
    completed_homework_map = {row[0]: row[1] for row in completed_homework_result.all()}

    courses_data = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lessons = total_lessons_map.get(course.id, 0)
        total_tests = total_tests_map.get(course.id, 0)
        total_homework = total_homework_map.get(course.id, 0)

        completed_lessons = completed_lessons_map.get(course.id, 0)
        completed_tests = completed_tests_map.get(course.id, 0)
        completed_homework = completed_homework_map.get(course.id, 0)

        total_items = total_lessons + total_tests + total_homework
        completed_items = completed_lessons + completed_tests + completed_homework
        progress_percentage = (
            (completed_items / total_items * 100) if total_items > 0 else 0.0
        )

        courses_data.append(
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "img_url": course.img_url,
                "created_at": course.created_at,
                "completed_lessons": completed_lessons,
                "completed_tests": completed_tests,
                "completed_homework": completed_homework,
                "total_lessons": total_lessons,
                "total_tests": total_tests,
                "total_homework": total_homework,
                "progress_percentage": round(progress_percentage, 2),
            }
        )

    sort_key_map = {
        "created_at": lambda c: c["created_at"],
        "progress": lambda c: c["progress_percentage"],
        "title": lambda c: (c["title"] or "").lower(),
    }
    key_func = sort_key_map.get(sort_by, sort_key_map["created_at"])
    reverse = order.lower() != "asc"
    courses_data.sort(key=key_func, reverse=reverse)

    total = len(courses_data)
    total_pages = ceil(total / page_size) if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    paginated_courses = courses_data[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "courses": paginated_courses,
    }


async def get_enrolled_course_detail(course_id: int, user: User, db: AsyncSession):
    await require_course_enrollment(course_id, user, db)
    course = await load_course_with_modules(course_id, db)
    return await get_course_with_progress_data(course, user.id, db)


# MODULE WITH PROGRESS
async def get_module_with_progress(
    course_id: int, module_id: int, user: User, db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
    module = await load_module_with_materials(course_id, module_id, db)
    material_ids = [m.id for m in module.materials]
    progress_map = await get_materials_progress(user.id, material_ids, db)

    materials_data = []
    completed_count = 0

    for material in module.materials:
        progress = progress_map.get(material.id)
        is_completed = progress is not None

        if is_completed:
            completed_count += 1

        material_dict = {
            "id": material.id,
            "title": material.title,
            "type": material.type.value,
            "position": material.position,
            "is_completed": is_completed,
            "completed_at": progress.completed_at if progress else None,
            "is_locked": False,
            "lock_reason": None,
            "has_tests": len(material.tests) > 0,
            "has_homework": len(material.homework_assignments),
        }
        materials_data.append(material_dict)

    progress_percentage = (
        (completed_count / len(module.materials) * 100) if module.materials else 0
    )

    return {
        "id": module.id,
        "title": module.title,
        "position": module.position,
        "course_id": module.course_id,
        "materials": materials_data,
        "progress_percentage": round(progress_percentage, 2),
    }


# PROGRESS TRACKING


async def mark_material_completed(
    course_id: int, module_id: int, material_id: int, user: User, db: AsyncSession
):
    await require_course_enrollment(course_id, user, db)
    result = await db.execute(
        select(Material)
        .join(Module)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id,
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module",
        )
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == material_id,
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


async def get_material_detail(
    course_id: int, module_id: int, material_id: int, user: User, db: AsyncSession
):
    access = await check_material_access(course_id, module_id, material_id, user, db)
    result = await db.execute(
        select(Material)
        .options(
            selectinload(Material.module),
            selectinload(Material.material_files).selectinload(MaterialFile.file),
            selectinload(Material.tests),
            selectinload(Material.homework_assignments),
        )
        .where(Material.id == material_id)
    )
    material = result.scalar_one()
    progress_result = await db.execute(
        select(LessonProgress).where(
            and_(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == material_id,
            )
        )
    )
    progress = progress_result.scalar_one_or_none()
    return {
        "id": material.id,
        "module": {
            "id": material.module.id,
            "title": material.module.title,
            "position": material.module.position,
            "course_id": material.module.course_id,
        },
        "type": material.type,
        "title": material.title,
        "content_url": material.content_url,
        "text_content": material.text_content,
        "transcript": material.transcript,
        "position": material.position,
        "files": [
            {"id": mf.id, "file_id": mf.file_id, "file": mf.file}
            for mf in material.material_files
        ],
        "has_tests": len(material.tests) > 0,
        "has_homework": len(material.homework_assignments),
        "tests": [
            {
                "id": test.id,
                "title": test.title,
                "num_questions": test.num_questions,
                "time_limit_seconds": test.time_limit_seconds,
                "pass_threshold": test.pass_threshold,
            }
            for test in material.tests
        ],
        "is_completed": progress is not None,
        "completed_at": progress.completed_at if progress else None,
    }
