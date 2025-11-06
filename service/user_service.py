from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from models import User
from core.security import verify_password, get_password_hash
from schemas.user import UserResponse


async def get_user(user: User):
    return UserResponse.model_validate(user)


async def update_user_profile(
        user: User, first_name: str,
        last_name: str, patronymic: str | None,
        group_name: str | None, db: AsyncSession
):
    user.first_name = first_name
    user.last_name = last_name
    user.patronymic = patronymic
    user.group_name = group_name

    await db.commit()
    await db.refresh(user)

    return user


async def change_password(
        user: User, old_password: str,
        new_password: str, db: AsyncSession
):
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    if verify_password(new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password"
        )

    user.password_hash = get_password_hash(new_password)

    await db.commit()
