from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from models import (
    Course, Module, Material, CourseEditor,
    User, MaterialFile, CourseApplication,
    CourseEnrollment
)
from models.Enums import RoleType, ApplicationStatus
from schemas.course import (
    CourseCreateRequest, CourseUpdateRequest, ModuleCreateRequest,
    ModuleUpdateRequest
)


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


async def get_my_courses(user: User, db: AsyncSession):
    creator_query = select(Course).options(
        selectinload(Course.creator)
    ).where(Course.creator_id == user.id)
    editor_query = (
        select(Course)
        .options(selectinload(Course.creator))
        .join(CourseEditor, Course.id == CourseEditor.course_id)
        .where(CourseEditor.user_id == user.id)
    )

    creator_result = await db.execute(creator_query)
    editor_result = await db.execute(editor_query)

    created_courses = list(creator_result.scalars().all())
    editor_courses = list(editor_result.scalars().all())

    all_courses = {course.id: course for course in created_courses + editor_courses}

    return list(all_courses.values())


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


async def add_editor(
        course_id: int, teacher_id: int,
        user: User, db: AsyncSession
):
    course = await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.id == teacher_id)
    )
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    if teacher.role.name not in [RoleType.teacher, RoleType.admin]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be a teacher or admin"
        )

    existing_editor = await db.execute(
        select(CourseEditor).where(
            and_(
                CourseEditor.course_id == course_id,
                CourseEditor.user_id == teacher_id
            )
        )
    )
    if existing_editor.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an editor of this course"
        )

    editor = CourseEditor(
        course_id=course_id, user_id=teacher_id,
        granted_by=user.id
    )

    db.add(editor)
    await db.commit()
    await db.refresh(editor)

    result = await db.execute(
        select(CourseEditor)
        .options(selectinload(CourseEditor.user))
        .where(CourseEditor.id == editor.id)
    )
    editor_loaded = result.scalar_one()

    return editor_loaded


async def remove_editor(course_id: int, editor_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(CourseEditor).where(
            and_(
                CourseEditor.id == editor_id,
                CourseEditor.course_id == course_id
            )
        )
    )
    editor = result.scalar_one_or_none()
    if not editor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Editor not found in this course"
        )

    await db.delete(editor)
    await db.commit()


async def get_course_editors(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=True)
    result = await db.execute(
        select(CourseEditor)
        .options(selectinload(CourseEditor.user))
        .where(CourseEditor.course_id == course_id)
        .order_by(CourseEditor.granted_at.desc())
    )
    editors = result.scalars().all()
    return list(editors)


# APPLICATION MANAGEMENT
async def get_course_applications(course_id: int, user: User, db: AsyncSession):
    await check_course_access(course_id, user, db, require_creator=False)
    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.course_id == course_id)
        .order_by(CourseApplication.applied_at.desc())
    )
    return list(result.scalars().all())


async def approve_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication)
        .options(selectinload(CourseApplication.course))
        .where(CourseApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    await check_course_access(application.course_id, user, db, require_creator=False)
    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application status is already '{application.status}'"
        )

    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            and_(
                CourseEnrollment.user_id == application.user_id,
                CourseEnrollment.course_id == application.course_id
            )
        )
    )
    if enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already enrolled in this course"
        )

    application.status = ApplicationStatus.approved
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = user.id

    enrollment = CourseEnrollment(
        user_id=application.user_id,
        course_id=application.course_id
    )

    db.add(enrollment)
    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.id == application.id)
    )
    application_loaded = result.scalar_one()

    return {
        "id": application_loaded.id,
        "user": application_loaded.user,
        "course": application_loaded.course,
        "status": application_loaded.status,
        "applied_at": application_loaded.applied_at,
        "reviewed_at": application_loaded.reviewed_at,
        "reviewed_by": application_loaded.reviewer
    }


async def reject_application(application_id: int, user: User, db: AsyncSession):
    result = await db.execute(
        select(CourseApplication)
        .options(selectinload(CourseApplication.course))
        .where(CourseApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )

    await check_course_access(application.course_id, user, db, require_creator=False)

    if application.status != ApplicationStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application status is already '{application.status}'"
        )

    application.status = ApplicationStatus.rejected
    application.reviewed_at = datetime.utcnow()
    application.reviewed_by = user.id

    await db.commit()
    await db.refresh(application)

    result = await db.execute(
        select(CourseApplication)
        .options(
            selectinload(CourseApplication.user),
            selectinload(CourseApplication.course).selectinload(Course.creator),
            selectinload(CourseApplication.reviewer)
        )
        .where(CourseApplication.id == application.id)
    )
    application_loaded = result.scalar_one()

    return {
        "id": application_loaded.id,
        "user": application_loaded.user,
        "course": application_loaded.course,
        "status": application_loaded.status,
        "applied_at": application_loaded.applied_at,
        "reviewed_at": application_loaded.reviewed_at,
        "reviewed_by": application_loaded.reviewer
    }
