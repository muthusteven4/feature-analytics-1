import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


NOW = datetime.now(timezone.utc)
TS = NOW.isoformat()


def post_event(client, **kwargs):
    payload = {
        "timestamp": TS,
        "user_id": "user-001",
        "feature": "netflix_on_us",
        "metadata": {"plan": "pro", "device": "mobile"},
        **kwargs,
    }
    return client.post("/events", json=payload)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_single_event(client):
    r = post_event(client)
    assert r.status_code == 201
    data = r.json()
    assert data["feature"] == "netflix_on_us"
    assert data["user_id"] == "user-001"


def test_ingest_event_without_timestamp(client):
    r = client.post("/events", json={"user_id": "user-002", "feature": "sms"})
    assert r.status_code == 201
    assert r.json()["timestamp"] is not None


def test_ingest_event_without_metadata(client):
    r = client.post("/events", json={"user_id": "user-003", "feature": "voice_call"})
    assert r.status_code == 201
    assert r.json()["metadata"] is None


def test_ingest_missing_user_id_returns_422(client):
    r = client.post("/events", json={"feature": "sms"})
    assert r.status_code == 422


def test_ingest_missing_feature_returns_422(client):
    r = client.post("/events", json={"user_id": "user-001"})
    assert r.status_code == 422


def test_ingest_whitespace_only_user_id_returns_422(client):
    r = client.post("/events", json={"user_id": "   ", "feature": "voice_call"})
    assert r.status_code == 422


def test_ingest_invalid_timestamp_returns_422(client):
    r = client.post("/events", json={"user_id": "u1", "feature": "f1", "timestamp": "not-a-date"})
    assert r.status_code == 422


def test_batch_ingest(client):
    events = [{"user_id": f"user-{i:03}", "feature": "netflix_on_us"} for i in range(10)]
    r = client.post("/events/batch", json={"events": events})
    assert r.status_code == 201
    assert r.json()["accepted"] == 10


def test_batch_empty_list_returns_422(client):
    r = client.post("/events/batch", json={"events": []})
    assert r.status_code == 422


def test_batch_over_limit_returns_422(client):
    events = [{"user_id": "u", "feature": "f"}] * 1001
    r = client.post("/events/batch", json={"events": events})
    assert r.status_code == 422


def test_list_events(client):
    for i in range(5):
        post_event(client, user_id=f"user-{i:03}")
    r = client.get("/events?limit=10")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_list_events_filter_by_feature(client):
    post_event(client, feature="netflix_on_us")
    post_event(client, feature="voice_call")
    r = client.get("/events?feature=voice_call")
    assert r.status_code == 200
    assert r.json()[0]["feature"] == "voice_call"


def test_top_features(client):
    for uid in ["u1", "u2", "u3"]:
        post_event(client, feature="netflix_on_us", user_id=uid)
    post_event(client, feature="voice_call", user_id="u1")
    r = client.get("/analytics/top-features?limit=5")
    assert r.status_code == 200
    assert r.json()["top_features"][0]["feature"] == "netflix_on_us"


def test_top_features_with_time_window(client):
    past_ts = (NOW - timedelta(hours=2)).isoformat()
    recent_ts = NOW.isoformat()
    client.post("/events", json={"user_id": "u1", "feature": "old_feature", "timestamp": past_ts})
    client.post("/events", json={"user_id": "u2", "feature": "new_feature", "timestamp": recent_ts})
    window_start = (NOW - timedelta(minutes=30)).isoformat()
    window_end = (NOW + timedelta(minutes=5)).isoformat()
    r = client.get(f"/analytics/top-features?start={window_start}&end={window_end}")
    assert r.status_code == 200
    features = [f["feature"] for f in r.json()["top_features"]]
    assert "new_feature" in features
    assert "old_feature" not in features


def test_top_features_invalid_window(client):
    r = client.get("/analytics/top-features?start=2025-01-01T10:00:00Z&end=2025-01-01T09:00:00Z")
    assert r.status_code == 422


def test_unique_users(client):
    for uid in ["u1", "u1", "u2", "u3"]:
        post_event(client, feature="netflix_on_us", user_id=uid)
    r = client.get("/analytics/unique-users?feature=netflix_on_us")
    assert r.status_code == 200
    assert r.json()["unique_users"] == 3


def test_unique_users_zero_for_unknown(client):
    r = client.get("/analytics/unique-users?feature=unknown")
    assert r.status_code == 200
    assert r.json()["unique_users"] == 0


def test_metadata_breakdown(client):
    for device in ["mobile", "mobile", "tablet"]:
        client.post("/events", json={
            "user_id": "u1",
            "feature": "netflix_on_us",
            "metadata": {"device": device},
        })
    r = client.get("/analytics/metadata-breakdown?feature=netflix_on_us&dimension=device")
    assert r.status_code == 200
    assert r.json()["breakdown"][0]["dimension_value"] == "mobile"


def test_metadata_breakdown_empty(client):
    r = client.get("/analytics/metadata-breakdown?feature=ghost&dimension=plan")
    assert r.status_code == 200
    assert r.json()["breakdown"] == []
