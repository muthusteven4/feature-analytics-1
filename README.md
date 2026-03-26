# Feature Usage Analytics API

Built for T-Mobile's take-home assignment. This service tracks feature usage events across T-Mobile's product lineup and lets analysts answer questions like "what features did our subscribers use most between 9am and 10am?"

## How to Run
```bash
docker-compose up --build
```

Then open http://localhost:8000 for the dashboard or http://localhost:8000/docs for the API.

## How to Seed Data
```bash
# from inside the container
docker exec feature-analytics-api python scripts/seed.py --count 500

# or wipe and reseed
docker exec feature-analytics-api python scripts/seed.py --reset --count 500
```

## How to Run Tests
```bash
docker exec feature-analytics-api python -m pytest tests/ -v
```

All 20 tests should pass.

## API Endpoints

### Ingest a single event
```
POST /events
```
```json
{
  "user_id": "user-123",
  "feature": "netflix_on_us",
  "metadata": {"plan": "magenta_max", "device": "mobile"}
}
```

### Ingest a batch (up to 1000 events)
```
POST /events/batch
```

### Top features in a time window
```
GET /analytics/top-features?start=2025-01-01T09:00:00Z&end=2025-01-01T10:00:00Z&limit=5
```

### Unique users for a feature
```
GET /analytics/unique-users?feature=netflix_on_us
```

### Metadata breakdown
```
GET /analytics/metadata-breakdown?feature=netflix_on_us&dimension=device
```

### Health check
```
GET /health
```

## What I Built

- FastAPI REST API with event ingestion and analytics endpoints
- SQLite database with proper indexes on feature, user_id, and timestamp
- Repository pattern so swapping to Postgres is just a config change
- Batch ingestion in a single atomic transaction
- Input validation with Pydantic — bad data gets rejected before hitting the DB
- T-Mobile branded analytics dashboard at localhost:8000
- 20 pytest tests covering all endpoints and edge cases
- Docker + docker-compose setup

## Production Readiness

### What's implemented
- Input validation and error handling
- Request logging with timing
- Composite database indexes for fast time-range queries
- Health check endpoint for load balancers
- Atomic batch writes
- Non-root Docker user
- 20 automated tests

### What I'd add with more time
- Kafka or Kinesis in front of the ingestion endpoint — at 120M subscribers you can't write directly to SQLite or even Postgres without buffering
- Postgres with JSONB indexes instead of SQLite — json_extract() on TEXT doesn't scale
- Pre-aggregated hourly summary tables — COUNT queries over billions of rows need materialized views
- Auth — right now the API is wide open
- Rate limiting
- OpenTelemetry tracing

## Design Decisions

**Repository pattern** — all database queries live in event_repository.py. The routers never touch SQLAlchemy directly. If T-Mobile wants to move to CosmosDB or Postgres, only that one file changes.

**SQLite for this assignment** — zero external dependencies, works identically in Docker and in the test suite (in-memory). The DATABASE_URL env var makes swapping to Postgres a one-line change.

**On-demand analytics over pre-aggregation** — flexible for any time window. Works fine at this scale. At T-Mobile scale with billions of rows, I'd add an hourly rollup job.

**Synchronous FastAPI** — simpler code, easier to reason about. At scale, run multiple uvicorn workers instead of going async.

## Scale Assumptions

T-Mobile has ~120M active subscribers with ~1.2 devices each = ~144M devices. If each device emits one event every 5 minutes that's roughly 480K events per minute. The current SQLite setup handles development and demos fine. Production would need Kafka for ingestion buffering and Postgres with partitioned tables for storage.