from math import ceil
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import (
    Course, Material, CourseEditor, User, Module,
    MaterialFile, CourseEnrollment, CourseProgress,
    LessonProgress, Test, TestAttempt,
    HomeworkAssignment, HomeworkSubmission,
)
from helpers.general.common_helper import _build_full_name
from helpers.students.formatters import format_progress_data
from schemas.enums import CourseRoleFilter
from schemas.course import CourseCreateRequest, CourseUpdateRequest
from schemas.teacher_progress import CourseProgressOverviewResponse, StudentProgressRow


async def check_course_access(
    course_id: int, user: User, db: AsyncSession, require_creator: bool = False
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    if course.creator_id == user.id:
        return course

    if require_creator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only course creator can perform this action",
        )

    editor_result = await db.execute(
        select(CourseEditor).where(
            and_(CourseEditor.course_id == course_id, CourseEditor.user_id == user.id)
        )
    )
    editor = editor_result.scalar_one_or_none()

    if not editor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this course",
        )

    return course


async def create_course(data: CourseCreateRequest, creator: User, db: AsyncSession):
    course = Course(
        title=data.title,
        description=data.description,
        img_url=data.img_url,
        creator_id=creator.id,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)

    return course


async def get_my_courses(
    user: User, db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1, page_size: int = 20,
    role: CourseRoleFilter = CourseRoleFilter.all,
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
            Course.title.ilike(f"%{search}%"), Course.description.ilike(f"%{search}%")
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
        "courses": paginated_courses,
    }


async def get_course_detail(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Course)
        .options(
            selectinload(Course.modules)
            .selectinload(Module.materials)
            .selectinload(Material.material_files)
            .selectinload(MaterialFile.file),
            selectinload(Course.creator),
        )
        .where(Course.id == course_id)
    )
    course = result.scalar_one()
    course.modules.sort(key=lambda m: m.position)
    for module in course.modules:
        module.materials.sort(key=lambda mat: mat.position)
        for material in module.materials:
            material.files = material.material_files

    return course


async def get_material_detail_for_teacher(
    course_id: int, module_id: int, material_id: int, user: User, db: AsyncSession
):
    await check_course_access(course_id, user, db)
    result = await db.execute(
        select(Material)
        .options(
            selectinload(Material.module),
            selectinload(Material.material_files).selectinload(MaterialFile.file),
            selectinload(Material.tests),
            selectinload(Material.homework_assignments),
        )
        .where(and_(Material.id == material_id, Material.module_id == module_id))
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Material not found"
        )

    if material.module.course_id != course_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this course",
        )

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
        "has_homework": len(material.homework_assignments),
        "has_tests": len(material.tests) > 0,
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
    }


async def update_course(
    course_id: int, data: CourseUpdateRequest, user: User, db: AsyncSession
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
    page: int = 1, page_size: int = 50,
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
            or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )

    result = await db.execute(query)
    all_enrollments = list(result.scalars().all())

    user_ids = [e.user_id for e in all_enrollments]
    progress_result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.course_id == course_id,
                CourseProgress.user_id.in_(user_ids),
            )
        )
    )
    progresses = {p.user_id: p for p in progress_result.scalars().all()}
    formatted_progresses = {}
    for user_id, progress_obj in progresses.items():
        formatted_progresses[user_id] = format_progress_data(progress_obj)

    if min_progress is not None:
        filtered_enrollments = [
            e
            for e in all_enrollments
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
            "progress": formatted_progresses.get(enrollment.user_id),
        }
        students_data.append(student_dict)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "students": students_data,
    }


