from fastapi import HTTPException
from sqlalchemy import select, and_, or_
from math import ceil
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status
from models import User, RoleType, CourseEditor
from service.course_service import check_course_access


async def add_editor(course_id: int, teacher_id: int, user: User, db: AsyncSession):
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


async def get_course_editors(
    course_id: int, user: User,
    db: AsyncSession,
    search: Optional[str] = None,
    page: int = 1, page_size: int = 20
):
    await check_course_access(course_id, user, db, require_creator=True)
    query = (
        select(CourseEditor)
        .options(selectinload(CourseEditor.user))
        .join(CourseEditor.user)
        .where(CourseEditor.course_id == course_id)
    )

    if search:
        search_filter = or_(
            User.email.ilike(f"%{search}%"),
            User.first_name.ilike(f"%{search}%"),
            User.last_name.ilike(f"%{search}%"),
            User.patronymic.ilike(f"%{search}%"),
            User.group_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    query = query.order_by(CourseEditor.granted_at.desc())
    result = await db.execute(query)
    editors = list(result.scalars().all())
    total = len(editors)
    total_pages = ceil(total / page_size) if total > 0 else 0
    start = (page - 1) * page_size
    end = start + page_size
    paginated_editors = editors[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "editors": paginated_editors
    }
