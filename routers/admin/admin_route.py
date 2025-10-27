from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from math import ceil
from core.database import get_db
from core.dependencies import get_current_admin
from service import admin_service
from models import User
from models.Enums import RoleType
from schemas.admin import (
    CreateUserRequest, UpdateUserRequest,
    UserListResponse, PaginatedUsersResponse,
    StatisticsResponse, ChangeUserRoleRequest
)
from schemas.auth import MessageResponse

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.post(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user"
)
async def create_user(
        data: CreateUserRequest,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    user = await admin_service.create_user(data, db)
    return user


@admin_router.get(
    "/users",
    response_model=PaginatedUsersResponse,
    summary="Get users list"
)
async def get_users(
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
        role: Optional[RoleType] = Query(None, description="Фильтр по роли"),
        search: Optional[str] = Query(None, description="Поиск по имени/email"),
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    users, total = await admin_service.get_users_list(
        db=db, page=page,
        page_size=page_size, role_filter=role,
        search=search
    )
    total_pages = ceil(total / page_size) if total > 0 else 0

    return PaginatedUsersResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        users=[UserListResponse.model_validate(user) for user in users]
    )


@admin_router.get(
    "/users/{user_id}",
    response_model=UserListResponse,
    summary="Get user by ID"
)
async def get_user(
        user_id: int,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    user = await admin_service.get_user_by_id(user_id, db)
    return user


@admin_router.put(
    "/users/{user_id}",
    response_model=UserListResponse,
    summary="Update user"
)
async def update_user(
        user_id: int,
        data: UpdateUserRequest,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    user = await admin_service.update_user(user_id, data, db)
    return user


@admin_router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    summary="Delete user"
)
async def delete_user(
        user_id: int,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    await admin_service.delete_user(user_id, current_admin, db)
    return MessageResponse(message="User successfully deleted")


@admin_router.patch(
    "/users/{user_id}/role",
    response_model=UserListResponse,
    summary="Change user role"
)
async def change_user_role(
        user_id: int,
        data: ChangeUserRoleRequest,
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    user = await admin_service.change_user_role(
        user_id, data.role, current_admin, db
    )
    return user


@admin_router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get platform statistics"
)
async def get_statistics(
        current_admin: User = Depends(get_current_admin),
        db: AsyncSession = Depends(get_db)
):
    stats = await admin_service.get_statistics(db)
    return stats
