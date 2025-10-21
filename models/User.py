import datetime
from uuid import uuid4
from typing import List
from sqlalchemy import String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core.database import Base
from werkzeug.security import generate_password_hash, check_password_hash


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[uuid4] = mapped_column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String(100))
    group_name: Mapped[str | None] = mapped_column(String(100))

    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="SET NULL"))
    role: Mapped["Role"] = relationship("Role", back_populates="users")

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    created_courses: Mapped[List["Course"]] = relationship(
        "Course",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    applications: Mapped[List["CourseApplication"]] = relationship(
        "CourseApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    enrollments: Mapped[List["CourseEnrollment"]] = relationship(
        "CourseEnrollment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    editable_courses: Mapped[List["CourseEditor"]] = relationship(
        "CourseEditor",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    lesson_progress: Mapped[List["LessonProgress"]] = relationship(
        "LessonProgress",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("NOW()"), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)
