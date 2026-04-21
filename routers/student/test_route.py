from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from core.database import get_db
from core.dependencies import get_current_user
from service import student_test_service
from models import User
from schemas.student_tests import (
    TestForStudent, TestAttemptResponse,
    SubmitAnswerRequest, QuestionAttemptResponse,
    TestResultResponse, MyTestAttemptSummary,
    TestAttemptWithBlockResponse, SubmitTestRequest,
    QuestionHintResponse, TestAttemptWithFeedbackResponse,
)

student_test_router = APIRouter(tags=["Student / Тесты"])


@student_test_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}",
    response_model=TestForStudent,
    summary="Get test for taking"
)
async def get_test(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.get_test_for_student(
        course_id, module_id, material_id,
        test_id, current_user, db
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/start",
    response_model=TestAttemptResponse, status_code=status.HTTP_201_CREATED,
    summary="Start test attempt"
)
async def start_test(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.start_test_attempt(
        course_id, module_id, material_id,
        test_id, current_user, db
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/answer",
    response_model=QuestionAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit answer to question"
)
async def submit_answer(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    attempt_id: int, data: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.submit_answer(
        course_id, module_id, material_id, test_id,
        attempt_id, data.question_id, data.answer,
        data.hint_used, current_user, db
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/finish",
    response_model=TestAttemptWithBlockResponse,
    summary="Finish test attempt"
)
async def finish_test(
    course_id: int, module_id: int, material_id: int,
    test_id: int, attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.finish_test_attempt(
        course_id, module_id, material_id, test_id,
        attempt_id, current_user, db
    )


@student_test_router.get(
    "/test-attempts/{attempt_id}/result",
    response_model=TestResultResponse,
    summary="Get test result"
)
async def get_result(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.get_test_result(
        attempt_id, current_user, db
    )


@student_test_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts",
    response_model=List[MyTestAttemptSummary],
    summary="Get my test attempts"
)
async def get_my_attempts(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.get_my_test_attempts(
        course_id, module_id, material_id,
        test_id, current_user, db
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/submit",
    response_model=TestAttemptWithFeedbackResponse,
    summary="Submit all test answers at once"
)
async def submit_all_answers(
    course_id: int, module_id: int, material_id: int,
    test_id: int, attempt_id: int, data: SubmitTestRequest,
    with_feedback: bool = Query(False, description="Generate AI feedback"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.submit_test_all_at_once(
        course_id, module_id, material_id, test_id,
        attempt_id, [a.model_dump() for a in data.answers],
        current_user, db, generate_feedback=with_feedback
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/submit-all",
    response_model=TestAttemptWithFeedbackResponse,
    summary="Submit all test answers at once (legacy path)"
)
async def submit_all_answers_legacy(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    attempt_id: int, data: SubmitTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.submit_test_all_at_once(
        course_id, module_id, material_id, test_id,
        attempt_id, [a.model_dump() for a in data.answers],
        current_user, db, generate_feedback=False
    )


@student_test_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/submit-with-feedback",
    response_model=TestAttemptWithFeedbackResponse,
    summary="Submit all test answers with AI feedback (legacy path)"
)
async def submit_all_answers_with_feedback_legacy(
    course_id: int, module_id: int, material_id: int, test_id: int,
    attempt_id: int, data: SubmitTestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await student_test_service.submit_test_all_at_once(
        course_id, module_id, material_id, test_id,
        attempt_id, [a.model_dump() for a in data.answers],
        current_user, db, generate_feedback=True
    )


@student_test_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/attempts/{attempt_id}/questions/{question_id}/hint",
    response_model=QuestionHintResponse,
    summary="Get question hint"
)
async def get_question_hint(
        course_id: int, module_id: int, material_id: int, test_id: int,
        attempt_id: int, question_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    return await student_test_service.get_question_hint(
        course_id, module_id, material_id, test_id,
        attempt_id, question_id, current_user, db
    )
