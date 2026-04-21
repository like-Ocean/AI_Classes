from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.dependencies import get_current_user
from models import User
from schemas.comments import (
    CreateCommentRequest, CommentResponse, PaginatedCommentsResponse,
    CommentReactionRequest, CommentReactionSummaryResponse,
)
from service import student_comment_service


student_comment_router = APIRouter(tags=["Student / Комментарии"])


@student_comment_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/comments",
    response_model=PaginatedCommentsResponse,
    summary="List comments under material"
)
async def list_material_comments(
    course_id: int, module_id: int, material_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await student_comment_service.list_material_comments(
        course_id, module_id, material_id,
        page, page_size,
        current_user, db
    )


@student_comment_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/comments",
    response_model=CommentResponse, status_code=status.HTTP_201_CREATED,
    summary="Create comment under material"
)
async def create_material_comment(
    course_id: int, module_id: int,
    material_id: int, data: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await student_comment_service.create_material_comment(
        course_id, module_id, material_id,
        data, current_user, db
    )


@student_comment_router.get(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/comments",
    response_model=PaginatedCommentsResponse,
    summary="List comments under test"
)
async def list_test_comments(
    course_id: int, module_id: int, material_id: int,
    test_id: int,
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await student_comment_service.list_test_comments(
        course_id, module_id, material_id,
        test_id, page, page_size,
        current_user, db
    )


@student_comment_router.post(
    "/my-courses/{course_id}/modules/{module_id}/materials/{material_id}/tests/{test_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create comment under test"
)
async def create_test_comment(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    data: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await student_comment_service.create_test_comment(
        course_id, module_id, material_id,
        test_id, data, current_user, db
    )


@student_comment_router.post(
    "/comments/{comment_id}/reaction",
    response_model=CommentReactionSummaryResponse,
    summary="Like or dislike comment"
)
async def react_to_comment(
    comment_id: int, data: CommentReactionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await student_comment_service.react_to_comment(
        comment_id, data, 
        current_user, db
    )
