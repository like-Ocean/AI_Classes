from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from service import auth_service
from schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshTokenRequest, MessageResponse
)
from schemas.user import UserResponse

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new student"
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(data, db)
    return user


@auth_router.post("/login", response_model=TokenResponse, summary="Login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    access_token, refresh_token = await auth_service.login_user(
        data.email,
        data.password,
        db
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@auth_router.post(
    "/refresh",
    response_model=dict,
    summary="Refresh access token"
)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    access_token = await auth_service.refresh_access_token(data.refresh_token, db)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@auth_router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout"
)
async def logout(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.logout_user(data.refresh_token, db)
    return MessageResponse(message="Successfully logged out")
