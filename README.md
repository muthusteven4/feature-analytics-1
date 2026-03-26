# 📡 Feature Usage Analytics API

> A production-grade REST API for ingesting and analyzing feature usage events — built for T-Mobile scale (120M+ subscribers).

---

## 📋 Table of Contents

- [Summary](#-summary)
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
- [Scale Assumptions](#-scale-assumptions)

---

## 🗂 Summary

This project is a take-home engineering assignment for T-Mobile. The goal was to build a production-grade feature usage analytics API from scratch in 1–3 hours.

| Item | Detail |
|------|--------|
| Framework | FastAPI (Python) |
| Database | SQLite (file-backed, persists via Docker volume) |
| Containerization | Docker + docker-compose |
| Tests | 20 passing pytest tests |
| Dashboard | Live at `localhost:8000` with date filters |
| API Docs | Swagger UI at `localhost:8000/docs` |
| Seed Data | 10,000 events spread across 5 years (2021–2026) |
| AI Tool Used | Claude Code (documented in `LLM_INTERACTIONS.md`) |

**What's production-ready:** Pydantic validation, repository pattern, batch ingestion, parameterized queries, Docker, health check, full test suite, persistent storage, date-filtered analytics.

**What's deferred to v2:** Authentication, rate limiting, Postgres migration, Kafka async queue, pre-aggregation tables, OpenTelemetry tracing, Kubernetes autoscaling.

---

## 🧠 What This Does

This service does two things:

1. **Ingests feature usage events** — accepts a single event or a batch, validates them, and stores them
2. **Answers analytics questions** — most popular features, unique user counts, top-N rankings, and metadata breakdowns by plan or device

**Example use case:** T-Mobile analysts want to know: *"Was Netflix on Us or texting more popular between 9–10 AM last Tuesday?"* This API answers that.

### Example Event

```json
{
  "timestamp": "2026-03-26T12:00:00Z",
  "user_id": "user-123",
  "feature": "netflix_on_us",
  "metadata": { "plan": "magenta_max", "device": "mobile" }
}
```

---

## 📊 Live Dashboard

Visit [http://localhost:8000](http://localhost:8000) after seeding to see the live analytics dashboard.

**Features:**
- Date range filter with From/To date pickers
- Preset buttons — Today, 7 Days, 30 Days, All Time
- Feature Usage bar chart (Top 10)
- Device Breakdown donut chart
- Plan Breakdown horizontal bar chart
- Feature Ranking list with progress bars
- Live dot indicator + Refresh Data button

All charts update instantly when you change the date range — powered by the same API endpoints.

---

## 🐳 Quick Start (Docker)

> Recommended. No Python setup needed — just Docker.

### 1. Clone the repo

```bash
git clone https://github.com/muthusteven4/feature-analytics-1.git
cd feature-analytics-1
```

### 2. Build and run

```bash
docker-compose up --build -d
```

### 3. Confirm it's running

```bash
curl http://localhost:8000/health
# → {"status":"ok","timestamp":"...","version":"1.0.0"}
```

### 4. Seed the database

```bash
docker-compose exec api python scripts/seed.py --count 10000
```

### 5. Open the dashboard

Visit [http://localhost:8000](http://localhost:8000) — live analytics dashboard with date filters.

### 6. Open the API docs

Visit [http://localhost:8000/docs](http://localhost:8000/docs) — Swagger UI for testing all endpoints.

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

---

## 🌱 Seed the Database

```bash
# Seed 10,000 events (recommended)
docker-compose exec api python scripts/seed.py --count 10000

# Reset and reseed fresh
docker-compose exec api python scripts/seed.py --reset --count 10000

# Custom count
docker-compose exec api python scripts/seed.py --reset --count 5000
```

**What it loads:**
- Events spread randomly across the past 5 years (2021–2026)
- 500 unique users (`user-0001` through `user-0500`)
- 10 T-Mobile features: `netflix_on_us`, `sms_text_message`, `voice_call`, `wifi_calling`, `satellite_connect`, `mobile_hotspot`, `syncup_tracker`, `visual_voicemail`, `international_roaming`, `magenta_edge_upgrade`
- Metadata: `plan` (magenta / magenta_max / essentials / prepaid / business), `device` (mobile / tablet / watch / hotspot_device / syncup_iot), `region` (west / central / east / southeast / northeast)

---

## 🧪 Run the Tests

```bash
# Run all 20 tests
docker-compose exec api pytest -v
```

### Test Results (20/20 passing)

| Test | Description |
|------|-------------|
| `test_health` | Health endpoint returns 200 |
| `test_ingest_single_event` | Valid single event returns 201 |
| `test_ingest_event_without_timestamp` | Missing timestamp defaults to now |
| `test_ingest_event_without_metadata` | Optional metadata accepted |
| `test_ingest_missing_user_id_returns_422` | Missing user_id rejected |
| `test_ingest_missing_feature_returns_422` | Missing feature rejected |
| `test_ingest_whitespace_only_user_id_returns_422` | Blank user_id rejected |
| `test_ingest_invalid_timestamp_returns_422` | Bad timestamp rejected |
| `test_batch_ingest` | Valid batch returns 201 |
| `test_batch_empty_list_returns_422` | Empty batch rejected |
| `test_batch_over_limit_returns_422` | Oversized batch rejected |
| `test_list_events` | Events list endpoint works |
| `test_list_events_filter_by_feature` | Feature filter works |
| `test_top_features` | Returns ranked features |
| `test_top_features_with_time_window` | Date range filter works |
| `test_top_features_invalid_window` | Bad date range rejected |
| `test_unique_users` | Returns correct unique count |
| `test_unique_users_zero_for_unknown` | Unknown feature returns 0 |
| `test_metadata_breakdown` | Groups by metadata key correctly |
| `test_metadata_breakdown_empty` | No data returns empty list |

---

## 📡 API Reference

### `POST /events` — Ingest Events

Accepts a **single event** or a **batch (list)** of events.

**Single event:**
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2026-03-26T12:00:00Z",
    "user_id": "user-123",
    "feature": "netflix_on_us",
    "metadata": { "plan": "magenta_max", "device": "mobile" }
  }'
```

**Batch of events:**
```bash
curl -X POST http://localhost:8000/events \
  -H "Content-Type: application/json" \
  -d '[
    {"timestamp": "2026-03-26T09:00:00Z", "user_id": "user-1", "feature": "netflix_on_us", "metadata": {"plan": "magenta_max"}},
    {"timestamp": "2026-03-26T09:05:00Z", "user_id": "user-2", "feature": "sms_text_message", "metadata": {"plan": "essentials"}},
    {"timestamp": "2026-03-26T09:10:00Z", "user_id": "user-3", "feature": "wifi_calling", "metadata": {"plan": "magenta"}}
  ]'
```

**Response (201 Created):**
```json
{ "inserted": 3 }
```

---

### `GET /analytics/top-features` — Most Popular Features

```bash
curl "http://localhost:8000/analytics/top-features?start=2026-03-20T00:00:00Z&end=2026-03-26T23:59:59Z&limit=10"
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `start` | ISO datetime | ❌ | Start of time window |
| `end` | ISO datetime | ❌ | End of time window |
| `limit` | integer | ❌ | Top N results (default: 10, max: 100) |

**Response:**
```json
{
  "window_start": "2026-03-20T00:00:00Z",
  "window_end": "2026-03-26T23:59:59Z",
  "top_features": [
    { "feature": "sms_text_message", "event_count": 2420, "unique_users": 499 },
    { "feature": "netflix_on_us",    "event_count": 2023, "unique_users": 491 },
    { "feature": "voice_call",       "event_count": 1566, "unique_users": 484 }
  ]
}
```

---

### `GET /analytics/unique-users` — Unique User Count

```bash
curl "http://localhost:8000/analytics/unique-users?feature=netflix_on_us&start=2026-03-01T00:00:00Z&end=2026-03-26T23:59:59Z"
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `feature` | string | ✅ | Feature name |
| `start` | ISO datetime | ❌ | Start of time window |
| `end` | ISO datetime | ❌ | End of time window |

**Response:**
```json
{
  "feature": "netflix_on_us",
  "unique_users": 491,
  "window_start": "2026-03-01T00:00:00Z",
  "window_end": "2026-03-26T23:59:59Z"
}
```

---

### `GET /analytics/metadata-breakdown` — Breakdown by Metadata Dimension

```bash
curl "http://localhost:8000/analytics/metadata-breakdown?feature=netflix_on_us&dimension=plan&start=2026-03-01T00:00:00Z&end=2026-03-26T23:59:59Z"
```

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `feature` | string | ✅ | Feature to analyze |
| `dimension` | string | ✅ | Metadata key (`plan`, `device`, `region`) |
| `start` | ISO datetime | ❌ | Start of time window |
| `end` | ISO datetime | ❌ | End of time window |

**Response:**
```json
{
  "feature": "netflix_on_us",
  "dimension_key": "plan",
  "breakdown": [
    { "dimension_value": "prepaid",     "event_count": 420, "unique_users": 210 },
    { "dimension_value": "magenta_max", "event_count": 380, "unique_users": 190 },
    { "dimension_value": "essentials",  "event_count": 310, "unique_users": 160 }
  ]
}
```

---

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
# → {"status":"ok","timestamp":"2026-03-26T12:00:00Z","version":"1.0.0"}
```

---

## 📁 Project Structure

```
feature-analytics-1/
│
├── app/
│   ├── main.py                      # FastAPI app entry point
│   ├── db/
│   │   └── database.py              # DB connection and initialization
│   ├── models/
│   │   └── event.py                 # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── event.py                 # Pydantic request/response schemas
│   ├── routers/
│   │   ├── events.py                # POST /events, GET /events
│   │   ├── analytics.py             # GET /analytics/*
│   │   └── health.py                # GET /health
│   └── services/
│       └── event_repository.py      # All DB queries (repository pattern)
│
├── scripts/
│   └── seed.py                      # Seed script (--count, --reset flags)
│
├── static/
│   └── index.html                   # Live dashboard with date filters
│
├── tests/
│   └── test_api.py                  # 20 pytest tests
│
├── data/                            # SQLite DB persisted via Docker volume
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── LLM_INTERACTIONS.md
```

---

## 🏗 Architecture & Design

### Repository Pattern

All database access goes through `EventRepository` — a single class that owns all queries. FastAPI routes never touch SQL directly. Swapping SQLite for Postgres means implementing one new class and changing one environment variable.

### Metadata Storage & Querying

The `metadata` field accepts any valid JSON object and is stored as a TEXT column. Queries use SQLite's `json_extract()`:

```sql
SELECT json_extract(metadata_json, '$.plan') as value, COUNT(*) as count
FROM feature_events
WHERE feature = 'netflix_on_us'
  AND timestamp BETWEEN ? AND ?
GROUP BY value
ORDER BY count DESC
```

In Postgres this becomes a JSONB column with a GIN index — dramatically faster at scale.

### Request Flow

```
HTTP Request
    ↓
FastAPI Router     → Pydantic validation (rejects bad payloads immediately)
    ↓
EventRepository    → SQL queries with optional date range filters
    ↓
SQLite             → Persistent file-backed storage via Docker volume
    ↓
JSON Response
```

---

## 🚀 Production Readiness Notes

### What IS production-ready

- ✅ Pydantic validation rejects bad payloads at the boundary
- ✅ Repository pattern makes DB migration a 1-class change
- ✅ Batch ingestion reduces round trips for high-throughput clients
- ✅ Parameterized queries — no SQL injection risk
- ✅ Docker + persistent volume — data survives restarts
- ✅ Health check endpoint for load balancer probes
- ✅ 20 passing tests covering happy path + all validation failures
- ✅ Date range filtering on all analytics endpoints
- ✅ Live dashboard connected to the same API

### What is NOT production-ready (deferred)

| Gap | What's Needed | Priority |
|-----|--------------|----------|
| No authentication | API key / JWT middleware | P0 |
| SQLite at scale | Postgres with date partitioning | P0 |
| No rate limiting | Token bucket per client | P1 |
| On-demand aggregation | Pre-aggregated hourly/daily summary tables | P1 |
| No metrics | Prometheus `/metrics` + Grafana | P1 |
| No tracing | OpenTelemetry → Jaeger | P1 |
| Single instance | Kubernetes HPA autoscaling | P2 |
| Sync ingestion | Kafka/Kinesis async queue | P2 |

---

## ⚖️ Trade-Offs

### SQLite vs PostgreSQL
Chose SQLite for zero-config simplicity. The repository pattern means Postgres is a one-class swap. At T-Mobile scale (7.2B events/day), Postgres with date partitioning is required.

### On-Demand vs Pre-Aggregation
Chose on-demand SQL `GROUP BY` for v1 — flexible for any time window. Pre-aggregated hourly/daily summary tables would cut query time from seconds to milliseconds at scale.

### Synchronous vs Async Ingestion
Chose synchronous `POST /events` for simplicity. At ~250K events/sec peak, Kafka-backed async ingestion is required to decouple write latency from API response time.

### File-backed SQLite vs In-Memory
Chose file-backed SQLite via Docker volume so data persists through container restarts. In-memory would be faster but loses all data on restart.

---

## 🗺 Future Roadmap

**v2 — Scale**
- [ ] Postgres with JSONB + GIN index on metadata
- [ ] Pre-aggregated hourly/daily summary tables
- [ ] Redis caching for repeated analytics queries

**v3 — Real-Time**
- [ ] Kafka async ingestion pipeline
- [ ] Apache Flink stream processor
- [ ] WebSocket live dashboard updates

**v4 — Operational Excellence**
- [ ] OpenTelemetry distributed tracing
- [ ] Prometheus + Grafana dashboards
- [ ] Kubernetes HPA autoscaling
- [ ] GitHub Actions CI/CD → ECR → EKS

---

## 🧰 Scale Assumptions

| Assumption | Value |
|-----------|-------|
| Active subscribers | 120,000,000 |
| Avg devices per subscriber | 1.2 |
| Total devices | ~144,000,000 |
| Events per device per day | ~50 |
| Total events per day | ~7,200,000,000 |
| Peak events per second | ~250,000 |
| SQLite viable at this scale? | No — prototype only |
| Recommended production DB | Postgres (partitioned by date) |

---