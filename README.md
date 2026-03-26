# 📡 Feature Usage Analytics API

> A production-grade REST API for ingesting and analyzing feature usage events — built for T-Mobile scale (120M+ subscribers).

---

## 📋 Table of Contents

- [What This Does](#-what-this-does)
- [Quick Start (Docker)](#-quick-start-docker)
- [Quick Start (Local)](#-quick-start-local)
- [Seed the Database](#-seed-the-database)
- [Run the Tests](#-run-the-tests)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Architecture & Design](#-architecture--design)
- [Production Readiness Notes](#-production-readiness-notes)
- [Trade-Offs](#-trade-offs)
- [Future Roadmap](#-future-roadmap)

---

## 🧠 What This Does

This service does two things:

1. **Ingests feature usage events** — accepts a single event or a batch, validates them, and stores them
2. **Answers analytics questions** — most popular features, unique user counts, top-N rankings, and metadata breakdowns

**Example use case:** T-Mobile analysts want to know: *"Was Netflix on Us or texting more popular between 9–10 AM last Tuesday?"* This API answers that.

### Example Event

```json
{
  "timestamp": "2025-01-01T12:34:56Z",
  "user_id": "user-123",
  "feature": "netflix_on_us",
  "metadata": { "plan": "pro", "device": "mobile" }
}
```

---

## 🐳 Quick Start (Docker)

> Recommended. No Python setup needed — just Docker.

### 1. Clone the repo

```bash
git clone https://github.com/your-username/feature-usage-api.git
cd feature-usage-api
```

### 2. Build and run

```bash
docker-compose up --build
```

### 3. Confirm it's running

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

### 4. Open the interactive docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs) in your browser — Swagger UI is built in.

---

## 💻 Quick Start (Local)

> If you prefer running without Docker.

### Prerequisites

- Python 3.11+
- pip

### Steps

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) to confirm.

---

## 🌱 Seed the Database

After the server is running, load realistic sample data so you can immediately test the analytics endpoints.

```bash
python seed_data.py
```

**What it loads:**
- 500 events spread across the past 7 days
- 100 unique users (`user-1` through `user-100`)
- 5 T-Mobile features: `netflix_on_us`, `satellite_connect`, `syncup_tracker`, `wifi_calling`, `text_message`
- Metadata with `plan` (pro / basic / enterprise) and `device` (mobile / tablet / watch)

**Verify the seed worked:**

```bash
curl "http://localhost:8000/analytics/top-features?start=2025-01-01T00:00:00Z&end=2026-01-01T00:00:00Z&limit=5"
```

You should see a ranked list of features with usage counts.

---

## 🧪 Run the Tests

```bash
# From the project root
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing
```

### What's tested

| Test | Description |
|------|-------------|
| `test_ingest_single_event` | Valid single event returns 201 |
| `test_ingest_batch_events` | Valid batch of 3 events returns 201 |
| `test_invalid_payload_missing_user_id` | Missing user_id returns 422 |
| `test_invalid_payload_bad_timestamp` | Malformed timestamp returns 422 |
| `test_top_features_analytics` | Returns ranked features for a time range |
| `test_unique_users_count` | Returns correct unique user count |
| `test_metadata_breakdown` | Groups events by metadata key correctly |

---

## 📡 API Reference

### `POST /events` — Ingest Events

Accepts a **single event** or a **batch (list)** of events.

**Single event:**
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2025-01-01T12:34:56Z",
    "user_id": "user-123",
    "feature": "netflix_on_us",
    "metadata": { "plan": "pro", "device": "mobile" }
  }'
```

**Batch of events:**
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp": "2025-01-01T09:00:00Z", "user_id": "user-1", "feature": "netflix_on_us", "metadata": {"plan": "pro"}},
    {"timestamp": "2025-01-01T09:05:00Z", "user_id": "user-2", "feature": "text_message", "metadata": {"plan": "basic"}},
    {"timestamp": "2025-01-01T09:10:00Z", "user_id": "user-1", "feature": "wifi_calling", "metadata": {"plan": "pro"}}
  ]'
```

**Response (201 Created):**
```json
{ "inserted": 3 }
```

**Validation error (422):**
```json
{
  "detail": [
    { "loc": ["body", "user_id"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

---

### `GET /analytics/top-features` — Most Popular Features

Returns features ranked by usage count over a time window.

```bash
curl "http://localhost:8000/analytics/top-features?start=2025-01-01T09:00:00Z&end=2025-01-01T10:00:00Z&limit=5"
```

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | ISO datetime | ✅ | Start of time window |
| `end` | ISO datetime | ✅ | End of time window |
| `limit` | integer | ❌ | Top N results (default: 10) |

**Response:**
```json
{
  "start": "2025-01-01T09:00:00Z",
  "end": "2025-01-01T10:00:00Z",
  "results": [
    { "feature": "netflix_on_us", "count": 4821 },
    { "feature": "text_message",  "count": 3104 },
    { "feature": "wifi_calling",  "count": 1892 }
  ]
}
```

---

### `GET /analytics/unique-users` — Unique User Count

Returns the number of distinct users who triggered a specific feature.

```bash
curl "http://localhost:8000/analytics/unique-users?feature=netflix_on_us&start=2025-01-01T00:00:00Z&end=2025-01-02T00:00:00Z"
```

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `feature` | string | ✅ | Feature name to count |
| `start` | ISO datetime | ✅ | Start of time window |
| `end` | ISO datetime | ✅ | End of time window |

**Response:**
```json
{
  "feature": "netflix_on_us",
  "unique_users": 31204,
  "start": "2025-01-01T00:00:00Z",
  "end": "2025-01-02T00:00:00Z"
}
```

---

### `GET /analytics/metadata-breakdown` — Breakdown by Metadata Dimension

Groups event counts by a specific metadata key for a given feature.

```bash
curl "http://localhost:8000/analytics/metadata-breakdown?feature=netflix_on_us&meta_key=plan&start=2025-01-01T00:00:00Z&end=2025-01-02T00:00:00Z"
```

**Query parameters:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `feature` | string | ✅ | Feature to analyze |
| `meta_key` | string | ✅ | Metadata key to group by (e.g. `plan`, `device`) |
| `start` | ISO datetime | ✅ | Start of time window |
| `end` | ISO datetime | ✅ | End of time window |

**Response:**
```json
{
  "feature": "netflix_on_us",
  "dimension": "plan",
  "breakdown": [
    { "value": "pro",        "count": 3100 },
    { "value": "enterprise", "count": 1540 },
    { "value": "basic",      "count": 920  }
  ]
}
```

---

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
# → {"status": "ok"}
```

---

## 📁 Project Structure

```
feature-usage-api/
│
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── models.py                # Pydantic request/response schemas
│   ├── database.py              # DB connection and initialization
│   ├── routers/
│   │   ├── events.py            # POST /events
│   │   └── analytics.py        # GET /analytics/*
│   ├── repositories/
│   │   ├── base.py              # EventRepository ABC (interface)
│   │   └── sqlite.py            # SQLite implementation
│   └── services/
│       └── analytics.py         # Business logic for analytics queries
│
├── tests/
│   ├── conftest.py              # Shared fixtures (test DB, test client)
│   ├── test_events.py           # Event ingestion tests
│   └── test_analytics.py       # Analytics endpoint tests
│
├── seed_data.py                 # Populates DB with 500 sample events
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md                    # ← You are here
└── LLM_INTERACTIONS.md         # AI usage log
```

---

## 🏗 Architecture & Design

### Repository Pattern

All database access goes through a `EventRepository` abstract base class:

```python
class EventRepository(ABC):
    def insert(self, event: Event) -> None: ...
    def insert_batch(self, events: list[Event]) -> None: ...
    def query_by_time_range(self, start, end) -> list[Event]: ...
```

The FastAPI routes call only this interface — never raw SQL. The concrete implementation (`SQLiteEventRepository`) is injected via `Depends()`. Swapping to Postgres means writing one new class and changing one line in the DI config.

### Metadata Storage

The `metadata` field is stored as a JSON string (TEXT column). Queries use SQLite's built-in `json_extract()`:

```sql
SELECT json_extract(metadata, '$.plan') as value, COUNT(*) as count
FROM events
WHERE feature = 'netflix_on_us'
  AND timestamp BETWEEN ? AND ?
GROUP BY value
ORDER BY count DESC
```

In Postgres, this would use `JSONB` with a GIN index for significantly faster performance at scale.

### Layers

```
HTTP Request
    ↓
FastAPI Router         (input validation via Pydantic)
    ↓
Service Layer          (business logic, aggregations)
    ↓
Repository Layer       (data access abstraction)
    ↓
SQLite / Postgres      (storage)
```

---

## 🚀 Production Readiness Notes

### What IS production-ready in this implementation

- ✅ Pydantic validation rejects bad payloads at the boundary
- ✅ Repository pattern makes DB migration a 1-file change
- ✅ Batch ingestion reduces round trips for high-throughput clients
- ✅ Parameterized queries (no SQL injection risk)
- ✅ Docker containerization for consistent environments
- ✅ Health check endpoint for load balancer readiness probes
- ✅ pytest suite covering happy path + validation failures

### What is NOT production-ready (and why it's deferred)

| Gap | What's Needed | Priority |
|-----|--------------|----------|
| No authentication | API key / JWT middleware | P0 before any external traffic |
| SQLite in-memory | Postgres with date partitioning | P0 for persistence and scale |
| No rate limiting | Token bucket per client ID | P1 |
| No distributed tracing | OpenTelemetry → Jaeger/Tempo | P1 |
| On-demand query aggregation | Pre-aggregated hourly/daily summary tables | P1 for T-Mobile scale |
| No metrics endpoint | Prometheus `/metrics` + Grafana dashboard | P1 |
| Single instance | Kubernetes HPA with horizontal autoscaling | P2 |
| Synchronous ingestion | Kafka/Kinesis async queue at 250K events/sec | P2 |

---

## ⚖️ Trade-Offs

### SQLite vs PostgreSQL

**Chose SQLite** for simplicity and zero-config setup. The repository pattern means switching to Postgres is a new class + one config change.

**Postgres is required for production.** At T-Mobile scale (~120M subscribers, ~1.2 devices each, ~50 events/device/day = ~7.2B events/day), SQLite cannot handle the write throughput or the concurrent analytics queries.

### On-Demand Aggregation vs Pre-Aggregation

**Chose on-demand** (SQL `GROUP BY` at query time) for v1. Fast to build, flexible for any time window.

**Pre-aggregation needed for v2.** A background job materializing hourly/daily summaries into a separate table would reduce analytics query time from seconds to milliseconds at scale. A Redis cache layer with short TTL would serve repeated identical queries instantly.

### Synchronous HTTP vs Async Queue

**Chose synchronous** `POST /events` for simplicity. Works fine at low-to-medium traffic.

**At T-Mobile peak (~250K events/sec estimated),** the ingestion endpoint would need to be backed by a Kafka topic. The API would enqueue and acknowledge immediately; a separate consumer would write to the database asynchronously. This decouples ingestion latency from write latency.

---

## 🗺 Future Roadmap

**v2 — Scale & Performance**
- [ ] Replace SQLite with Postgres (JSONB + GIN index on metadata)
- [ ] Pre-aggregated hourly/daily summary tables via scheduled job
- [ ] Redis caching layer for repeated analytics queries

**v3 — Real-Time**
- [ ] Kafka-backed async ingestion pipeline
- [ ] Apache Flink stream processor for real-time feature ranking
- [ ] Live dashboard via Server-Sent Events or WebSocket

**v4 — Operational Excellence**
- [ ] OpenTelemetry distributed tracing
- [ ] Prometheus metrics + Grafana dashboards
- [ ] Kubernetes deployment with HPA autoscaling
- [ ] CI/CD pipeline (GitHub Actions → ECR → EKS)

---

## 🧰 Scale Assumptions (Documented)

| Assumption | Value |
|-----------|-------|
| Active subscribers | 120,000,000 |
| Avg devices per subscriber | 1.2 |
| Total devices | ~144,000,000 |
| Events per device per day | ~50 |
| Total events per day | ~7,200,000,000 |
| Peak events per second | ~250,000 |
| SQLite viable? | No — prototype only |
| Recommended production DB | Postgres (partitioned) or Cassandra |

---

*Built with FastAPI · SQLite · Docker · pytest 
