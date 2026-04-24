from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.Enums import QuestionType
from schemas.base import ORMModel


# TEST FOR STUDENT (БЕЗ ПРАВИЛЬНЫХ ОТВЕТОВ)

class TestOptionForStudent(ORMModel):
    id: int
    content: str


class TestQuestionForStudent(ORMModel):
    id: int
    text: str
    type: QuestionType
    position: int
    hint_text: Optional[str]
    options: List[TestOptionForStudent] = []


class TestForStudent(ORMModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int
    questions: List[TestQuestionForStudent] = []


# TEST ATTEMPT (ПОПЫТКА ПРОХОЖДЕНИЯ)

class TestAttemptBase(ORMModel):
    id: int
    test_id: int
    user_id: int
    score: Optional[int]
    passed: Optional[bool]
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime]
    blocked_until: Optional[datetime]
    current_question_id: Optional[int]


class TestAttemptResponse(TestAttemptBase):
    pass


# ANSWERS (ОТВЕТЫ СТУДЕНТА)

class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer: Dict[str, Any] = Field(
        ...,
        description="Ответ в формате: {'selected_option_ids': [1, 2]} для выбора или {'text': 'ответ'} для текста"
    )
    hint_used: bool = Field(default=False, description="Была ли использована подсказка")


class QuestionAttemptResponse(ORMModel):
    id: int
    test_attempt_id: int
    question_id: int
    answer: Optional[Dict[str, Any]]
    is_correct: Optional[bool]
    hint_used: bool
    attempt_number: int


# TEST RESULTS (РЕЗУЛЬТАТЫ)

class QuestionResult(BaseModel):
    question_id: int
    question_text: str
    student_answer: Optional[Dict[str, Any]]
    is_correct: bool
    hint_used: bool
    partial_score: int = Field(
        ...,
        description="Частичный балл за вопрос (0-100%)"
    )
    hint_text: Optional[str] = Field(
        None,
        description="Подсказка для неправильного ответа"
    )


class TestResultResponse(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime]
    total_questions: int
    score: Optional[int]
    passed: Optional[bool]
    questions_results: List[QuestionResult] = []


# MY ATTEMPTS (МОИ ПОПЫТКИ)

class MyTestAttemptSummary(ORMModel):
    id: int
    test_id: int
    test_title: str
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime]
    score: Optional[int]
    passed: Optional[bool]


class TestAttemptWithBlockResponse(TestAttemptBase):
    blocked: bool = Field(default=False, description="Заблокирован ли тест")
    consecutive_fails: int = Field(default=0, description="Провалов подряд")
    message: Optional[str] = Field(None, description="Сообщение для студента")


class QuestionAnswerBatch(SubmitAnswerRequest):
    pass


class SubmitTestRequest(BaseModel):
    answers: List[QuestionAnswerBatch] = Field(
        ...,
        description="Список всех ответов на вопросы теста"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "answers": [
                        {
                            "question_id": 18,
                            "answer": {"selected_option_ids": [67, 68, 69]},
                            "hint_used": False
                        },
                        {
                            "question_id": 19,
                            "answer": {"selected_option_ids": [71, 72]},
                            "hint_used": True
                        }
                    ]
                }
            ]
        }
    }


class QuestionHintResponse(BaseModel):
    question_id: int
    hint_text: str = Field(
        ...,
        description="Текст подсказки"
    )


class TestAttemptWithFeedbackResponse(TestAttemptBase):
    blocked: bool = Field(default=False)
    consecutive_fails: int = Field(default=0)
    feedback_text: Optional[str] = Field(None)
    message: Optional[str] = Field(None)
