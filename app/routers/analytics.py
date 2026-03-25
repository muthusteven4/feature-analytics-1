import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.event import (
    MetadataBreakdownResponse,
    TopFeaturesResponse,
    UniqueUsersResponse,
)
from app.services.event_repository import EventRepository

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_dt(value: Optional[str], param_name: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        normalised = value.strip().replace(" ", "+").replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalised)
        return dt.astimezone(timezone.utc)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid datetime format for '{param_name}'. Use ISO-8601 e.g. 2025-01-01T09:00:00Z",
        )


@router.get("/top-features", response_model=TopFeaturesResponse)
def top_features(
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    start_dt = _parse_dt(start, "start")
    end_dt = _parse_dt(end, "end")

    if start_dt and end_dt and start_dt >= end_dt:
        raise HTTPException(status_code=422, detail="'start' must be before 'end'.")

    repo = EventRepository(db)
    rows = repo.top_features(start=start_dt, end=end_dt, limit=limit)

    return TopFeaturesResponse(
        window_start=start_dt or datetime.min.replace(tzinfo=timezone.utc),
        window_end=end_dt or datetime.now(timezone.utc),
        top_features=rows,
    )


@router.get("/unique-users", response_model=UniqueUsersResponse)
def unique_users(
    feature: str = Query(...),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    start_dt = _parse_dt(start, "start")
    end_dt = _parse_dt(end, "end")

    repo = EventRepository(db)
    count = repo.unique_users(feature=feature, start=start_dt, end=end_dt)

    return UniqueUsersResponse(
        feature=feature,
        window_start=start_dt,
        window_end=end_dt,
        unique_users=count,
    )


@router.get("/metadata-breakdown", response_model=MetadataBreakdownResponse)
def metadata_breakdown(
    feature: str = Query(...),
    dimension: str = Query(...),
    db: Session = Depends(get_db),
):
    repo = EventRepository(db)
    rows = repo.metadata_breakdown(feature=feature, dimension_key=dimension)

    return MetadataBreakdownResponse(
        feature=feature,
        dimension_key=dimension,
        breakdown=rows,
    )
