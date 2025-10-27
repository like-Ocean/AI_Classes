from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models.Enums import MaterialType


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    img_url: Optional[str] = Field(None, max_length=500)


class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    img_url: Optional[str]
    created_at: datetime
    creator_id: Optional[int]

    class Config:
        from_attributes = True


class ModuleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    position: int = Field(..., ge=1, description="Позиция модуля в курсе")


class ModuleUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    position: Optional[int] = Field(None, ge=1)


class ModuleResponse(BaseModel):
    id: int
    title: str
    position: int
    course_id: int

    class Config:
        from_attributes = True


class MaterialCreateRequest(BaseModel):
    type: MaterialType
    title: str = Field(..., min_length=1, max_length=255)
    content_url: Optional[str] = Field(None, max_length=500)
    text_content: Optional[str] = None
    transcript: Optional[str] = None
    position: int = Field(..., ge=1, description="Позиция материала в модуле")


class MaterialUpdateRequest(BaseModel):
    type: Optional[MaterialType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content_url: Optional[str] = Field(None, max_length=500)
    text_content: Optional[str] = None
    transcript: Optional[str] = None
    position: Optional[int] = Field(None, ge=1)


class MaterialResponse(BaseModel):
    id: int
    module_id: int
    type: MaterialType
    title: str
    content_url: Optional[str]
    text_content: Optional[str]
    transcript: Optional[str]
    position: int

    class Config:
        from_attributes = True


class ModuleDetailResponse(ModuleResponse):
    materials: List[MaterialResponse] = []


class CourseDetailResponse(CourseResponse):
    modules: List[ModuleDetailResponse] = []


class AddEditorRequest(BaseModel):
    user_id: int = Field(..., description="ID преподавателя")


class EditorResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    granted_at: datetime
    granted_by: Optional[int]

    class Config:
        from_attributes = True
