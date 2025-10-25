from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Boolean, text
from core.database import Base


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    num_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    time_limit_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    pass_threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"), nullable=False)
    generated_by_nn: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    module_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), nullable=True
    )
    material_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("materials.id", ondelete="SET NULL"),
        nullable=True, index=True
    )

    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="test",
        cascade="all, delete-orphan"
    )
    attempts: Mapped[List["TestAttempt"]] = relationship(
        "TestAttempt",
        back_populates="test",
        cascade="all, delete-orphan"
    )
