from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy import Enum as SAEnum
from core.database import Base
from Enums import QuestionType


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType, name="question_type"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    hint_text: Mapped[Optional[str]] = mapped_column(Text)

    test: Mapped["Test"] = relationship("Test", back_populates="questions")
    options: Mapped[List["AnswerOption"]] = relationship(
        "AnswerOption",
        back_populates="question",
        cascade="all, delete-orphan"
    )
