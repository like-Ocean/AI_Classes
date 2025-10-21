from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Text, Boolean, ForeignKey, text
from core.database import Base


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)

    question: Mapped["Question"] = relationship("Question", back_populates="options")
