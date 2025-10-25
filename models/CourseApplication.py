from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, String, text
from core.database import Base


class CourseApplication(Base):
    __tablename__ = "course_applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'pending'"), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)

    reviewer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reviewed_by]
    )
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="applications"
    )
    course: Mapped["Course"] = relationship(
        "Course",
        back_populates="applications"
    )
