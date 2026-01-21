from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from core.database import Base


class TestAttemptFeedback(Base):
    __tablename__ = "test_attempt_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    test_attempt_id = Column(
        Integer, ForeignKey("test_attempts.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )

    feedback_text = Column(
        Text, nullable=False, comment="Персонализированная рекомендация студенту"
    )

    generated_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    test_attempt = relationship(
        "TestAttempt", back_populates="feedback",
        foreign_keys=[test_attempt_id]
    )
