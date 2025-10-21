from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, text, UniqueConstraint
from core.database import Base


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    user: Mapped["User"] = relationship("User")
    lesson: Mapped["Material"] = relationship("Material")
