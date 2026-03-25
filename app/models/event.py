from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from app.db.database import Base


class FeatureEvent(Base):
    __tablename__ = "feature_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    user_id = Column(String(255), nullable=False, index=True)
    feature = Column(String(255), nullable=False, index=True)
    # storing metadata as json string
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_feature_timestamp", "feature", "timestamp"),
        Index("ix_user_feature", "user_id", "feature"),
    )
