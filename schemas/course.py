from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from models.Enums import MaterialType
from schemas.user import UserResponse
from schemas.file import FileResponse
from schemas.common import TestBriefInfo
from schemas.base import ORMModel, PaginationMeta


class CourseRoleFilter(str, Enum):
    all = "all"
    created = "created"
    editor = "editor"


# COURSE SCHEMAS
class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class CourseResponse(ORMModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    created_at: datetime
    creator: Optional[UserResponse] = None


# MODULE SCHEMAS
class ModuleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    position: int = Field(..., ge=1, description="Позиция модуля в курсе")


class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[int] = Field(None, ge=1)


class ModuleResponse(ORMModel):
    id: int
    title: str
    position: int
    course_id: int


# MATERIAL
class MaterialCreateRequest(BaseModel):
    type: MaterialType
    title: str = Field(..., min_length=1, max_length=255)
    content_url: Optional[str] = Field(None, max_length=500)
    text_content: Optional[str] = None
    transcript: Optional[str] = None
    position: int = Field(..., ge=1, description="Позиция материала в модуле")

    @field_validator('transcript')
    @classmethod
    def validate_transcript(cls, v, info):
        """transcript только для type=video"""
        material_type = info.data.get('type')
        if material_type == MaterialType.video:
            return v
        return None

    @field_validator('text_content')
    @classmethod
    def validate_text_content(cls, v, info):
        """text_content только для text, document, presentation"""
        material_type = info.data.get('type')
        if material_type in [MaterialType.text, MaterialType.document, MaterialType.presentation]:
            return v
        return None


class MaterialUpdateRequest(BaseModel):
    type: Optional[MaterialType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content_url: Optional[str] = Field(None, max_length=500)
    text_content: Optional[str] = None
    transcript: Optional[str] = None
    position: Optional[int] = Field(None, ge=1)


class MaterialFileInfo(ORMModel):
    id: int
    file_id: int
    file: FileResponse


class MaterialResponse(ORMModel):
    id: int
    module_id: int
    type: MaterialType
    title: str
    content_url: Optional[str]
    text_content: Optional[str]
    transcript: Optional[str]
    position: int
    files: List[MaterialFileInfo] = []


class ModuleWithMaterialsResponse(ModuleResponse):
    materials: List[MaterialResponse] = []


class CourseWithModulesResponse(CourseResponse):
    modules: List[ModuleWithMaterialsResponse] = []


class AddEditorRequest(BaseModel):
    user_id: int = Field(..., description="ID преподавателя")


class EditorResponse(ORMModel):
    id: int
    user: UserResponse
    course_id: int
    granted_at: datetime
    granted_by: Optional[int]

class PaginatedEditorsResponse(PaginationMeta):
    editors: List[EditorResponse]


class MaterialDetailForTeacher(ORMModel):
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
    tests: List[TestBriefInfo] = []

