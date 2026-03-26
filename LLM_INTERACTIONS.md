# LLM Interactions Log

## Tool Used
Claude (claude-sonnet-4.6) via claude.ai

## Overview
This document logs the actual prompts I used and what got built at each step.
I used Claude as a coding collaborator — I drove the requirements and decisions,
Claude handled the boilerplate and implementation. Rough split: ~65% Claude generated,
~35% me directed, changed, or fixed based on testing.

---

## Phase 1 — Project Setup & Architecture

**Prompt 1:**
> "I have a T-Mobile engineering take-home. Build a FastAPI service that ingests
> feature usage events and lets you query analytics on top of them. Events have
> timestamp, user_id, feature name, and a flexible metadata JSON field.
> Use SQLite for storage, Docker to run it, pytest for tests.
> What's the right folder structure for this?"

**What got built:** Project skeleton — `app/`, `routers/`, `services/`, `models/`,
`schemas/`, `tests/`, `scripts/`, `static/` folders with empty init files.

**My change:** Claude suggested a separate `services/analytics.py` file.
I simplified it — kept all DB logic in one `event_repository.py` class.
Cleaner for this scope.

---

**Prompt 2:**
> "Set up the database layer. SQLite with SQLAlchemy. I need a FeatureEvent model
> with id, timestamp, user_id, feature, and metadata stored as a JSON string.
> Add a composite index on feature + timestamp since all our analytics queries
> filter by feature first then time range."

**What got built:** `app/db/database.py` with engine setup, `app/models/event.py`
with the ORM model and composite index.

**My change:** Claude named the column `metadata`. I renamed it to `metadata_json`
so it's obvious in the code that it's a string, not a native object. Avoids
confusion when reading queries later.

---

**Prompt 3:**
> "Build the repository class. I want all database queries in one place —
> EventRepository with methods for: create single event, bulk create,
> top features with date range and limit, unique users per feature,
> and metadata breakdown by dimension key using json_extract."

**What got built:** `app/services/event_repository.py` with all query methods.

**What I caught:** Claude's initial metadata_breakdown() had no start/end date
parameters. I caught this later when testing the dashboard — the plan breakdown
chart wasn't changing with date filters. I directed Claude to add date filtering
to both the repository method and the router endpoint.

---

## Phase 2 — API Endpoints

**Prompt 4:**
> "Build the events router. POST /events should accept either a single event
> object OR a list of events (batch). Validate with Pydantic — user_id and
> feature are required, timestamp defaults to now if missing, metadata is
> optional. Return 201 with inserted count. Reject empty batches and
> batches over 500 events."

**What got built:** `app/routers/events.py` with single and batch ingestion,
Pydantic validation, 422 responses for bad payloads.

**My addition:** I specifically asked for whitespace-only user_id to be rejected —
`user_id: "   "` should fail validation. Claude hadn't included that edge case.

---

**Prompt 5:**
> "Build the analytics router with three endpoints:
> 1. GET /analytics/top-features — start, end, limit params. Return features
>    ranked by event_count with unique_users per feature.
> 2. GET /analytics/unique-users — feature, start, end. Return distinct user count.
> 3. GET /analytics/metadata-breakdown — feature, dimension, start, end.
>    Group events by a metadata key like plan or device."

**What got built:** `app/routers/analytics.py` with all three endpoints.

**My change:** Claude used `Optional[datetime]` for date params. I changed to
`Optional[str]` with a manual `_parse_dt()` helper — gives much better error
messages when someone sends a bad date format like `2026/03/26` instead of ISO 8601.

---

**Prompt 6:**
> "Build the health endpoint. GET /health should return status ok, current
> timestamp, and version. Also set up the main FastAPI app — mount the static
> folder at root so localhost:8000 serves the dashboard, register all routers
> with /analytics prefix, add CORS middleware."

**What got built:** `app/routers/health.py`, `app/main.py` with full app setup.

---

## Phase 3 — Docker & Infrastructure

**Prompt 7:**
> "Write the Dockerfile. Python 3.12 slim base, non-root user for security,
> install requirements, copy app code, expose port 8000, run with uvicorn."

**What got built:** `Dockerfile` with multi-step setup and appuser for security.

---

**Prompt 8:**
> "Write docker-compose.yml. Single api service, build from Dockerfile,
> port 8000, set DATABASE_URL env var pointing to /app/data/analytics.db,
> mount ./data as a volume so the SQLite file persists outside the container."

**What got built:** `docker-compose.yml` with volume mount for persistence.

**Why this mattered:** Without the volume mount, every `docker-compose restart`
wiped all the seeded data. The volume means data survives restarts permanently.

---

## Phase 4 — Seed Script

**Prompt 9:**
> "Write a seed script at scripts/seed.py. Generate realistic T-Mobile events:
> 10 features with weighted distribution (sms_text_message most popular,
> magenta_edge_upgrade least popular), 500 users, metadata with plan
> (magenta/magenta_max/essentials/prepaid/business), device
> (mobile/tablet/watch/hotspot_device/syncup_iot), and region
> (west/central/east/southeast/northeast). Spread events randomly across
> the past 5 years. Add --count and --reset CLI flags."

