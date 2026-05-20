from math import ceil
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status
from models import User, Comment, CommentReaction
from helpers.students.comment_helper import (
    normalize_comment_content, validate_material_context,
    validate_test_context, build_reaction_maps,
    serialize_comment, get_comment_response, require_comment_access,
    is_teacher_or_admin,
)
from schemas.comments import (
    CreateCommentRequest, CommentResponse,
    CommentReactionRequest, CommentReactionSummaryResponse,
    PaginatedCommentsResponse,
)


async def create_material_comment(
    course_id: int, module_id: int,
    material_id: int, data: CreateCommentRequest,
    user: User, db: AsyncSession,
) -> CommentResponse:
    await validate_material_context(
        course_id, module_id, 
        material_id, user, db
    )

    comment = Comment(
        user_id=user.id,
        material_id=material_id,
        content=normalize_comment_content(data.content),
        is_anonymous=data.is_anonymous,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return await get_comment_response(comment.id, user.id, db)


async def create_test_comment(
    course_id: int, module_id: int,
    material_id: int, test_id: int,
    data: CreateCommentRequest,
    user: User, db: AsyncSession,
) -> CommentResponse:
    await validate_test_context(course_id, module_id, material_id, test_id, user, db)

    comment = Comment(
        user_id=user.id,
        test_id=test_id,
        content=normalize_comment_content(data.content),
        is_anonymous=data.is_anonymous,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return await get_comment_response(comment.id, user.id, db)


async def list_material_comments(
    course_id: int, module_id: int, material_id: int,
    page: int, page_size: int, user: User, db: AsyncSession,
) -> PaginatedCommentsResponse:
    await validate_material_context(course_id, module_id, material_id, user, db)

    total_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.material_id == material_id)
    )
    total = total_result.scalar() or 0
    total_pages = ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size

    rows_result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .where(Comment.material_id == material_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = rows_result.all()

    comments = [row[0] for row in rows]
    comment_ids = [c.id for c in comments]
    likes_map, dislikes_map, my_reactions_map = await build_reaction_maps(comment_ids, user.id, db)

    return PaginatedCommentsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        comments=[
            serialize_comment(comment, author, likes_map, dislikes_map, my_reactions_map)
            for comment, author in rows
        ],
    )


async def list_test_comments(
    course_id: int, module_id: int, material_id: int,
    test_id: int, page: int,
    page_size: int, user: User, db: AsyncSession,
) -> PaginatedCommentsResponse:
    await validate_test_context(
        course_id, module_id, material_id, test_id, user, db
    )

    total_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.test_id == test_id)
    )
    total = total_result.scalar() or 0
    total_pages = ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size

    rows_result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .where(Comment.test_id == test_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    rows = rows_result.all()

    comments = [row[0] for row in rows]
    comment_ids = [c.id for c in comments]
    likes_map, dislikes_map, my_reactions_map = await build_reaction_maps(
        comment_ids, user.id, db
    )

    return PaginatedCommentsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        comments=[
            serialize_comment(comment, author, likes_map, dislikes_map, my_reactions_map)
            for comment, author in rows
        ],
    )


async def react_to_comment(
    comment_id: int, data: CommentReactionRequest,
    user: User, db: AsyncSession,
) -> CommentReactionSummaryResponse:
    comment_result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    await require_comment_access(comment, user, db)

    reaction_result = await db.execute(
        select(CommentReaction).where(
            and_(
                CommentReaction.comment_id == comment_id,
                CommentReaction.user_id == user.id,
            )
        )
    )
    existing = reaction_result.scalar_one_or_none()

    if existing and existing.is_like == data.is_like:
        await db.delete(existing)
        my_reaction: Optional[str] = None
    elif existing:
        existing.is_like = data.is_like
        my_reaction = "like" if data.is_like else "dislike"
    else:
        db.add(CommentReaction(
            comment_id=comment_id,
            user_id=user.id,
            is_like=data.is_like,
        ))
        my_reaction = "like" if data.is_like else "dislike"

    await db.commit()

    counts_result = await db.execute(
        select(CommentReaction.is_like, func.count(CommentReaction.id))
        .where(CommentReaction.comment_id == comment_id)
        .group_by(CommentReaction.is_like)
    )

    likes_count = 0
    dislikes_count = 0
    for is_like, count in counts_result.all():
        if is_like:
            likes_count = count
        else:
            dislikes_count = count

    return CommentReactionSummaryResponse(
        comment_id=comment_id,
        likes_count=likes_count,
        dislikes_count=dislikes_count,
        my_reaction=my_reaction,
    )


async def delete_comment(comment_id: int, user: User, db: AsyncSession) -> dict:
    comment_result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = comment_result.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
        )

    if not await is_teacher_or_admin(user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers or admins can delete comments"
        )

    await require_comment_access(comment, user, db)

    await db.delete(comment)
    await db.commit()

    return {"message": "Comment deleted successfully"}
