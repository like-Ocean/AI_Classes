from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import HTTPException, status

from models import User, Role, Material, Module, Test, Comment, CommentReaction
from models.Enums import RoleType
from helpers.students.access_helper import require_course_enrollment
from schemas.comments import CommentResponse


def build_author_name(user: User, is_anonymous: bool) -> str:
    if is_anonymous:
        return "Аноним"

    parts = [user.first_name, user.last_name]
    full_name = " ".join(p for p in parts if p)
    return full_name or user.email


def normalize_comment_content(content: str) -> str:
    normalized = content.strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment content cannot be empty"
        )
    return normalized


async def is_teacher_or_admin(user: User, db: AsyncSession):
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    return bool(role and role.name in (RoleType.teacher, RoleType.admin))


async def ensure_comment_access_to_course(course_id: int, user: User, db: AsyncSession):
    if await is_teacher_or_admin(user, db):
        return
    await require_course_enrollment(course_id, user, db)


async def validate_material_context(
    course_id: int, module_id: int,
    material_id: int, user: User,
    db: AsyncSession,
) -> Material:
    await ensure_comment_access_to_course(course_id, user, db)

    result = await db.execute(
        select(Material)
        .join(Module, Module.id == Material.module_id)
        .where(
            and_(
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found in this module"
        )
    return material


async def validate_test_context(
    course_id: int, module_id: int, material_id: int,
    test_id: int, user: User, db: AsyncSession,
) -> Test:
    await ensure_comment_access_to_course(course_id, user, db)
    result = await db.execute(
        select(Test)
        .join(Material, Material.id == Test.material_id)
        .join(Module, Module.id == Material.module_id)
        .where(
            and_(
                Test.id == test_id,
                Material.id == material_id,
                Module.id == module_id,
                Module.course_id == course_id
            )
        )
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found in this material",
        )
    return test


async def build_reaction_maps(comment_ids: list[int], current_user_id: int, db: AsyncSession):
    if not comment_ids:
        return {}, {}, {}

    likes_result = await db.execute(
        select(CommentReaction.comment_id, func.count(CommentReaction.id))
        .where(
            and_(
                CommentReaction.comment_id.in_(comment_ids),
                CommentReaction.is_like.is_(True)
            )
        )
        .group_by(CommentReaction.comment_id)
    )
    likes_map = {row[0]: row[1] for row in likes_result.all()}

    dislikes_result = await db.execute(
        select(CommentReaction.comment_id, func.count(CommentReaction.id))
        .where(
            and_(
                CommentReaction.comment_id.in_(comment_ids),
                CommentReaction.is_like.is_(False),
            )
        )
        .group_by(CommentReaction.comment_id)
    )
    dislikes_map = {row[0]: row[1] for row in dislikes_result.all()}

    my_reactions_result = await db.execute(
        select(CommentReaction.comment_id, CommentReaction.is_like)
        .where(
            and_(
                CommentReaction.comment_id.in_(comment_ids),
                CommentReaction.user_id == current_user_id
            )
        )
    )
    my_reactions_map = {row[0]: ("like" if row[1] else "dislike") for row in my_reactions_result.all()}

    return likes_map, dislikes_map, my_reactions_map


def serialize_comment(
    comment: Comment, author: User,
    likes_map: dict[int, int],
    dislikes_map: dict[int, int],
    my_reactions_map: dict[int, str],
) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        is_anonymous=comment.is_anonymous,
        author_name=build_author_name(author, comment.is_anonymous),
        created_at=comment.created_at,
        likes_count=likes_map.get(comment.id, 0),
        dislikes_count=dislikes_map.get(comment.id, 0),
        my_reaction=my_reactions_map.get(comment.id)
    )


async def get_comment_response(comment_id: int, current_user_id: int, db: AsyncSession) -> CommentResponse:
    row_result = await db.execute(
        select(Comment, User)
        .join(User, User.id == Comment.user_id)
        .where(Comment.id == comment_id)
    )
    row = row_result.one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    comment, author = row
    likes_map, dislikes_map, my_reactions_map = await build_reaction_maps([comment.id], current_user_id, db)
    return serialize_comment(comment, author, likes_map, dislikes_map, my_reactions_map)


async def require_comment_access(comment: Comment, user: User, db: AsyncSession):
    if comment.material_id is not None:
        result = await db.execute(
            select(Module.course_id)
            .join(Material, Material.module_id == Module.id)
            .where(Material.id == comment.material_id)
        )
        course_id = result.scalar_one_or_none()
        if course_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment target not found")
        await ensure_comment_access_to_course(course_id, user, db)
        return

    if comment.test_id is not None:
        result = await db.execute(
            select(Module.course_id)
            .join(Material, Material.module_id == Module.id)
            .join(Test, Test.material_id == Material.id)
            .where(Test.id == comment.test_id)
        )
        course_id = result.scalar_one_or_none()
        if course_id is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment target not found")
        await ensure_comment_access_to_course(course_id, user, db)
        return

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid comment target")
