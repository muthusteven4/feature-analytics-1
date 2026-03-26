# LLM Interactions Log

## Tool Used
Claude (claude-sonnet-4-6) via claude.ai

## How I Used It

I used Claude as a technical collaborator — not as a code generator I blindly copied from.
Claude provided starting points and suggestions. I reviewed everything, changed what didn't
fit, debugged what broke, and made all the architectural decisions myself.

The split was roughly:
- **Claude:** Generated boilerplate, suggested patterns, helped debug errors I pasted in
- **Me:** Drove requirements, changed code that didn't work, made all trade-off decisions,
  tested everything live, and directed what to build next

---

## Session 1 — Architecture Planning

**What I asked:**
> I have a T-Mobile take-home. They want a FastAPI service that ingests feature usage
> events and answers analytics questions. SQLite for storage, Docker, pytest.
> What's the right structure?

**What Claude suggested:** Repository pattern, separate routers, Pydantic v2 validation.

**What I changed:** Claude initially suggested a more complex layered structure with
separate service classes. I simplified it — for this scope, the repository does both
data access and business logic. Cleaner for a 1-3 hour assignment.

**Why I kept the repository pattern:** The interviewer literally asked about database
swappability (SQLite → Postgres → CosmosDB). This directly answered that concern.
I recognized it was the right call — Claude didn't make that connection, I did.

---

## Session 2 — Metadata Design Decision

**What I asked:**
> The metadata field can be any JSON. Separate columns or JSON string?

**What Claude suggested:** JSON string with json_extract() for SQLite, JSONB for Postgres.

**What I changed:** Claude's initial schema had the metadata column named `metadata`.
I renamed it to `metadata_json` to make it obvious in the codebase that it's stored
as a string, not a native object. Small change, but it avoids confusion when reading
the code later.

**My decision on indexes:** Claude suggested a single index on timestamp. I pushed
back and asked for a composite index on (feature, timestamp) because our queries
always filter by feature first, then time range. That's more efficient for the
analytics queries we're actually running.

---

## Session 3 — Analytics Endpoints

**What I asked:**
> Build the top-features endpoint with start/end filtering and unique user count.

**What Claude gave me:** A working endpoint — but it was missing date filtering on
the metadata-breakdown endpoint. Claude only added start/end to top-features and
unique-users.

**What I caught and fixed:** I noticed the Plan Breakdown and Device Breakdown charts
on the dashboard weren't changing when I switched date ranges. I diagnosed it was
the metadata-breakdown endpoint missing date parameters — not a dashboard bug.
I directed Claude to fix both the router and the repository layer.

This is a good example of where my testing caught something Claude missed.

---

## Session 4 — Real Bugs I Debugged

### Bug 1 — SQLite path error

```
sqlalchemy.exc.OperationalError: unable to open database file
```

Claude suggested several fixes. The first two didn't work. I kept testing each one
and reporting back what happened. The final fix was adding a Docker volume mount
so the database file persists outside the container:

```yaml
environment:
  - DATABASE_URL=sqlite:////app/data/analytics.db
volumes:
  - ./data:/app/data
```

I also created the `data/` directory locally. Claude told me what to do — I had to
figure out which suggestion actually fixed it through trial and error.

### Bug 2 — IndentationError

```
IndentationError: expected an indented block after function definition on line 106
```

When I updated the metadata_breakdown function I accidentally used 2 spaces instead
of 4. I pasted the error to Claude, it spotted the issue. But I had to actually go
into the file and fix it — and I had to do it twice because the first paste didn't
save correctly. I learned to always verify with `docker-compose logs` after rebuilding.

### Bug 3 — Dashboard date filter not working

The dashboard had date pickers but they weren't connected to the API calls. Claude
had built the dashboard with hardcoded URLs:

```javascript
// What Claude originally wrote
const r = await fetch(`${API}/analytics/top-features?limit=10`);
```

I spotted this when changing dates did nothing. I asked Claude to fix it and also
asked for preset buttons (Today, 7 Days, 30 Days, All Time) which Claude hadn't
thought to include. That was my addition to the UX.

---

## Session 5 — Tests

**What I asked:**
> How do I test FastAPI without hitting a real database?

Claude showed me the dependency_override pattern and wrote the core test fixtures.

**Tests I directed specifically:**
- Whitespace-only user_id should return 422 (Claude's initial tests didn't cover this)
- Empty batch should return 422 (I added this edge case)
- Unknown feature unique-users should return 0, not an error (I specified this behavior)
- metadata-breakdown with no matching data should return empty list, not 404

Claude wrote the test code. I decided what behaviors needed to be tested.

**Result:** 20/20 passing.

---

## Session 6 — Seed Script

**What I asked:**
> Generate realistic T-Mobile seed data — 10 features with weighted distribution,
> 500 users, plan/device/region metadata, spread across 5 years so date filtering
> is actually meaningful in the demo.

**What I changed:** Claude used `random.uniform()` for timestamp spread which clusters
data unevenly. I changed it to `random.randint()` for more even distribution across
years. Small but important for the demo — you want clearly different counts when
switching between "7 Days" and "All Time".

---

## Session 7 — Dashboard Design

**What I asked:**
> T-Mobile magenta theme, dark background, bar chart for top features, donut for
> device breakdown, horizontal bars for plan breakdown, feature ranking list.

Claude built the HTML/CSS/JS. I directed the specific additions:
- Date filter bar with From/To inputs
- Preset buttons I designed (Today / 7 Days / 30 Days / All Time)
- Active range label showing current window
- Refresh Data button
- The "Showing: X → Y" indicator so it's clear what data you're looking at

The core dashboard was Claude's. The UX decisions were mine.

---

## Summary

| Section | Claude's Contribution | My Contribution |
|---|---|---|
| Project structure | Suggested patterns and boilerplate | Simplified the structure, made trade-off calls |
| Database schema | Generated the model and migrations | Added composite index, renamed metadata_json |
| API endpoints | Generated working endpoint code | Caught missing date params, directed fixes |
| Debugging | Diagnosed errors when I pasted them | Reproduced bugs, tested each fix, verified with logs |
| Tests | Wrote test code and fixtures | Decided what behaviors to test, added edge cases |
| Seed script | Generated the script | Changed uniform to randint for even distribution |
| Dashboard | Built HTML/CSS/JS | Designed the UX, added preset buttons and date filter |
| README & docs | Wrote first drafts | Corrected inaccuracies, added real response examples |

