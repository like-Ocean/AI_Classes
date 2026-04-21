from fastapi import APIRouter, Depends, status, UploadFile, File as FastAPIFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from core.database import get_db
from core.dependencies import get_current_teacher
from service import file_service, material_service, editor_service, application_service, course_service
from models import User
from models.Enums import ApplicationStatus
from schemas.course import AddEditorRequest, EditorResponse, PaginatedEditorsResponse
from schemas.student import (
    CourseApplicationDetailResponse,
    PaginatedApplicationsResponse,
    EnrolledStudentsListResponse,
)
from schemas.file import FileResponse, MaterialFileResponse
from schemas.auth import MessageResponse

teacher_management_router = APIRouter(tags=["Teacher / Управление"])


@teacher_management_router.post(
    "/files/upload", response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file"
)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await file_service.save_file(file, db)


@teacher_management_router.post(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/files",
    response_model=List[MaterialFileResponse],
    summary="Attach files to material"
)
async def attach_files(
    course_id: int, module_id: int,
    material_id: int, file_ids: List[int],
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await material_service.attach_files_to_material(
        course_id, module_id, material_id,
        file_ids, current_teacher, db
    )


@teacher_management_router.delete(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/files/{file_id}",
    response_model=MessageResponse,
    summary="Detach file from material"
)
async def detach_file(
    course_id: int, module_id: int,
    material_id: int, file_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await material_service.detach_file_from_material(
        course_id, module_id, material_id,
        file_id, current_teacher, db
    )
    return MessageResponse(message="File detached successfully")


@teacher_management_router.post(
    "/courses/{course_id}/editors",
    response_model=EditorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add course editor"
)
async def add_editor(
    course_id: int, data: AddEditorRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await editor_service.add_editor(
        course_id, data.user_id, current_teacher, db
    )


@teacher_management_router.delete(
    "/courses/{course_id}/editors/{editor_id}",
    response_model=MessageResponse,
    summary="Remove course editor"
)
async def remove_editor(
    course_id: int, editor_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await editor_service.remove_editor(
        course_id, editor_id, current_teacher, db
    )
    return MessageResponse(message="Editor successfully removed")


@teacher_management_router.get(
    "/courses/{course_id}/editors",
    response_model=PaginatedEditorsResponse,
    summary="Get course editors with pagination"
)
async def get_editors(
        course_id: int,
        search: Optional[str] = Query(None, description="Поиск по имени, фамилии, отчеству или email"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await editor_service.get_course_editors(
        course_id, current_teacher, db, 
        search, page, page_size
    )


@teacher_management_router.get(
    "/courses/{course_id}/applications",
    response_model=PaginatedApplicationsResponse,
    summary="Get course applications"
)
async def get_applications(
        course_id: int,
        status: Optional[ApplicationStatus] = Query(None, description="Фильтр по статусу: pending, approved, rejected"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await application_service.get_course_applications(
        course_id, current_teacher, 
        db, status, page, page_size
    )


@teacher_management_router.post(
    "/applications/{application_id}/approve",
    response_model=CourseApplicationDetailResponse,
    summary="Approve application"
)
async def approve_application(
        application_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await application_service.approve_application(
        application_id, current_teacher, db
    )


@teacher_management_router.post(
    "/applications/{application_id}/reject",
    response_model=CourseApplicationDetailResponse,
    summary="Reject application"
)
async def reject_application(
        application_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await application_service.reject_application(
        application_id, current_teacher, db
    )


@teacher_management_router.get(
    "/courses/{course_id}/students",
    response_model=EnrolledStudentsListResponse,
    summary="Get enrolled students"
)
async def get_enrolled_students(
        course_id: int,
        search: Optional[str] = Query(None, description="Поиск по имени или email"),
        min_progress: Optional[int] = Query(None, ge=0, le=100, description="Минимальный прогресс (%)"),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(50, ge=1, le=200, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    return await course_service.get_enrolled_students(
        course_id, current_teacher, db, search, 
        min_progress, page, page_size
    )


@teacher_management_router.delete(
    "/courses/{course_id}/students/{user_id}",
    response_model=MessageResponse,
    summary="Unenroll student from course"
)
async def unenroll_student(
    course_id: int, user_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await course_service.unenroll_student(
        course_id, user_id, current_teacher, db
    )
