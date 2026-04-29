from sqlalchemy import Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class HomeworkSubmissionFile(Base):
    __tablename__ = "homework_submission_files"
    __table_args__ = (
        UniqueConstraint("submission_id", "file_id", name="uq_homework_submission_file"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        ForeignKey("homework_submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)

    submission: Mapped["HomeworkSubmission"] = relationship("HomeworkSubmission", back_populates="files")
    file: Mapped["File"] = relationship("File", back_populates="homework_submission_files")
