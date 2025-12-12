from math import ceil
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import (
    Course, Material, CourseEditor, User, Module,
    MaterialFile, CourseEnrollment, CourseProgress,
    LessonProgress
)
from helpers.students.my_courses_helper import format_progress_data
from schemas.enums import CourseRoleFilter
from schemas.course import CourseCreateRequest, CourseUpdateRequest


async def check_course_access(
        course_id: int, user: User,
        db: AsyncSession, require_creator: bool = False
):
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    if course.creator_id == user.id:
        return course

    if require_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course creator can perform this action"
        )

    editor_result = await db.execute(
        select(CourseEditor).where(
            and_(
                CourseEditor.course_id == course_id,
                CourseEditor.user_id == user.id
            )
        )
    )
    editor = editor_result.scalar_one_or_none()

    if not editor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this course"
        )

    return course


async def create_course(data: CourseCreateRequest, creator: User, db: AsyncSession):
    course = Course(
        title=data.title, description=data.description,
        img_url=data.img_url, creator_id=creator.id
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)

    return course


async def get_my_courses(
        user: User, db: AsyncSession,
        search: Optional[str] = None,
        page: int = 1, page_size: int = 20,
        role: CourseRoleFilter = CourseRoleFilter.all
):
    creator_query = (
        select(Course)
        .options(selectinload(Course.creator))
        .where(Course.creator_id == user.id)
    )

    editor_query = (
        select(Course)
        .options(selectinload(Course.creator))
        .join(CourseEditor, Course.id == CourseEditor.course_id)
        .where(CourseEditor.user_id == user.id)
    )
    if search:
        search_filter = or_(
            Course.title.ilike(f"%{search}%"),
            Course.description.ilike(f"%{search}%")
        )
        creator_query = creator_query.where(search_filter)
        editor_query = editor_query.where(search_filter)

    if role == CourseRoleFilter.created:
        creator_result = await db.execute(creator_query)
        created_courses = list(creator_result.scalars().all())
        courses_list = created_courses

    elif role == CourseRoleFilter.editor:
        editor_result = await db.execute(editor_query)
        editor_courses = list(editor_result.scalars().all())
        courses_list = editor_courses

    else:
        creator_result = await db.execute(creator_query)
        editor_result = await db.execute(editor_query)

        created_courses = list(creator_result.scalars().all())
        editor_courses = list(editor_result.scalars().all())

        all_courses = {course.id: course for course in created_courses + editor_courses}
        courses_list = list(all_courses.values())

    courses_list.sort(key=lambda c: c.created_at, reverse=True)

    total = len(courses_list)
    total_pages = ceil(total / page_size) if total > 0 else 0

    start = (page - 1) * page_size
    end = start + page_size
    paginated_courses = courses_list[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "courses": paginated_courses
    }


async def get_course_detail(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.modules),
            selectinload(Course.creator)
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one()
    course.modules.sort(key=lambda m: m.position)

    return course


async def get_material_detail_for_teacher(
        course_id: int, module_id: int,
        material_id: int, user: User,
        db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .options(
            selectinload(Material.module),
            selectinload(Material.material_files).selectinload(MaterialFile.file),
            selectinload(Material.tests)
        )
        .where(
            and_(
                Material.id == material_id,
                Material.module_id == module_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    if material.module.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this course"
        )

    return {
        "id": material.id,
        "module": {
            "id": material.module.id,
            "title": material.module.title,
            "position": material.module.position,
            "course_id": material.module.course_id
        },
        "type": material.type,
        "title": material.title,
        "content_url": material.content_url,
        "text_content": material.text_content,
        "transcript": material.transcript,
        "position": material.position,
        "files": [
            {
                "id": mf.id,
                "file_id": mf.file_id,
                "file": mf.file
            }
            for mf in material.material_files
        ],
        "has_tests": len(material.tests) > 0,
        "tests": [
            {
                "id": test.id,
                "title": test.title,
                "num_questions": test.num_questions,
                "time_limit_seconds": test.time_limit_seconds,
                "pass_threshold": test.pass_threshold
            }
            for test in material.tests
        ]
    }


async def update_course(
        course_id: int, data: CourseUpdateRequest,
        user: User, db: AsyncSession
):
    course = await check_course_access(course_id, user, db)

    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.img_url is not None:
        course.img_url = data.img_url

    await db.commit()
    await db.refresh(course)

    return course


async def delete_course(course_id: int, user: User, db: AsyncSession):
    course = await check_course_access(course_id, user, db, require_creator=True)
    await db.delete(course)
    await db.commit()


async def get_enrolled_students(
        course_id: int, user: User, db: AsyncSession,
        search: Optional[str] = None,
        min_progress: Optional[int] = None,
        page: int = 1, page_size: int = 50
):
    await check_course_access(course_id, user, db, require_creator=False)
    query = (
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.user))
        .where(CourseEnrollment.course_id == course_id)
    )
    if search:
        query = query.join(User, CourseEnrollment.user_id == User.id)
        query = query.where(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    result = await db.execute(query)
    all_enrollments = list(result.scalars().all())

    user_ids = [e.user_id for e in all_enrollments]
    progress_result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.course_id == course_id,
                CourseProgress.user_id.in_(user_ids)
            )
        )
    )
    progresses = {p.user_id: p for p in progress_result.scalars().all()}
    formatted_progresses = {}
    for user_id, progress_obj in progresses.items():
        formatted_progresses[user_id] = format_progress_data(progress_obj)

    if min_progress is not None:
        filtered_enrollments = [
            e for e in all_enrollments
            if e.user_id in formatted_progresses
               and formatted_progresses[e.user_id]["progress_percentage"] >= min_progress
        ]
    else:
        filtered_enrollments = all_enrollments

    total = len(filtered_enrollments)
    total_pages = ceil(total / page_size) if total > 0 else 0

    start = (page - 1) * page_size
    end = start + page_size
    paginated_enrollments = filtered_enrollments[start:end]

    students_data = []
    for enrollment in paginated_enrollments:
        student_dict = {
            "user": enrollment.user,
            "progress": formatted_progresses.get(enrollment.user_id)
        }
        students_data.append(student_dict)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "students": students_data
    }


async def unenroll_student(
        course_id: int, user_id: int,
        user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.user))
        .where(
            and_(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id
            )
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this course"
        )

    progress_result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.course_id == course_id,
                CourseProgress.user_id == user_id
            )
        )
    )
    progress = progress_result.scalar_one_or_none()
    if progress:
        await db.delete(progress)

    lesson_progress_result = await db.execute(
        select(LessonProgress)
        .join(Material, LessonProgress.lesson_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(
                Module.course_id == course_id,
                LessonProgress.user_id == user_id
            )
        )
    )
    lesson_progresses = lesson_progress_result.scalars().all()
    for lp in lesson_progresses:
        await db.delete(lp)

    await db.delete(enrollment)
    await db.commit()

    student_name = f"{enrollment.user.last_name} {enrollment.user.first_name}"

    return {
        "message": f"Student {student_name} unenrolled from course"
    }