**What got built:** `scripts/seed.py` with weighted feature distribution and CLI flags.

**My change:** Claude used `random.uniform(0, 1825)` for timestamp spread.
I changed to `random.randint(0, 1825)` — uniform was clustering data unevenly
which made date filter comparisons look the same. randint gives a more even
spread across years so Today vs 30 Days vs All Time show clearly different counts.

---

## Phase 5 — Tests

**Prompt 10:**
> "Write pytest tests for the full API. Use FastAPI's dependency_override to
> inject an in-memory SQLite test database. Add an autouse fixture that
> drops and recreates all tables before each test so there's no state leakage.
> Test: health check, single event ingest, batch ingest, all validation failures
> (missing user_id, missing feature, whitespace user_id, bad timestamp, empty batch,
> oversized batch), top-features with time window, unique-users returning 0 for
> unknown feature, metadata-breakdown returning empty list when no data."

**What got built:** `tests/test_api.py` with 20 tests.

**My additions I specifically asked for:**
- `test_unique_users_zero_for_unknown` — unknown feature should return 0, not 404
- `test_metadata_breakdown_empty` — no matching data should return empty list, not error
- `test_top_features_invalid_window` — start after end should return 422

**Result:** 20/20 passing on first full run after fixing one SQLAlchemy query
ordering issue (filters must come before limit/offset).

---

## Phase 6 — Dashboard

**Prompt 11:**
> "Build an HTML dashboard served at localhost:8000. T-Mobile magenta theme
> (#E20074), dark background (#0a0a0a). Show: top features bar chart using
> Chart.js, device breakdown donut chart, plan breakdown horizontal bar chart,
> feature ranking list with progress bars. Fetch data from the same API endpoints."

**What got built:** `static/index.html` with Chart.js visualizations.

---

**Prompt 12:**
> "The dashboard needs date filtering. Add a filter bar with From and To date
> inputs. When the user changes dates and clicks Apply Filter, all charts should
> re-fetch from the API with the new start and end params. Also add preset buttons:
> Today, 7 Days, 30 Days, All Time. Show an active range label so it's clear
> what window is being displayed."

**What got built:** Date filter bar with inputs, preset buttons, active range label,
all fetch calls updated to pass start/end parameters.

**What I caught:** After adding date filters, the Plan Breakdown and Device Breakdown
charts still showed all-time data. Claude had updated top-features and unique-users
but missed metadata-breakdown. I diagnosed it by testing each endpoint separately
in Swagger, found the metadata-breakdown endpoint had no date params in the router
or repository. Directed Claude to fix both layers.

---

## Phase 7 — Documentation

**Prompt 13:**
> "Write a README.md that explains the project like a YouTube tutorial —
> someone should clone the repo and have it running in 5 minutes.
> Include: summary table, what it does, Docker quick start, local quick start,
> seed instructions with all flags, all 20 test names and descriptions,
> full API reference with curl examples and real response shapes,
> live dashboard section, project structure, architecture explanation,
> production readiness table with P0/P1/P2 priorities, trade-offs section,
> future roadmap, and scale assumptions with the 120M subscriber math."

**What got built:** Full README.md.

**My corrections:**
- Updated GitHub repo URL to actual repo
- Fixed API response shapes to match real output (window_start, top_features, dimension_key)
- Added dashboard section after API reference
- Added footer line

---

## Summary Table

| Prompt | What Got Built | My Change |
|--------|---------------|-----------|
| 1 — Project structure | Folder skeleton | Simplified service layer |
| 2 — Database layer | ORM model + DB setup | Renamed metadata → metadata_json |
| 3 — Repository | All query methods | Caught missing date params later |
| 4 — Events router | Single + batch ingestion | Added whitespace user_id validation |
| 5 — Analytics router | 3 analytics endpoints | Changed datetime to string params |
| 6 — Health + main app | App entry point + CORS | — |
| 7 — Dockerfile | Container setup | — |
| 8 — docker-compose | Service + volume mount | Understood why volume matters |
| 9 — Seed script | 10K realistic events | Changed uniform to randint |
| 10 — Tests | 20 pytest tests | Added 3 specific edge case tests |
| 11 — Dashboard base | Charts + T-Mobile theme | — |
| 12 — Date filters | Filter bar + presets | Caught metadata-breakdown bug |
| 13 — README | Full documentation | Fixed URLs, responses, added dashboard section |

---

**Total prompts:** 13 main prompts + multiple follow-up debugging prompts

**Lines generated by Claude:** ~65%

**Key decisions made by me:**
- Repository pattern (directly answered interviewer's DB swappability question)
- Composite index on (feature, timestamp) instead of single timestamp index
- File-backed SQLite via Docker volume instead of in-memory
- randint vs uniform for even seed data distribution
- All trade-off decisions documented in README
