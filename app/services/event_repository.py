import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.event import FeatureEvent
from app.schemas.event import EventCreate

logger = logging.getLogger(__name__)


class EventRepository:
    def __init__(self, db: Session):
        self._db = db

    def create(self, payload: EventCreate) -> FeatureEvent:
        event = FeatureEvent(
            timestamp=payload.timestamp or datetime.now(timezone.utc),
            user_id=payload.user_id,
            feature=payload.feature,
            metadata_json=json.dumps(payload.metadata) if payload.metadata else None,
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event

    def bulk_create(self, payloads: List[EventCreate]) -> int:
        rows = [
            FeatureEvent(
                timestamp=p.timestamp or datetime.now(timezone.utc),
                user_id=p.user_id,
                feature=p.feature,
                metadata_json=json.dumps(p.metadata) if p.metadata else None,
            )
            for p in payloads
        ]
        self._db.bulk_save_objects(rows)
        self._db.commit()
        return len(rows)

    def get_by_id(self, event_id: int) -> Optional[FeatureEvent]:
        return self._db.get(FeatureEvent, event_id)

    def list_events(self, feature=None, start=None, end=None, limit=100, offset=0):
        q = self._db.query(FeatureEvent)
        if feature:
            q = q.filter(FeatureEvent.feature == feature)
        if start:
            q = q.filter(FeatureEvent.timestamp >= start)
        if end:
            q = q.filter(FeatureEvent.timestamp <= end)
        return q.order_by(FeatureEvent.timestamp.desc()).offset(offset).limit(limit).all()

    def top_features(self, start=None, end=None, limit=10):
        q = self._db.query(
            FeatureEvent.feature,
            func.count(FeatureEvent.id).label("event_count"),
            func.count(func.distinct(FeatureEvent.user_id)).label("unique_users"),
        )
        if start:
            q = q.filter(FeatureEvent.timestamp >= start)
        if end:
            q = q.filter(FeatureEvent.timestamp <= end)
        q = q.group_by(FeatureEvent.feature).order_by(func.count(FeatureEvent.id).desc()).limit(limit)
        return [{"feature": r.feature, "event_count": r.event_count, "unique_users": r.unique_users} for r in q.all()]

    def unique_users(self, feature, start=None, end=None):
        q = self._db.query(func.count(func.distinct(FeatureEvent.user_id))).filter(
            FeatureEvent.feature == feature
        )
        if start:
            q = q.filter(FeatureEvent.timestamp >= start)
        if end:
            q = q.filter(FeatureEvent.timestamp <= end)
        return q.scalar() or 0

    def metadata_breakdown(self, feature, dimension_key, start=None, end=None):
        json_val = func.json_extract(FeatureEvent.metadata_json, f"$.{dimension_key}")
        q = self._db.query(
            json_val.label("dim_value"),
            func.count(FeatureEvent.id).label("event_count"),
            func.count(func.distinct(FeatureEvent.user_id)).label("unique_users"),
        ).filter(
            FeatureEvent.feature == feature,
            FeatureEvent.metadata_json.isnot(None),
            json_val.isnot(None),
        )
        if start:
            q = q.filter(FeatureEvent.timestamp >= start)
        if end:
            q = q.filter(FeatureEvent.timestamp <= end)
        q = q.group_by(json_val).order_by(func.count(FeatureEvent.id).desc())
        return [
            {
                "dimension_key": dimension_key,
                "dimension_value": str(r.dim_value),
                "event_count": r.event_count,
                "unique_users": r.unique_users,
            }
            for r in q.all()
        ]