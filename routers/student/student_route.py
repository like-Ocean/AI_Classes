from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from core.dependencies import get_current_user
from service import student_service
from models import User
from schemas.student import (
    CourseApplicationResponse, PaginatedCoursesResponse,
    MyCoursesResponse, LessonProgressResponse,
    ModuleWithProgressResponse
)
from schemas.course import CourseWithModulesResponse
from schemas.auth import MessageResponse

student_router = APIRouter(prefix="/student", tags=["Student"])

# TODO: Сдлать так чтобы препод или админ могли примнимать заявку студента(
#  одобрить\изменить её статус с pending на другой)


# НЕ ТЕСТИЛ
# COURSE CATALOG

@student_router.get(
    "/courses",
    response_model=PaginatedCoursesResponse,
    summary="Get available courses catalog"
)
async def get_courses_catalog(
        search: Optional[str] = Query(
            None,
            description="Поиск по названию или описанию"
        ),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_available_courses(
        user=current_user, db=db, search=search,
        page=page, page_size=page_size
    )
    return data


@student_router.get(
    "/courses/{course_id}",
    response_model=dict,
    summary="Get course public info"
)
async def get_course_public_info(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_course_public_detail(
        course_id, current_user, db
    )
    return data


# APPLICATIONS

@student_router.post(
    "/courses/{course_id}/apply",
    response_model=CourseApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for course"
)
async def apply_for_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    application = await student_service.apply_for_course(
        course_id, current_user, db
    )
    return application


@student_router.get(
    "/applications",
    response_model=list[CourseApplicationResponse],
    summary="Get my applications"
)
async def get_my_applications(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    applications = await student_service.get_my_applications(
        current_user, db
    )
    return applications


@student_router.delete(
    "/applications/{application_id}",
    response_model=MessageResponse,
    summary="Cancel application"
)
async def cancel_application(
        application_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    await student_service.cancel_application(
        application_id, current_user, db
    )
    return MessageResponse(message="Application cancelled successfully")


# MY COURSES

@student_router.get(
    "/my-courses",
    response_model=MyCoursesResponse,
    summary="Get my enrolled courses"
)
async def get_my_courses(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_my_courses(
        current_user, db
    )
    return data


@student_router.get(
    "/my-courses/{course_id}",
    response_model=CourseWithModulesResponse,
    summary="Get enrolled course details"
)
async def get_enrolled_course(
        course_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    course = await student_service.get_enrolled_course_detail(
        course_id, current_user, db
    )
    return course


@student_router.get(
    "/modules/{module_id}",
    response_model=ModuleWithProgressResponse,
    summary="Get module with progress"
)
async def get_module(
        module_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    data = await student_service.get_module_with_progress(
        module_id, current_user, db
    )
    return data


# PROGRESS

@student_router.post(
    "/materials/{material_id}/complete",
    response_model=LessonProgressResponse,
    summary="Mark material as completed"
)
async def complete_material(
        material_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    progress = await student_service.mark_material_completed(
        material_id, current_user, db
    )
    return progress
