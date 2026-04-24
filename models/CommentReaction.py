from datetime import datetime
from sqlalchemy import Integer, ForeignKey, Boolean, DateTime, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class CommentReaction(Base):
    __tablename__ = "comment_reactions"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_reactions_comment_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    comment_id: Mapped[int] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_like: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    comment: Mapped["Comment"] = relationship("Comment", back_populates="reactions")
    user: Mapped["User"] = relationship("User", back_populates="comment_reactions")
