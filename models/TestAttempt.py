from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Boolean, TIMESTAMP, text, Index
from core.database import Base


class TestAttempt(Base):
    __tablename__ = "test_attempts"
    __table_args__ = (
        Index("idx_user_test_attempt", "user_id", "test_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    current_question_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("questions.id", ondelete="SET NULL")
    )

    question_attempts: Mapped[List["QuestionAttempt"]] = relationship(
        "QuestionAttempt",
        back_populates="test_attempt",
        cascade="all, delete-orphan"
    )
    test: Mapped["Test"] = relationship("Test", back_populates="attempts")
    user: Mapped["User"] = relationship("User")
    current_question: Mapped[Optional["Question"]] = relationship("Question")
