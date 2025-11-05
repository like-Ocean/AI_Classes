from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from schemas.course import ModuleResponse, MaterialResponse
from models.Enums import ApplicationStatus


# COURSE APPLICATION (ЗАЯВКИ)

class CourseApplicationCreate(BaseModel):
    pass


class CourseApplicationResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    status: ApplicationStatus
    applied_at: datetime
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]

    class Config:
        from_attributes = True


# COURSE CATALOG (КАТАЛОГ КУРСОВ)

class CourseCardResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    creator_id: Optional[int]
    created_at: datetime
    is_enrolled: bool = False
    application_status: Optional[ApplicationStatus] = None

    class Config:
        from_attributes = True


class PaginatedCoursesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    courses: List[CourseCardResponse]


# STUDENT PROGRESS (ПРОГРЕСС)

class LessonProgressResponse(BaseModel):
    id: int
    lesson_id: int
    completed_at: datetime

    class Config:
        from_attributes = True


class CourseProgressResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    completed_items: int
    total_items: int
    progress_percentage: float
    last_accessed_at: datetime

    class Config:
        from_attributes = True


# ENROLLED COURSE (МОИ КУРСЫ)

class EnrolledCourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    progress: Optional[CourseProgressResponse] = None

    class Config:
        from_attributes = True


class MyCoursesResponse(BaseModel):
    courses: List[EnrolledCourseResponse]


# MODULE WITH PROGRESS (МОДУЛЬ С ПРОГРЕССОМ)

class MaterialProgressInfo(BaseModel):
    material_id: int
    title: str
    type: str
    position: int
    is_completed: bool
    completed_at: Optional[datetime] = None


class ModuleWithProgressResponse(BaseModel):
    id: int
    title: str
    position: int
    course_id: int
    materials: List[MaterialProgressInfo] = []
    progress_percentage: float = 0.0
