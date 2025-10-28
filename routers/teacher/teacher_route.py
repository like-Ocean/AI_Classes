from fastapi import APIRouter, Depends, status, UploadFile, File as FastAPIFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from core.dependencies import get_current_teacher
from service import course_service, file_service
from models import User
from schemas.course import (
    CourseCreateRequest, CourseUpdateRequest, CourseResponse,
    CourseDetailResponse, ModuleCreateRequest, ModuleUpdateRequest,
    ModuleResponse, MaterialCreateRequest, MaterialUpdateRequest,
    MaterialResponse, AddEditorRequest, EditorResponse
)
from schemas.file import FileResponse, MaterialFileResponse
from schemas.auth import MessageResponse

teacher_router = APIRouter(prefix="/teacher", tags=["Teacher"])

# НЕ ТЕСТИЛ НУЖНО ПРОВЕРЯТЬ. СКОРЕЕ ВСЕГО НУЖНО ДОБАВИТЬ
# ЕЩЁ ПРАУ ТАБЛИЦ ДЛЯ МАТЕРИАЛОВ Т.К Я ЗАТУПИЛ..
# Добавил но ничего не тестил

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
    response_model=List[CourseResponse],
    summary="Get my courses"
)
async def get_my_courses(
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    courses = await course_service.get_my_courses(current_teacher, db)
    return courses


@teacher_router.get(
    "/courses/{course_id}",
    response_model=CourseDetailResponse,
    summary="Get course details"
)
async def get_course(
        course_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    course = await course_service.get_course_detail(
        course_id, current_teacher, db
    )
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
    module = await course_service.create_module(
        course_id, data, current_teacher, db
    )
    return module


@teacher_router.put(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update module"
)
async def update_module(
        module_id: int,
        data: ModuleUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    module = await course_service.update_module(
        module_id, data, current_teacher, db
    )
    return module


@teacher_router.delete(
    "/modules/{module_id}",
    response_model=MessageResponse,
    summary="Delete module"
)
async def delete_module(
        module_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await course_service.delete_module(
        module_id, current_teacher, db
    )
    return MessageResponse(
        message="Module successfully deleted"
    )


# MATERIALS

@teacher_router.post(
    "/modules/{module_id}/materials",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create material"
)
async def create_material(
        module_id: int,
        data: MaterialCreateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    material = await course_service.create_material(
        module_id, data, current_teacher, db
    )
    return material


@teacher_router.put(
    "/materials/{material_id}",
    response_model=MaterialResponse,
    summary="Update material"
)
async def update_material(
        material_id: int, data: MaterialUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    material = await course_service.update_material(
        material_id, data, current_teacher, db
    )
    return material


@teacher_router.delete(
    "/materials/{material_id}",
    response_model=MessageResponse,
    summary="Delete material"
)
async def delete_material(
        material_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await course_service.delete_material(
        material_id, current_teacher, db
    )
    return MessageResponse(
        message="Material successfully deleted"
    )


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
    editor = await course_service.add_editor(
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
    await course_service.remove_editor(
        course_id, editor_id, current_teacher, db
    )
    return MessageResponse(
        message="Editor successfully removed"
    )

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
    """
    Максимальный размер: 100 MB
    """
    uploaded_file = await file_service.save_file(file, db)
    return uploaded_file


#     Прикрепление файлов к материалу.
#     Сначала загрузить файлы через /files/upload,
#     затем прикрепите их к материалу по ID.
@teacher_router.post(
    "/materials/{material_id}/files",
    response_model=List[MaterialFileResponse],
    summary="Attach files to material"
)
async def attach_files(
        material_id: int, file_ids: List[int],
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    material_files = await course_service.attach_files_to_material(
        material_id, file_ids, current_teacher, db
    )
    return material_files


@teacher_router.delete(
    "/materials/{material_id}/files/{file_id}",
    response_model=MessageResponse,
    summary="Detach file from material"
)
async def detach_file(
        material_id: int, file_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await course_service.detach_file_from_material(
        material_id, file_id, current_teacher, db
    )
    return MessageResponse(message="File detached successfully")
