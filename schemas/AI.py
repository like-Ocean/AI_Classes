from typing import List
from pydantic import BaseModel, Field


class GenerateTestRequest(BaseModel):
    num_questions: int = Field(5, ge=3, le=20, description="Количество вопросов (3-20)")
    question_types: List[str] = Field(
        default=["single", "multiple"],
        description="Типы вопросов"
    )
    pass_threshold: int = Field(70, ge=0, le=100, description="Проходной балл (%)")
    time_limit_minutes: int = Field(15, ge=5, le=180, description="Лимит времени (мин)")