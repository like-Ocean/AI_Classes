from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_teacher
from models import User
from AI import generate_test_with_ai
from schemas.tests import TestWithQuestionsResponse
from schemas.AI import GenerateTestRequest

ai_router = APIRouter(prefix="/ai", tags=["AI"])


@ai_router.post(
    "/courses/{course_id}/modules/{module_id}/materials/{material_id}/generate-test",
    response_model=TestWithQuestionsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate test with AI"
)
async def generate_test(
        course_id: int, module_id: int,
        material_id: int, data: GenerateTestRequest,
        current_teacher: User = Depends(get_current_teacher),
        db: AsyncSession = Depends(get_db)
):
    test = await generate_test_with_ai(
        course_id=course_id, module_id=module_id,
        material_id=material_id,
        num_questions=data.num_questions,
        question_types=data.question_types,
        pass_threshold=data.pass_threshold,
        time_limit_minutes=data.time_limit_minutes,
        user=current_teacher, db=db
    )
    return test
