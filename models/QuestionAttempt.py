from typing import Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Boolean, ForeignKey, text, UniqueConstraint
from core.database import Base


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"
    __table_args__ = (
        UniqueConstraint(
            "test_attempt_id",
            "question_id",
            "attempt_number",
            name="uq_test_question_attempt"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    hint_used: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    question: Mapped["Question"] = relationship("Question")
    test_attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="question_attempts")
