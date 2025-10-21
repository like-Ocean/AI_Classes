from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Boolean, ForeignKey, text
from core.database import Base


class QuestionAttempt(Base):
    __tablename__ = "question_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer: Mapped[Optional[str]] = mapped_column(Text)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean)
    hint_used: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    question: Mapped["Question"] = relationship("Question")
    test_attempt: Mapped["TestAttempt"] = relationship("TestAttempt", back_populates="question_attempts")
