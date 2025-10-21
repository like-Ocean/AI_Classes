from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, ForeignKey, Text, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    img_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"))

    creator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    creator: Mapped[Optional["User"]] = relationship("User", back_populates="created_courses")
    modules: Mapped[List["Module"]] = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    editors: Mapped[List["CourseEditor"]] = relationship("CourseEditor", back_populates="course", cascade="all, delete-orphan")
    applications: Mapped[List["CourseApplication"]] = relationship("CourseApplication", back_populates="course", cascade="all, delete-orphan")
    enrollments: Mapped[List["CourseEnrollment"]] = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
