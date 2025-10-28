from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy import Enum as SAEnum
from core.database import Base
from .Enums import MaterialType


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[MaterialType] = mapped_column(SAEnum(MaterialType, name="material_type"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_url: Mapped[Optional[str]] = mapped_column(String(500))
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    module: Mapped["Module"] = relationship("Module", back_populates="materials")
    tests: Mapped[List["Test"]] = relationship(
        "Test",
        back_populates="material",
        cascade="all, delete-orphan"
    )
    material_files: Mapped[List["MaterialFile"]] = relationship(
        "MaterialFile",
        back_populates="material",
        cascade="all, delete-orphan"
    )
