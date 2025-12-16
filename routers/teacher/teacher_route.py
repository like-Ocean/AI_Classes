from fastapi import (
    APIRouter, Depends, status, UploadFile,
    File as FastAPIFile, Query
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from core.database import get_db
from core.dependencies import get_current_teacher
from service import (
    course_service, file_service, material_service,
    module_service, application_service, editor_service
)
from models import User
from models.Enums import ApplicationStatus
from schemas.enums import CourseRoleFilter
from schemas.course import (
    CourseCreateRequest, CourseUpdateRequest, CourseResponse,
    ModuleCreateRequest, ModuleUpdateRequest, CourseWithModulesResponse,
    ModuleResponse, ModuleWithMaterialsResponse,
    MaterialCreateRequest, MaterialUpdateRequest,
    MaterialResponse, AddEditorRequest, EditorResponse, MaterialDetailForTeacher
)
from schemas.student import (
    CourseApplicationDetailResponse,
    PaginatedApplicationsResponse, PaginatedCoursesResponse,
    EnrolledStudentsListResponse
)
from schemas.file import FileResponse, MaterialFileResponse
from schemas.auth import MessageResponse
from schemas.tests import TestsListResponse

teacher_router = APIRouter(prefix="/teacher", tags=["Teacher"])


# COURSES
@teacher_router.post(
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
    course = await course_service.create_course(
        data, current_teacher, db
    )
    return course


@teacher_router.get(
    "/courses",
    response_model=PaginatedCoursesResponse,
    summary="Get my courses with pagination"
)
async def get_my_courses(
        search: Optional[str] = Query(
            None,
            description="Поиск по названию или описанию"
        ),
        role: CourseRoleFilter = Query(
            CourseRoleFilter.all,
            description="Фильтр по роли: all (все),"
                        "created (только созданные),"
                        "editor (только редактируемые)"
        ),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    data = await course_service.get_my_courses(
        current_teacher, db, search, page, page_size, role
    )
    return data


@teacher_router.get(
    "/courses/{course_id}",
    response_model=CourseWithModulesResponse,
    summary="Get course with modules"
)
async def get_course(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    course = await course_service.get_course_detail(course_id, current_teacher, db)
    return course


@teacher_router.put(
    "/courses/{course_id}",
    response_model=CourseResponse,
    summary="Update course"
)
async def update_course(
        course_id: int, data: CourseUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    course = await course_service.update_course(
        course_id, data, current_teacher, db
    )
    return course


@teacher_router.delete(
    "/courses/{course_id}",
    response_model=MessageResponse,
    summary="Delete course"
)
async def delete_course(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await course_service.delete_course(
        course_id, current_teacher, db
    )
    return MessageResponse(
        message="Course successfully deleted"
    )


# MODULES

@teacher_router.post(
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
    module = await module_service.create_module(
        course_id, data, current_teacher, db
    )
    return module


@teacher_router.get(
    "/courses/{course_id}/modules/{module_id}",
    response_model=ModuleWithMaterialsResponse,
    summary="Get module with materials"
)
async def get_module(
    course_id: int, module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    module = await module_service.get_module_detail(
        course_id, module_id, current_teacher, db
    )
    return module


@teacher_router.put(
    "/courses/{course_id}/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update module"
)
async def update_module(
    course_id: int, module_id: int,
    data: ModuleUpdateRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    module = await module_service.update_module(
        course_id, module_id, data, current_teacher, db
    )
    return module


@teacher_router.delete(
    "/courses/{course_id}/modules/{module_id}",
    response_model=MessageResponse,
    summary="Delete module"
)
async def delete_module(
    course_id: int, module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await module_service.delete_module(
        course_id, module_id, current_teacher, db
    )
    return MessageResponse(message="Module successfully deleted")


# MATERIALS
@teacher_router.post(
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
    material = await material_service.create_material(
        course_id, module_id, data, current_teacher, db
    )
    return material


@teacher_router.put(
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
    material = await material_service.update_material(
        course_id, module_id, material_id, data, current_teacher, db
    )
    return material


@teacher_router.delete(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MessageResponse,
    summary="Delete material"
)
async def delete_material(
    course_id: int, module_id: int, material_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    await material_service.delete_material(
        course_id, module_id, material_id, current_teacher, db
    )
    return MessageResponse(message="Material successfully deleted")


@teacher_router.get(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}",
    response_model=MaterialDetailForTeacher,
    summary="Get material detail for teacher"
)
async def get_material_detail(
        course_id: int, module_id: int, material_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    material = await course_service.get_material_detail_for_teacher(
        course_id, module_id, material_id, current_teacher, db
    )
    return material


# FILES
@teacher_router.post(
    "/files/upload",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file"
)
async def upload_file(
        file: UploadFile = FastAPIFile(...),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    uploaded_file = await file_service.save_file(file, db)
    return uploaded_file


#     Прикрепление файлов к материалу.
#     Сначала загрузить файлы через /files/upload,
#     затем прикрепите их к материалу по ID.
@teacher_router.post(
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
    material_files = await material_service.attach_files_to_material(
        course_id, module_id, material_id, file_ids, current_teacher, db
    )
    return material_files


@teacher_router.delete(
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
        course_id, module_id, material_id, file_id, current_teacher, db
    )
    return MessageResponse(message="File detached successfully")


# EDITORS

@teacher_router.post(
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
    editor = await editor_service.add_editor(
        course_id, data.user_id, current_teacher, db
    )
    return editor


@teacher_router.delete(
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
    return MessageResponse(
        message="Editor successfully removed"
    )


@teacher_router.get(
    "/courses/{course_id}/editors",
    response_model=List[EditorResponse],
    summary="Get course editors"
)
async def get_editors(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    editors = await editor_service.get_course_editors(
        course_id, current_teacher, db
    )
    return editors


@teacher_router.get(
    "/courses/{course_id}/applications",
    response_model=PaginatedApplicationsResponse,
    summary="Get course applications"
)
async def get_applications(
        course_id: int,
        status: Optional[ApplicationStatus] = Query(
            None,
            description="Фильтр по статусу: pending, approved, rejected"
        ),
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    applications = await application_service.get_course_applications(
        course_id, current_teacher, db, status, page, page_size
    )
    return applications


@teacher_router.post(
    "/applications/{application_id}/approve",
    response_model=CourseApplicationDetailResponse,
    summary="Approve application"
)
async def approve_application(
        application_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    result = await application_service.approve_application(
        application_id, current_teacher, db
    )
    return result


@teacher_router.post(
    "/applications/{application_id}/reject",
    response_model=CourseApplicationDetailResponse,
    summary="Reject application"
)
async def reject_application(
        application_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    result = await application_service.reject_application(
        application_id, current_teacher, db
    )
    return result


@teacher_router.get(
    "/courses/{course_id}/modules/{module_id}/tests",
    response_model=TestsListResponse,
    summary="Get all tests in module"
)
async def get_module_tests(
    course_id: int, module_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    data = await module_service.get_module_tests(
        course_id, module_id, current_teacher, db
    )
    return data


@teacher_router.get(
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
    students = await course_service.get_enrolled_students(
        course_id, current_teacher, db, search, min_progress, page, page_size
    )
    return students


@teacher_router.delete(
    "/courses/{course_id}/students/{user_id}",
    response_model=MessageResponse,
    summary="Unenroll student from course"
)
async def unenroll_student(
        course_id: int, user_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    """
    Отчислить студента с курса. Доступно только создателю курса.
    """
    result = await course_service.unenroll_student(
        course_id, user_id, current_teacher, db
    )
    return result
