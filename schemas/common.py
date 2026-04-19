from pydantic import BaseModel
from typing import Optional
from schemas.base import ORMModel


class TestBriefInfo(ORMModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int
