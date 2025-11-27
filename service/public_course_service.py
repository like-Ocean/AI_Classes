from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload
from math import ceil
from models import Course


async def get_public_courses(
    db: AsyncSession, search: str = None,
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

    courses_data = [
        {
            "id": course.id,
            "title": course.title,
            "description": course.description,
            "img_url": course.img_url,
            "creator": course.creator,
            "created_at": course.created_at
        }
        for course in courses
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "courses": courses_data
    }


async def get_public_course_detail(course_id: int, db: AsyncSession):
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
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "img_url": course.img_url,
        "creator": course.creator,
        "created_at": course.created_at
    }
