from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey
from core.database import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey(
        "courses.id",
        ondelete="CASCADE"
    ), nullable=False)

    course: Mapped["Course"] = relationship("Course", back_populates="modules")
    materials: Mapped[List["Material"]] = relationship(
        "Material",
        back_populates="module",
        cascade="all, delete-orphan"
    )

