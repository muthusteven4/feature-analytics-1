# Feature Usage Analytics API

A REST API for ingesting and querying feature usage telemetry built for T-Mobile's take-home assignment.

## How to Run

### With Docker (recommended)
```bash
docker-compose up --build
```

### Without Docker
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive API docs.

## How to Seed Data
```bash
# default 500 events
python scripts/seed.py

# custom count
python scripts/seed.py --count 2000

# wipe and reseed
python scripts/seed.py --reset
```

## How to Run Tests
```bash
pytest tests/ -v
```

## API Usage

### Ingest Single Event
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "feature": "netflix_on_us",
    "metadata": {"plan": "magenta_max", "device": "mobile"}
  }'
```

### Ingest Batch
```bash
curl -X POST http://localhost:8000/events/batch \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {"user_id": "user-001", "feature": "voice_call"},
      {"user_id": "user-002", "feature": "netflix_on_us"}
    ]
  }'
```

### Top Features
```bash
curl "http://localhost:8000/analytics/top-features?start=2025-01-01T09:00:00Z&end=2025-01-01T10:00:00Z&limit=5"
```

### Unique Users
```bash
curl "http://localhost:8000/analytics/unique-users?feature=netflix_on_us"
```

### Metadata Breakdown
```bash
curl "http://localhost:8000/analytics/metadata-breakdown?feature=netflix_on_us&dimension=device"
```

### Health Check
```bash
curl http://localhost:8000/health
```

## Production Readiness Notes

### What is implemented
- Input validation with Pydantic v2
- Batch ingestion in single atomic transaction
- UTC timestamp normalisation
- Database indexes for fast queries
- Repository pattern for database swappability
- Request logging middleware
- Health check endpoint
- Non-root Docker user
- 20 automated tests

### What is missing for true production
- Kafka/Kinesis for high throughput ingestion (120M subscribers)
- Postgres with JSONB indexes instead of SQLite
- Redis caching for analytics queries
- Pre-aggregated hourly summary tables
- Authentication and rate limiting
- OpenTelemetry distributed tracing
- Horizontal scaling with Kubernetes

## Design Decisions and Trade-offs

### Repository Pattern
All database queries live in `event_repository.py`. Swapping SQLite to Postgres only requires changing the `DATABASE_URL` environment variable.

### SQLite over Postgres
Chose SQLite for simplicity and zero external dependencies. For production at T-Mobile scale (120M subscribers) Postgres with connection pooling is the right choice.

### On-demand analytics over pre-aggregation
Flexible for arbitrary time windows. At T-Mobile scale, hourly pre-aggregated summary tables would be needed for fast dashboard queries.

### Synchronous over async
Simpler code and easier to test. At scale, multiple uvicorn workers handle concurrency.

## Potential v2 Expansions
- Real-time streaming with Kafka
- Pre-aggregated hourly stats table
- Postgres JSONB with GIN indexes for metadata queries
- Multi-tenancy support
