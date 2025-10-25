from datetime import datetime
from sqlalchemy import Integer, ForeignKey, TIMESTAMP, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class CourseProgress(Base):
    __tablename__ = "course_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_user_course_progress"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)

    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_accessed_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"), nullable=False)

    user: Mapped["User"] = relationship("User")
    course: Mapped["Course"] = relationship("Course")
