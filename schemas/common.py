from pydantic import BaseModel
from typing import Optional


class TestBriefInfo(BaseModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int

    class Config:
        from_attributes = True
