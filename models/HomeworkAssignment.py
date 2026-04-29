from datetime import datetime
from typing import List
from sqlalchemy import Integer, Text, DateTime, ForeignKey, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class HomeworkAssignment(Base):
    __tablename__ = "homework_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_formats: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    submissions: Mapped[List["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
