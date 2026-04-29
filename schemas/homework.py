from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from models.Enums import (
    HomeworkSubmissionFormat,
    HomeworkSubmissionStatus, HomeworkReviewResult
)
from schemas.file import FileResponse
from schemas.base import ORMModel


class HomeworkCreateRequest(BaseModel):
    description: str = Field(..., min_length=1, max_length=5000)
    allowed_formats: List[HomeworkSubmissionFormat] = Field(..., min_length=1)
    deadline: datetime


class HomeworkResponse(ORMModel):
    id: int
    course_id: int
    module_id: int
    material_id: int
    created_by: Optional[int] = None
    description: str
    allowed_formats: List[HomeworkSubmissionFormat]
    deadline: datetime
    created_at: datetime


class HomeworkSubmissionResponse(ORMModel):
    id: int
    assignment_id: int
    student_id: int
    text_answer: Optional[str] = None
    status: HomeworkSubmissionStatus
    review_result: Optional[HomeworkReviewResult] = None
    review_comment: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    submitted_at: datetime
    updated_at: datetime
    files: List[FileResponse] = []


class HomeworkReviewRequest(BaseModel):
    review_result: HomeworkReviewResult
    review_comment: Optional[str] = Field(None, max_length=5000)


class HomeworkStudentItemResponse(HomeworkResponse):
    status: Optional[HomeworkSubmissionStatus] = None
    can_resubmit: bool = False
    submission: Optional[HomeworkSubmissionResponse] = None
