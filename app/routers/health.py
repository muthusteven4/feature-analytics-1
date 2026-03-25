from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str


@router.get("/health")
def health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
    )
