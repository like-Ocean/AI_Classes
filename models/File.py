from datetime import datetime
from sqlalchemy import String, Integer, BigInteger, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
from core.database import Base


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)  # в байтах
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA-256 hash
    uploaded_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"), nullable=False)

    material_files: Mapped[List["MaterialFile"]] = relationship(
        "MaterialFile",
        back_populates="file",
        cascade="all, delete-orphan"
    )
