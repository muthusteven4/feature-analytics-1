# LLM Interactions Log

This document records how I used Claude as an AI coding assistant throughout this assignment.

## How I Used the LLM

I used Claude (claude-sonnet-4-6) to help scaffold and build this project.
The approach was conversational — I described the requirements from the interview
and Claude helped me think through architecture decisions, generate code, and
review trade-offs.

## Interaction 1 — Architecture Planning

**My prompt:**
> We need to build a feature usage analytics API for T-Mobile.
> It needs to ingest events and answer questions like top features
> in a time window, unique users per feature, and metadata breakdowns.
> What architecture would you suggest?

**What Claude suggested:**
- FastAPI for the web framework
- Repository pattern to keep database logic separate
- SQLite for simplicity, swappable to Postgres via environment variable
- Pydantic v2 for input validation
- Separate routers for events and analytics

**What I decided:**
I agreed with the overall structure. The repository pattern made sense
because the interviewer specifically asked about swapping databases.

## Interaction 2 — Database Design

**My prompt:**
> How should I store the metadata field? It can be any valid JSON.

**What Claude suggested:**
- Store as TEXT (JSON string) for SQLite
- On Postgres, use JSONB with GIN index for fast queries
- Use json_extract() for SQLite queries on metadata fields

**What I decided:**
Used TEXT storage with json_extract() for now and documented
the Postgres JSONB upgrade path in the README.

## Interaction 3 — Trade-offs Discussion

**My prompt:**
> Should I pre-aggregate analytics data or compute on demand?

**What Claude suggested:**
Hybrid approach — pre-aggregate common windows, on-demand for ad-hoc.
For this assignment scope, on-demand with proper indexes is fine.

**What I decided:**
Implemented on-demand with composite indexes on (feature, timestamp)
and documented pre-aggregation as a v2 expansion.

## Interaction 4 — Test Coverage

**My prompt:**
> What edge cases should I test for a production analytics API?

**What Claude suggested:**
- Whitespace only user_id validation
- Invalid time window (start after end)
- Batch size limits
- Empty metadata breakdown returns 200 not 404
- Unknown feature returns 0 unique users not error

**What I added based on this:**
All of the above edge cases are covered in tests/test_api.py.

## Summary

| Component | LLM helped | I reviewed and understood |
|-----------|------------|--------------------------|
| Architecture | ✅ | ✅ |
| Database setup | ✅ | ✅ |
| ORM models | ✅ | ✅ |
| Schemas | ✅ | ✅ |
| Repository queries | ✅ | ✅ |
| API endpoints | ✅ | ✅ |
| Tests | ✅ | ✅ |
| Docker setup | ✅ | ✅ |

No code was accepted without reading and understanding what it does.
