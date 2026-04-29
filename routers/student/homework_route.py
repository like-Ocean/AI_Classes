from typing import List, Optional
from fastapi import APIRouter, Depends, File as FastAPIFile, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user
from models import User
from schemas.homework import HomeworkStudentItemResponse, HomeworkSubmissionResponse
from service import homework_service


student_homework_router = APIRouter(tags=["Student / ДЗ"])


@student_homework_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/homework",
    response_model=List[HomeworkStudentItemResponse],
    summary="List homework assignments for material"
)
async def list_homework_assignments_for_student(
    course_id: int, module_id: int,
    material_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await homework_service.list_material_homework_for_student(
        course_id=course_id, module_id=module_id,
        material_id=material_id,
        user=current_user, db=db
    )


@student_homework_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/homework/{assignment_id}/submit",
    response_model=HomeworkSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit homework (text/files/video/photo)"
)
async def submit_homework(
    course_id: int, module_id: int,
    material_id: int, assignment_id: int,
    text_answer: Optional[str] = Form(None),
    files: List[UploadFile] = FastAPIFile(default=[]),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await homework_service.submit_homework(
        course_id=course_id, module_id=module_id,
        material_id=material_id,
        assignment_id=assignment_id,
        text_answer=text_answer,
        files=files, user=current_user, db=db
    )

    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "text_answer": submission.text_answer,
        "status": submission.status,
        "review_result": submission.review_result,
        "review_comment": submission.review_comment,
        "reviewed_by": submission.reviewed_by,
        "reviewed_at": submission.reviewed_at,
        "submitted_at": submission.submitted_at,
        "updated_at": submission.updated_at,
        "files": [sf.file for sf in submission.files]
    }


@student_homework_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/homework/{assignment_id}/submission",
    response_model=HomeworkSubmissionResponse,
    summary="Get my homework submission"
)
async def get_my_submission(
    course_id: int, module_id: int,
    material_id: int, assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await homework_service.get_my_homework_submission(
        course_id=course_id, module_id=module_id,
        material_id=material_id, assignment_id=assignment_id,
        user=current_user, db=db
    )

    return {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "student_id": submission.student_id,
        "text_answer": submission.text_answer,
        "status": submission.status,
        "review_result": submission.review_result,
        "review_comment": submission.review_comment,
        "reviewed_by": submission.reviewed_by,
        "reviewed_at": submission.reviewed_at,
        "submitted_at": submission.submitted_at,
        "updated_at": submission.updated_at,
        "files": [sf.file for sf in submission.files]
    }
