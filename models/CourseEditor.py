from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, ForeignKey, DateTime, text
from core.database import Base


class CourseEditor(Base):
    __tablename__ = "course_editors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    granted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="editors")
    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="editable_courses"
    )
    granter: Mapped["User"] = relationship(
        "User",
        foreign_keys=[granted_by]
    )
