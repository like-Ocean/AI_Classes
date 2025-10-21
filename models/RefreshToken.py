from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, TIMESTAMP, ForeignKey, text
from core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(512), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, server_default=text("NOW()"))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
