from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, Boolean, TIMESTAMP, text
from core.database import Base


class TestAttempt(Base):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[Optional[int]] = mapped_column(Integer)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean)
    attempts_count: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP)

    question_attempts: Mapped[List["QuestionAttempt"]] = relationship(
        "QuestionAttempt",
        back_populates="test_attempt",
        cascade="all, delete-orphan"
    )
    test: Mapped["Test"] = relationship("Test", back_populates="attempts")
