from typing import List, Optional
from pydantic import BaseModel, Field
from schemas.base import PaginationMeta


class StudentProgressRow(BaseModel):
    user_id: int
    full_name: str
    group_name: Optional[str] = None
    completed_lessons: int = 0
    completed_tests: int = 0
    completed_homework: int = 0
    total_tests: int = 0
    remaining_tests: int = 0
    total_homework: int = 0
    remaining_homework: int = 0
    progress_percentage: float = 0.0


class CourseProgressOverviewResponse(PaginationMeta):
    course_id: int
    total_materials: int = 0
    total_tests: int = 0
    total_homework: int = 0
    students: List[StudentProgressRow] = Field(default_factory=list)
    least_active: List[StudentProgressRow] = Field(default_factory=list)
