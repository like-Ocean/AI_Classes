from datetime import datetime, timedelta
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from models import User, Role, RefreshToken
from models.Enums import RoleType
from core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, create_password_reset_token,
    decode_password_reset_token,
)
from core.config import settings
from schemas.auth import RegisterRequest
from core.email_service import send_password_reset_email


async def register_user(data: RegisterRequest, db: AsyncSession):
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    result = await db.execute(
        select(Role).where(Role.name == RoleType.student)
    )
    student_role = result.scalar_one_or_none()
    if not student_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Student role not found. Database not initialized properly."
        )

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        group_name=data.group_name,
        role_id=student_role.id
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def login_user(email: str, password: str, db: AsyncSession):
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token_str = create_refresh_token(data={"sub": user.id})

    refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

    db.add(refresh_token)
    await db.commit()

    return access_token, refresh_token_str


async def refresh_access_token(refresh_token_str: str, db: AsyncSession):
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token_str,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False)
        )
    )
    db_token = result.scalar_one_or_none()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or has been revoked"
        )

    if db_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired"
        )

    access_token = create_access_token(data={"sub": user_id})

    return access_token


async def logout_user(refresh_token_str: str, db: AsyncSession):
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == refresh_token_str,
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked.is_(False)
        )
    )
    token = result.scalar_one_or_none()

    if token:
        token.is_revoked = True
        await db.commit()


async def request_password_reset(email: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return

    reset_token = create_password_reset_token(user.id)
    reset_link = f"{settings.PASSWORD_RESET_URL}?token={quote_plus(reset_token)}"
    full_name = " ".join(p for p in [user.first_name, user.last_name] if p)
    await send_password_reset_email(user.email, reset_link, full_name)


async def reset_password(token: str, new_password: str, db: AsyncSession):
    payload = decode_password_reset_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user_id = payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    user.password_hash = get_password_hash(new_password)

    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.is_revoked.is_(False)
        )
        .values(is_revoked=True)
    )

    await db.commit()
