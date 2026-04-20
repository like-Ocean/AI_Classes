from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, Text, ForeignKey, Boolean, DateTime, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        CheckConstraint(
            "(material_id IS NOT NULL AND test_id IS NULL) OR (material_id IS NULL AND test_id IS NOT NULL)",
            name="ck_comments_exactly_one_target"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), nullable=True, index=True
    )
    test_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    author: Mapped["User"] = relationship("User", back_populates="comments")
    material: Mapped[Optional["Material"]] = relationship("Material", back_populates="comments")
    test: Mapped[Optional["Test"]] = relationship("Test", back_populates="comments")
    reactions: Mapped[List["CommentReaction"]] = relationship(
        "CommentReaction",
        back_populates="comment",
        cascade="all, delete-orphan"
    )
