from datetime import datetime
from typing import Optional, List
from sqlalchemy import Integer, Text, DateTime, ForeignKey, UniqueConstraint, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_homework_submission_assignment_student"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("homework_assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), server_default=text("'pending_review'"), nullable=False)
    review_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    assignment: Mapped["HomeworkAssignment"] = relationship(
        "HomeworkAssignment", back_populates="submissions"
    )
    student: Mapped["User"] = relationship(
        "User", back_populates="homework_submissions", foreign_keys=[student_id]
    )
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
    files: Mapped[List["HomeworkSubmissionFile"]] = relationship(
        "HomeworkSubmissionFile",
        back_populates="submission",
        cascade="all, delete-orphan"
    )
