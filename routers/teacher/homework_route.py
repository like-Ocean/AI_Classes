from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_teacher
from models import User
from schemas.homework import (
    HomeworkCreateRequest, HomeworkResponse,
    HomeworkSubmissionResponse, HomeworkReviewRequest,
    PaginatedHomeworkSubmissionsResponse,
)
from models.Enums import HomeworkSubmissionStatus, HomeworkReviewResult
from service import homework_service


teacher_homework_router = APIRouter(tags=["Teacher / ДЗ"])


@teacher_homework_router.post(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/homework",
    response_model=HomeworkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create homework assignment for material"
)
async def create_homework_assignment(
    course_id: int, module_id: int, material_id: int,
    data: HomeworkCreateRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await homework_service.create_homework_assignment(
        course_id=course_id, module_id=module_id,
        material_id=material_id,
        description=data.description,
        allowed_formats=data.allowed_formats,
        deadline=data.deadline,
        user=current_teacher, db=db
    )


@teacher_homework_router.get(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/homework",
    response_model=List[HomeworkResponse],
    summary="List homework assignments for material"
)
async def list_homework_assignments_for_teacher(
    course_id: int, module_id: int, material_id: int,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await homework_service.list_material_homework_for_teacher(
        course_id=course_id, module_id=module_id,
        material_id=material_id, user=current_teacher, db=db
    )


@teacher_homework_router.get(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/homework/{assignment_id}/submissions",
    response_model=PaginatedHomeworkSubmissionsResponse,
    summary="List submitted homework for teacher review"
)
async def list_homework_submissions(
    course_id: int, module_id: int,
    material_id: int, assignment_id: int,
    search: Optional[str] = Query(None, description="Поиск по имени или email"),
    submission_status: Optional[HomeworkSubmissionStatus] = Query(
        None,  alias="status", description="Фильтр по статусу"
    ),
    review_result: Optional[HomeworkReviewResult] = Query(
        None, description="Фильтр по результату проверки"
    ),
    sort_by: str = Query(
        "updated_at", description="Сортировка: submitted_at, updated_at, status, review_result"
    ),
    order: str = Query("desc", description="Порядок сортировки: asc или desc"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(50, ge=1, le=200, description="Размер страницы"),
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
):
    return await homework_service.list_homework_submissions_for_teacher(
        course_id=course_id, module_id=module_id,
        material_id=material_id, assignment_id=assignment_id,
        user=current_teacher, db=db,
        search=search, submission_status=submission_status,
        review_result=review_result,
        sort_by=sort_by, order=order,
        page=page, page_size=page_size,
    )


@teacher_homework_router.post(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/homework/{assignment_id}/submissions/{submission_id}/review",
    response_model=HomeworkSubmissionResponse,
    summary="Review homework submission (credit/no credit)"
)
async def review_homework_submission(
    course_id: int, module_id: int,
    material_id: int, assignment_id: int,
    submission_id: int, data: HomeworkReviewRequest,
    current_teacher: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db)
):
    return await homework_service.review_homework_submission(
        course_id=course_id, module_id=module_id,
        material_id=material_id, assignment_id=assignment_id,
        submission_id=submission_id, review_result=data.review_result,
        review_comment=data.review_comment,
        user=current_teacher, db=db
    )
