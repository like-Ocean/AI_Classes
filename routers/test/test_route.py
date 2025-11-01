from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_teacher
from service import test_service
from models import User
from schemas.tests import (
    TestCreateRequest, TestUpdateRequest, TestResponse,
    TestWithQuestionsResponse, QuestionCreateRequest,
    QuestionUpdateRequest, QuestionResponse,
    AnswerOptionCreate, AnswerOptionUpdate, AnswerOptionResponse
)
from schemas.auth import MessageResponse

test_router = APIRouter(prefix="/test", tags=["Test"])


# НЕ ТЕСТИЛ!!!
@test_router.post(
    "/materials/{material_id}/tests",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create test for material"
)
async def create_test(
        material_id: int, data: TestCreateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    test = await test_service.create_test(
        material_id, data, current_teacher, db
    )
    return test


@test_router.get(
    "/tests/{test_id}",
    response_model=TestWithQuestionsResponse,
    summary="Get test details"
)
async def get_test(
        test_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    test = await test_service.get_test_detail(
        test_id, current_teacher, db
    )
    return test


@test_router.put(
    "/tests/{test_id}",
    response_model=TestResponse, summary="Update test"
)
async def update_test(
        test_id: int, data: TestUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    test = await test_service.update_test(
        test_id, data, current_teacher, db
    )
    return test


@test_router.delete(
    "/tests/{test_id}",
    response_model=MessageResponse, summary="Delete test"
)
async def delete_test(
        test_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await test_service.delete_test(test_id, current_teacher, db)
    return MessageResponse(message="Test successfully deleted")


# QUESTIONS
@test_router.post(
    "/tests/{test_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create question"
)
async def create_question(
        test_id: int, data: QuestionCreateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    question = await test_service.create_question(
        test_id, data, current_teacher, db
    )
    return question


@test_router.put(
    "/questions/{question_id}",
    response_model=QuestionResponse, summary="Update question"
)
async def update_question(
        question_id: int, data: QuestionUpdateRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    question = await test_service.update_question(
        question_id, data, current_teacher, db
    )
    return question


@test_router.delete(
    "/questions/{question_id}",
    response_model=MessageResponse, summary="Delete question"
)
async def delete_question(
        question_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await test_service.delete_question(question_id, current_teacher, db)
    return MessageResponse(message="Question successfully deleted")


# ANSWER

@test_router.post(
    "/questions/{question_id}/options",
    response_model=AnswerOptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add answer option"
)
async def add_answer_option(
        question_id: int, data: AnswerOptionCreate,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    option = await test_service.add_answer_option(
        question_id, data, current_teacher, db
    )
    return option


@test_router.put(
    "/options/{option_id}",
    response_model=AnswerOptionResponse,
    summary="Update answer option"
)
async def update_answer_option(
        option_id: int, data: AnswerOptionUpdate,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    option = await test_service.update_answer_option(option_id, data, current_teacher, db)
    return option


@test_router.delete(
    "/options/{option_id}",
    response_model=MessageResponse,
    summary="Delete answer option"
)
async def delete_answer_option(
        option_id: int,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    await test_service.delete_answer_option(option_id, current_teacher, db)
    return MessageResponse(message="Answer option successfully deleted")
