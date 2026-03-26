# LLM Interactions Log

## Tool Used
Claude (claude-sonnet-4-6) via claude.ai

## How I Used It

I described the interview requirements and worked through the project
conversationally with Claude. I didn't just ask for code — I asked why,
pushed back when things broke, and asked Claude to explain things I
didn't understand.

---

## Session 1 — Architecture Planning

**Me:**
> I have a T-Mobile take-home. They want a FastAPI service that ingests
> feature usage events and answers analytics questions. SQLite for storage,
> Docker, pytest. What's the right way to structure this?

Claude suggested separating routers by concern, using the repository
pattern for database access, and Pydantic v2 for validation. I asked
why the repository pattern mattered and Claude explained that if T-Mobile
ever wants to swap SQLite for Postgres or CosmosDB, only one file changes.
That clicked for me — the interviewer had literally asked about database
swappability.

---

## Session 2 — Building File by File

I asked Claude to give me each file one at a time so I could read and
understand before moving on. Some files I had questions about:

**On the metadata column:**
> Why are we storing metadata as TEXT and not separate columns?

Claude explained that the metadata can be any valid JSON — plan, device,
region, anything. Fixed columns can't handle that. TEXT with json_extract()
works for SQLite. On Postgres you'd use JSONB with a GIN index for real
performance.

**On the indexes:**
> What are these Index lines doing in the model?

Without indexes, every analytics query would scan the entire table.
The composite index on (feature, timestamp) means time-range queries
for a specific feature are fast. At T-Mobile scale with billions of
rows that's the difference between 2ms and 20 seconds.

---

## Session 3 — Things That Broke

This is where it got real.

**Problem 1 — Wrong folder structure on GitHub**

I was creating files while inside subfolders on GitHub instead of
navigating back to root first. Ended up with app/app/db/database.py
instead of app/db/database.py. Had to delete the wrong files and
recreate from root. Claude told me to always click the repo name
breadcrumb before adding any file.

**Problem 2 — Docker couldn't open SQLite**

Got this error repeatedly:
```
sqlalchemy.exc.OperationalError: unable to open database file
```

We tried a few things:
- Changed the path to sqlite:////tmp/analytics.db
- Removed the volume mount from docker-compose
- Simplified docker-compose to remove the healthcheck

The fix was removing the volume mount entirely and letting the
database live inside the container. The volume mount was trying
to bind a file that didn't exist on the host yet.

**Problem 3 — YAML errors in docker-compose**

When editing docker-compose.yml in Windows Notepad it kept inserting
tabs instead of spaces. YAML breaks with tabs. Switched to VS Code
which handles indentation correctly.

**Problem 4 — Dashboard showing 404**

After adding the dashboard route, got a 404 at localhost:8000.
The issue was the static mount was registered before the route,
so FastAPI never reached the route handler. Fixed by moving the
@app.get("/") route above the app.mount() call.

---

## Session 4 — Tests

**Me:**
> How do I test the API without hitting a real database?

Claude showed me FastAPI's dependency_override pattern. You replace
get_db with a function that returns an in-memory SQLite session.
Each test gets a completely fresh database via an autouse fixture
that drops and recreates all tables. No state leaks between tests.

When I ran the tests the first time, one failed:
```
sqlalchemy.exc.InvalidRequestError: Query.filter() being called
on a Query which already has LIMIT or OFFSET applied
```

SQLAlchemy requires filters to be applied before limit/offset.
The top_features query had them in the wrong order. Fixed by
restructuring the query to filter first, then group, then limit.

---

## Session 5 — Dashboard

**Me:**
> Can we add a visual dashboard? T-Mobile magenta colors, dark theme,
> shows top features, device breakdown, plan breakdown.

Claude built the HTML/JS dashboard using Chart.js. It reads directly
from the same API endpoints we built. I added it as a static file
served by FastAPI at the root route so when you open localhost:8000
you see the dashboard instead of a blank page.

---

## Summary

┌─────────────────────────────────────────┬─────────────────────────────────────────┐
│ What I asked Claude for                 │ What I did myself                       │
├─────────────────────────────────────────┼─────────────────────────────────────────┤
│ Architecture advice                     │ Decided which suggestions made sense    │
│ File by file code generation            │ Read every file, asked questions        │
│ Debugging help when things broke        │ Tested fixes, understood root cause     │
│ Explanation of patterns                 │ Applied understanding in interview prep │
│ Dashboard HTML                          │ Integrated it into the FastAPI app      │
└─────────────────────────────────────────┴─────────────────────────────────────────┘