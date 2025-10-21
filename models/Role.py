from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, Enum as SAEnum
from core.database import Base
from Enums import RoleType


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[RoleType] = mapped_column(SAEnum(RoleType, name="role_type"), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship("User", back_populates="role")