async def unenroll_student(course_id: int, user_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.user))
        .where(
            and_(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id,
            )
        )
    )
    enrollment = result.scalar_one_or_none()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in this course",
        )

    progress_result = await db.execute(
        select(CourseProgress).where(
            and_(
                CourseProgress.course_id == course_id, CourseProgress.user_id == user_id
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
        .where(and_(Module.course_id == course_id, LessonProgress.user_id == user_id))
    )
    lesson_progresses = lesson_progress_result.scalars().all()
    for lp in lesson_progresses:
        await db.delete(lp)

    await db.delete(enrollment)
    await db.commit()

    student_name = f"{enrollment.user.last_name} {enrollment.user.first_name}"

    return {"message": f"Student {student_name} unenrolled from course"}


async def get_course_progress_overview(
    course_id: int, user: User, db: AsyncSession, page: int = 1,
    page_size: int = 50, search: Optional[str] = None,
    group_name: Optional[str] = None, min_progress: Optional[float] = None,
    max_progress: Optional[float] = None,
    sort_by: str = "progress", order: str = "desc",
) -> CourseProgressOverviewResponse:
    await check_course_access(course_id, user, db, require_creator=False)

    total_materials_result = await db.execute(
        select(func.count(Material.id))
        .join(Module)
        .where(Module.course_id == course_id)
    )
    total_materials = total_materials_result.scalar() or 0

    total_tests_result = await db.execute(
        select(func.count(Test.id))
        .join(Material, Test.material_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(Module.course_id == course_id)
    )
    total_tests = total_tests_result.scalar() or 0

    total_homework_result = await db.execute(
        select(func.count(HomeworkAssignment.id)).where(
            HomeworkAssignment.course_id == course_id
        )
    )
    total_homework = total_homework_result.scalar() or 0

    enrollments_result = await db.execute(
        select(CourseEnrollment)
        .options(selectinload(CourseEnrollment.user))
        .where(CourseEnrollment.course_id == course_id)
    )
    enrollments = list(enrollments_result.scalars().all())
    user_ids = [e.user_id for e in enrollments]

    if not user_ids:
        total_pages = 0
        return CourseProgressOverviewResponse(
            course_id=course_id,
            total_materials=total_materials,
            total_tests=total_tests,
            total_homework=total_homework,
            total=0,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            students=[],
            least_active=[],
        )

    lessons_result = await db.execute(
        select(LessonProgress.user_id, func.count(LessonProgress.id))
        .join(Material, LessonProgress.lesson_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(Module.course_id == course_id, LessonProgress.user_id.in_(user_ids))
        )
        .group_by(LessonProgress.user_id)
    )
    lessons_map = {row[0]: row[1] for row in lessons_result.all()}

    tests_result = await db.execute(
        select(TestAttempt.user_id, func.count(func.distinct(TestAttempt.test_id)))
        .join(Test, TestAttempt.test_id == Test.id)
        .join(Material, Test.material_id == Material.id)
        .join(Module, Material.module_id == Module.id)
        .where(
            and_(
                Module.course_id == course_id,
                TestAttempt.user_id.in_(user_ids),
                TestAttempt.passed.is_(True),
            )
        )
        .group_by(TestAttempt.user_id)
    )
    tests_map = {row[0]: row[1] for row in tests_result.all()}

    homework_result = await db.execute(
        select(HomeworkSubmission.student_id, func.count(HomeworkSubmission.id))
        .join(
            HomeworkAssignment,
            HomeworkSubmission.assignment_id == HomeworkAssignment.id,
        )
        .where(
            and_(
                HomeworkAssignment.course_id == course_id,
                HomeworkSubmission.student_id.in_(user_ids),
                HomeworkSubmission.review_result == "credit",
            )
        )
        .group_by(HomeworkSubmission.student_id)
    )
    homework_map = {row[0]: row[1] for row in homework_result.all()}

    students_rows: list[StudentProgressRow] = []
    for enrollment in enrollments:
        student = enrollment.user
        completed_lessons = lessons_map.get(student.id, 0)
        completed_tests = tests_map.get(student.id, 0)
        completed_homework = homework_map.get(student.id, 0)
        progress_percentage = (
            (completed_lessons / total_materials * 100) if total_materials > 0 else 0.0
        )
        students_rows.append(
            StudentProgressRow(
                user_id=student.id,
                full_name=_build_full_name(student),
                group_name=student.group_name,
                completed_lessons=completed_lessons,
                completed_tests=completed_tests,
                completed_homework=completed_homework,
                total_tests=total_tests,
                remaining_tests=max(total_tests - completed_tests, 0),
                total_homework=total_homework,
                remaining_homework=max(total_homework - completed_homework, 0),
                progress_percentage=round(progress_percentage, 2),
            )
        )

    if search:
        search_value = search.lower()
        email_map = {e.user_id: e.user.email for e in enrollments}
        students_rows = [
            row for row in students_rows
            if search_value in " ".join(
                part.lower() for part in [
                    row.full_name or "",
                    row.group_name or "",
                    email_map.get(row.user_id, ""),
                ]
            )
        ]

    if group_name:
        group_value = group_name.lower()
        students_rows = [
            row for row in students_rows
            if (row.group_name or "").lower() == group_value
        ]

    if min_progress is not None:
        students_rows = [row for row in students_rows if row.progress_percentage >= min_progress]

    if max_progress is not None:
        students_rows = [row for row in students_rows if row.progress_percentage <= max_progress]

    sort_key_map = {
        "progress": lambda s: s.progress_percentage,
        "full_name": lambda s: (s.full_name or "").lower(),
        "completed_lessons": lambda s: s.completed_lessons,
        "completed_tests": lambda s: s.completed_tests,
        "completed_homework": lambda s: s.completed_homework,
        "group_name": lambda s: (s.group_name or "").lower(),
    }
    key_func = sort_key_map.get(sort_by, sort_key_map["progress"])
    reverse = order.lower() != "asc"
    students_rows.sort(key=key_func, reverse=reverse)

    least_active = sorted(students_rows, key=lambda s: s.progress_percentage)[:5]

    total = len(students_rows)
    total_pages = ceil(total / page_size) if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    paginated_students = students_rows[start:end]

    return CourseProgressOverviewResponse(
        course_id=course_id,
        total_materials=total_materials,
        total_tests=total_tests,
        total_homework=total_homework,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        students=paginated_students,
        least_active=least_active,
    )
