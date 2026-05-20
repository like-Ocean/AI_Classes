from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from core.dependencies import get_current_user
from service import student_service, application_service
from models import User
from models.Enums import ApplicationStatus
from schemas.student import (
    CourseApplicationResponse, PaginatedCoursesResponse,
    MyCoursesResponse, MyCoursesProgressResponse,
    LessonProgressResponse, ModuleWithProgressResponse,
    CourseCardResponse, EnrolledCourseDetailResponse,
    MaterialDetailForStudent, PaginatedApplicationsResponse
)
from schemas.auth import MessageResponse

student_catalog_router = APIRouter(tags=["Student / Каталог"])


@student_catalog_router.get(
    "/courses",
    response_model=PaginatedCoursesResponse,
    summary="Get available courses catalog"
)
async def get_courses_catalog(
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_available_courses(
        user=current_user, db=db, search=search, page=page, page_size=page_size
    )


@student_catalog_router.get(
    "/courses/{course_id}",
    response_model=CourseCardResponse,
    summary="Get course public info"
)
async def get_course_public_info(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_course_public_detail(course_id, current_user, db)


@student_catalog_router.post(
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
    return await application_service.apply_for_course(course_id, current_user, db)


@student_catalog_router.get(
    "/applications",
    response_model=PaginatedApplicationsResponse,
    summary="Get my applications"
)
async def get_my_applications(
    status: Optional[ApplicationStatus] = Query(None, description="Фильтр по статусу: pending, approved, rejected"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await application_service.get_my_applications(
        current_user, db, status, page, page_size
    )


@student_catalog_router.delete(
    "/applications/{application_id}",
    response_model=MessageResponse,
    summary="Cancel application"
)
async def cancel_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await application_service.cancel_application(application_id, current_user, db)
    return MessageResponse(message="Application cancelled successfully")


@student_catalog_router.get(
    "/my-courses",
    response_model=MyCoursesProgressResponse,
    summary="Get my enrolled courses progress"
)
async def get_my_courses(
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    sort_by: str = Query("created_at", description="Сортировка: created_at, progress, title"),
    order: str = Query("desc", description="Порядок сортировки: asc или desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_my_courses_progress(
        current_user, db,
        search=search,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )


@student_catalog_router.get(
    "/my-courses-legacy",
    response_model=MyCoursesResponse,
    summary="Get my enrolled courses (legacy)"
)
async def get_my_courses_legacy(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_my_courses(current_user, db)


@student_catalog_router.get(
    "/my-courses/{course_id}",
    response_model=EnrolledCourseDetailResponse,
    summary="Get enrolled course details"
)
async def get_enrolled_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_enrolled_course_detail(course_id, current_user, db)


@student_catalog_router.get(
    "/my-courses/{course_id}/modules/{module_id}",
    response_model=ModuleWithProgressResponse,
    summary="Get module with progress"
)
async def get_module(
    course_id: int, module_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_module_with_progress(course_id, module_id, current_user, db)


@student_catalog_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/complete",
    response_model=LessonProgressResponse,
    summary="Mark material as completed"
)
async def complete_material(
    course_id: int, module_id: int, material_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.mark_material_completed(
        course_id, module_id, material_id, current_user, db
    )


@student_catalog_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MaterialDetailForStudent,
    summary="Get material detail (with access check)"
)
async def get_material_detail(
    course_id: int, module_id: int, material_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_service.get_material_detail(
        course_id, module_id, material_id, current_user, db
    )
