from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from models.Enums import RoleType


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    patronymic: Optional[str] = Field(None, max_length=100)
    group_name: Optional[str] = Field(None, max_length=100)
    role: RoleType = Field(..., description="Роль пользователя")


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    patronymic: Optional[str] = Field(None, max_length=100)
    group_name: Optional[str] = Field(None, max_length=100)
    role: Optional[RoleType] = None


class UserListResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    patronymic: Optional[str]
    group_name: Optional[str]
    role_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedUsersResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    users: List[UserListResponse]


class StatisticsResponse(BaseModel):
    total_users: int
    total_students: int
    total_teachers: int
    total_courses: int
    total_enrollments: int
    total_applications_pending: int


class ChangeUserRoleRequest(BaseModel):
    role: RoleType = Field(..., description="Новая роль")
