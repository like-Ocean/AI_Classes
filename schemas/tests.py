from pydantic import BaseModel, Field
from typing import Optional, List
from models.Enums import QuestionType


class TestCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    num_questions: int = Field(..., ge=1, description="Количество вопросов")
    time_limit_seconds: Optional[int] = Field(None, ge=60, description="Лимит времени в секундах")
    pass_threshold: int = Field(..., ge=0, le=100, description="Проходной балл в процентах")
    status: str = Field(default="draft", description="Статус теста: draft, published")


class TestUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    num_questions: Optional[int] = Field(None, ge=1)
    time_limit_seconds: Optional[int] = Field(None, ge=60)
    pass_threshold: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = Field(None, description="draft или published")


class TestResponse(BaseModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int
    status: str
    generated_by_nn: bool
    created_by: Optional[int]
    module_id: Optional[int]
    material_id: Optional[int]

    class Config:
        from_attributes = True


class AnswerOptionCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_correct: bool = Field(..., description="Правильный ли это ответ")


class AnswerOptionResponse(BaseModel):
    id: int
    question_id: int
    content: str
    is_correct: bool

    class Config:
        from_attributes = True


class QuestionCreateRequest(BaseModel):
    text: str = Field(..., min_length=1)
    type: QuestionType
    position: int = Field(..., ge=1, description="Позиция вопроса в тесте")
    hint_text: Optional[str] = None
    options: List[AnswerOptionCreate] = Field(
        default=[],
        description="Варианты ответов (для single и multiple)"
    )


class QuestionUpdateRequest(BaseModel):
    text: Optional[str] = Field(None, min_length=1)
    type: Optional[QuestionType] = None
    position: Optional[int] = Field(None, ge=1)
    hint_text: Optional[str] = None


class QuestionResponse(BaseModel):
    id: int
    test_id: int
    text: str
    type: QuestionType
    position: int
    hint_text: Optional[str]
    options: List[AnswerOptionResponse] = []

    class Config:
        from_attributes = True


class TestWithQuestionsResponse(TestResponse):
    questions: List[QuestionResponse] = []


class AnswerOptionUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    is_correct: Optional[bool] = None
