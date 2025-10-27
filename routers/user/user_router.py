from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user
from service import user_service
from models import User
from schemas.user import UserResponse, ChangePasswordRequest, UpdateProfileRequest
from schemas.auth import MessageResponse


user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get(
    "/profile",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return await user_service.get_user(current_user)


@user_router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile"
)
async def update_my_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await user_service.update_user_profile(
        user=current_user,
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        group_name=data.group_name,
        db=db
    )
    return user


@user_router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change password"
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await user_service.change_password(
        user=current_user,
        old_password=data.old_password,
        new_password=data.new_password,
        db=db
    )
    return MessageResponse(message="Password successfully changed")
