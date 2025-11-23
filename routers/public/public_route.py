from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from service import public_course_service
from schemas.student import PaginatedPublicCoursesResponse, PublicCourseCard


public_router = APIRouter(prefix="/public/courses", tags=["Public Courses"])


@public_router.get(
    "", response_model=PaginatedPublicCoursesResponse,
    summary="Get all available courses (public)"
)
async def get_public_courses(
    search: Optional[str] = Query(
        None,
        description="Search by title or description"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await public_course_service.get_public_courses(db, search, page, page_size)


@public_router.get(
    "/{course_id}", response_model=PublicCourseCard,
    summary="Get public course info"
)
async def get_public_course(course_id: int, db: AsyncSession = Depends(get_db)):
    return await public_course_service.get_public_course_detail(course_id, db)
