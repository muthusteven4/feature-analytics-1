from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EventCreate(BaseModel):
    timestamp: Optional[datetime] = Field(default=None)
    user_id: str = Field(..., min_length=1, max_length=255)
    feature: str = Field(..., min_length=1, max_length=255)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalise_timestamp(cls, v):
        if v is None:
            return datetime.now(timezone.utc)
        if isinstance(v, datetime):
            return v.astimezone(timezone.utc) if v.tzinfo else v.replace(tzinfo=timezone.utc)
        return v

    @field_validator("user_id", "feature")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Value must not be empty or whitespace only.")
        return stripped


class BatchEventCreate(BaseModel):
    events: List[EventCreate] = Field(..., min_length=1, max_length=1000)


class EventResponse(BaseModel):
    id: int
    timestamp: datetime
    user_id: str
    feature: str
    metadata: Optional[Dict[str, Any]] = None

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    accepted: int
    message: str


class FeatureCount(BaseModel):
    feature: str
    event_count: int
    unique_users: int


class TopFeaturesResponse(BaseModel):
    window_start: datetime
    window_end: datetime
    top_features: List[FeatureCount]


class UniqueUsersResponse(BaseModel):
    feature: str
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    unique_users: int


class MetadataBreakdownItem(BaseModel):
    dimension_key: str
    dimension_value: str
    event_count: int
    unique_users: int


class MetadataBreakdownResponse(BaseModel):
    feature: str
    dimension_key: str
    breakdown: List[MetadataBreakdownItem]
