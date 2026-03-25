import json
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.event import (
    BatchEventCreate,
    EventCreate,
    EventResponse,
    IngestResponse,
)
from app.services.event_repository import EventRepository

logger = logging.getLogger(__name__)
router = APIRouter()


def _to_response(event) -> EventResponse:
    meta = None
    if event.metadata_json:
        try:
            meta = json.loads(event.metadata_json)
        except (ValueError, TypeError):
            meta = None
    return EventResponse(
        id=event.id,
        timestamp=event.timestamp,
        user_id=event.user_id,
        feature=event.feature,
        metadata=meta,
    )


@router.post("", response_model=EventResponse, status_code=201)
def ingest_event(payload: EventCreate, db: Session = Depends(get_db)):
    repo = EventRepository(db)
    event = repo.create(payload)
    logger.info("ingested event id=%s feature=%s", event.id, event.feature)
    return _to_response(event)


@router.post("/batch", response_model=IngestResponse, status_code=201)
def ingest_batch(payload: BatchEventCreate, db: Session = Depends(get_db)):
    repo = EventRepository(db)
    count = repo.bulk_create(payload.events)
    logger.info("batch ingested %s events", count)
    return IngestResponse(accepted=count, message=f"Successfully ingested {count} event(s).")


@router.get("", response_model=List[EventResponse])
def list_events(
    feature: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    repo = EventRepository(db)
    events = repo.list_events(feature=feature, limit=limit, offset=offset)
    return [_to_response(e) for e in events]
