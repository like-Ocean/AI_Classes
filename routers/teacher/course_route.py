from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from core.database import get_db
from core.dependencies import get_current_teacher
from service import course_service, material_service, module_service
from models import User
from schemas.enums import CourseRoleFilter
from schemas.course import (
    CourseCreateRequest, CourseUpdateRequest, CourseResponse,
    ModuleCreateRequest, ModuleUpdateRequest,
    CourseWithModulesResponse, ModuleResponse,
    ModuleWithMaterialsResponse, MaterialCreateRequest,
    MaterialUpdateRequest, MaterialResponse,
    MaterialDetailForTeacher,
)
from schemas.student import PaginatedCoursesResponse
from schemas.auth import MessageResponse
from schemas.tests import TestsListResponse

teacher_course_router = APIRouter(tags=["Teacher / Курсы"])


@teacher_course_router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create course"
)
async def create_course(
        data: CourseCreateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await course_service.create_course(data, current_teacher, db)


@teacher_course_router.get(
    "/courses",
    response_model=PaginatedCoursesResponse,
    summary="Get my courses with pagination"
)
async def get_my_courses(
        search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
        role: CourseRoleFilter = Query(
            CourseRoleFilter.all,
            description="Фильтр по роли: all (все),created (только созданные),editor (только редактируемые)"
        ),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await course_service.get_my_courses(
        current_teacher, db, search, page, page_size, role
    )


@teacher_course_router.get(
    "/courses/{course_id}",
    response_model=CourseWithModulesResponse,
    summary="Get course with modules"
)
async def get_course(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await course_service.get_course_detail(course_id, current_teacher, db)


@teacher_course_router.put(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Update course"
)
async def update_course(
        course_id: int,
        data: CourseUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await course_service.update_course(course_id, data, current_teacher, db)


@teacher_course_router.delete(
    "/courses/{course_id}",
    response_model=MessageResponse,
    summary="Delete course"
)
async def delete_course(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await course_service.delete_course(course_id, current_teacher, db)
    return MessageResponse(message="Course successfully deleted")


@teacher_course_router.post(
    "/courses/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create module"
)
async def create_module(
        course_id: int,
        data: ModuleCreateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await module_service.create_module(course_id, data, current_teacher, db)


@teacher_course_router.get(
    "/courses/{course_id}/modules/{module_id}",
    response_model=ModuleWithMaterialsResponse,
    summary="Get module with materials"
)
async def get_module(
    course_id: int,
    module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await module_service.get_module_detail(course_id, module_id, current_teacher, db)


@teacher_course_router.put(
    "/courses/{course_id}/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update module"
)
async def update_module(
    course_id: int,
    module_id: int,
    data: ModuleUpdateRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await module_service.update_module(course_id, module_id, data, current_teacher, db)


@teacher_course_router.delete(
    "/courses/{course_id}/modules/{module_id}",
    response_model=MessageResponse,
    summary="Delete module"
)
async def delete_module(
    course_id: int, module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await module_service.delete_module(course_id, module_id, current_teacher, db)
    return MessageResponse(message="Module successfully deleted")


@teacher_course_router.post(
    "/courses/{course_id}/modules/{module_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create material"
)
async def create_material(
    course_id: int, module_id: int,
    data: MaterialCreateRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await material_service.create_material(
        course_id, module_id, data, current_teacher, db
    )


@teacher_course_router.put(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MaterialResponse,
    summary="Update material"
)
async def update_material(
    course_id: int, module_id: int,
    material_id: int, data: MaterialUpdateRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await material_service.update_material(
        course_id, module_id, material_id,
        data, current_teacher, db
    )


@teacher_course_router.delete(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MessageResponse,
    summary="Delete material"
)
async def delete_material(
    course_id: int, module_id: int,
    material_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await material_service.delete_material(
        course_id, module_id, material_id, 
        current_teacher, db
    )
    return MessageResponse(message="Material successfully deleted")


@teacher_course_router.get(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MaterialDetailForTeacher,
    summary="Get material detail for teacher"
)
async def get_material_detail(
    course_id: int, module_id: int,
    material_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await course_service.get_material_detail_for_teacher(
        course_id, module_id, material_id,
        current_teacher, db
    )


@teacher_course_router.get(
    "/courses/{course_id}/modules/{module_id}/tests",
    response_model=TestsListResponse,
    summary="Get all tests in module"
)
async def get_module_tests(
    course_id: int, module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await module_service.get_module_tests(
        course_id, module_id, current_teacher, db
    )
