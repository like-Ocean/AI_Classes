from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from schemas.course import CourseResponse, MaterialFileInfo, ModuleResponse
from schemas.user import UserResponse
from models.Enums import ApplicationStatus, MaterialType


# COURSE APPLICATION (ЗАЯВКИ)

class CourseApplicationCreate(BaseModel):
    pass


class CourseApplicationResponse(BaseModel):
    id: int
    course: CourseResponse
    user: UserResponse
    status: ApplicationStatus
    applied_at: datetime
    reviewed_at: Optional[datetime]
    reviewer: Optional[UserResponse] = None

    class Config:
        from_attributes = True


class CourseApplicationDetailResponse(BaseModel):
    id: int
    user: UserResponse
    course: CourseResponse
    status: ApplicationStatus
    applied_at: datetime
    reviewed_at: Optional[datetime]
    reviewer: Optional[UserResponse] = None

    class Config:
        from_attributes = True


# COURSE CATALOG (КАТАЛОГ КУРСОВ)

class CourseCardResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    creator: Optional[UserResponse] = None
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
    is_locked: bool = Field(
        default=False,
        description="Заблокирован ли доступ к материалу"
    )
    lock_reason: Optional[str] = Field(
        None,
        description="Причина блокировки"
    )
    has_tests: bool = Field(
        default=False,
        description="Есть ли тесты у материала"
    )


class ModuleWithProgressResponse(BaseModel):
    id: int
    title: str
    position: int
    course_id: int
    materials: Optional[List[MaterialProgressInfo]] = []
    progress_percentage: float = 0.0


class CourseModulesWithProgressResponse(BaseModel):
    course_id: int
    modules: List[ModuleWithProgressResponse] = []
    overall_progress: float = 0.0


class EnrolledCourseDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    creator: Optional[UserResponse] = None
    created_at: datetime
    overall_progress: float = 0.0
    completed_materials: int = 0
    total_materials: int = 0
    modules: List[ModuleWithProgressResponse] = []


class MaterialDetailForStudent(BaseModel):
    id: int
    module: ModuleResponse
    type: MaterialType
    title: str
    content_url: Optional[str]
    text_content: Optional[str]
    transcript: Optional[str]
    position: int
    files: List[MaterialFileInfo] = []
    has_tests: bool = False
    tests: List['TestBriefInfo'] = []
    is_completed: bool = False
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestBriefInfo(BaseModel):
    id: int
    title: str
    num_questions: int
    time_limit_seconds: Optional[int]
    pass_threshold: int

    class Config:
        from_attributes = True
