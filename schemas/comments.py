from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from schemas.base import PaginationMeta


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    is_anonymous: bool = Field(False, description="Показывать автора как 'Аноним'")


class CommentReactionRequest(BaseModel):
    is_like: bool = Field(..., description="True - лайк, False - дизлайк")


class CommentResponse(BaseModel):
    id: int
    content: str
    is_anonymous: bool
    author_name: str
    created_at: datetime
    likes_count: int = 0
    dislikes_count: int = 0
    my_reaction: Optional[Literal["like", "dislike"]] = None


class CommentReactionSummaryResponse(BaseModel):
    comment_id: int
    likes_count: int = 0
    dislikes_count: int = 0
    my_reaction: Optional[Literal["like", "dislike"]] = None


class PaginatedCommentsResponse(PaginationMeta):
    comments: list[CommentResponse]
