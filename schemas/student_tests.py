from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from models.Enums import QuestionType


# TEST FOR STUDENT (БЕЗ ПРАВИЛЬНЫХ ОТВЕТОВ)

class TestOptionForStudent(BaseModel):
    id: int
    content: str

    class Config:
        from_attributes = True


class TestQuestionForStudent(BaseModel):
    id: int
    text: str
    type: QuestionType
    position: int
    hint_text: Optional[str]
    options: List[TestOptionForStudent] = []

    class Config:
        from_attributes = True


class TestForStudent(BaseModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int
    questions: List[TestQuestionForStudent] = []

    class Config:
        from_attributes = True


# TEST ATTEMPT (ПОПЫТКА ПРОХОЖДЕНИЯ)

class TestAttemptResponse(BaseModel):
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

    class Config:
        from_attributes = True


# ANSWERS (ОТВЕТЫ СТУДЕНТА)

class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer: Dict[str, Any] = Field(
        ...,
        description="Ответ в формате: {'selected_option_ids': [1, 2]} для выбора или {'text': 'ответ'} для текста"
    )
    hint_used: bool = Field(default=False, description="Была ли использована подсказка")


class QuestionAttemptResponse(BaseModel):
    id: int
    test_attempt_id: int
    question_id: int
    answer: Optional[Dict[str, Any]]
    is_correct: Optional[bool]
    hint_used: bool
    attempt_number: int

    class Config:
        from_attributes = True


# TEST RESULTS (РЕЗУЛЬТАТЫ)

class QuestionResult(BaseModel):
    question_id: int
    question_text: str
    student_answer: Optional[Dict[str, Any]]
    correct_option_ids: List[int]
    is_correct: bool
    hint_used: bool
    partial_score: int = Field(
        ...,
        description="Частичный балл за вопрос (0-100%)"
    )


class TestResultResponse(BaseModel):
    attempt_id: int
    test_id: int
    test_title: str
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime]
    total_questions: int
    correct_answers: int
    score: Optional[int]
    passed: Optional[bool]
    questions_results: List[QuestionResult] = []


# MY ATTEMPTS (МОИ ПОПЫТКИ)

class MyTestAttemptSummary(BaseModel):
    id: int
    test_id: int
    test_title: str
    attempt_number: int
    started_at: datetime
    finished_at: Optional[datetime]
    score: Optional[int]
    passed: Optional[bool]

    class Config:
        from_attributes = True


class TestAttemptWithBlockResponse(BaseModel):
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

    blocked: bool = Field(default=False, description="Заблокирован ли тест")
    consecutive_fails: int = Field(default=0, description="Провалов подряд")
    message: Optional[str] = Field(None, description="Сообщение для студента")

    class Config:
        from_attributes = True
