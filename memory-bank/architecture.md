# Architecture Map

## Backend Folder Structure

```
backend/src/
├── app/           # FastAPI application setup
├── common/        # Shared utilities
├── core/          # Domain models and services
├── engines/       # Pure computation engines (15+ packages)
├── extraction/    # PDF/table extraction
├── models/        # Domain models
├── reports/       # Report generation
├── repositories/  # SQL access layer (extends BaseRepository)
├── routers/       # HTTP entry points (FastAPI routers)
├── services/      # Orchestration layer
├── structural/    # Structural helpers
├── utils/         # Utilities
├── api.py         # FastAPI app entry point
└── db.py          # SQLite manager (FinanceDB)
```

## Application Layers

### Layer Hierarchy (Dependency Direction)

```
Router (HTTP) ─→ Service (orchestration) ─→ Engine (pure logic) ─→ Repository (SQL) ─→ SQLite
```

| Layer | Path | Key Contract |
|-------|------|--------------|
| Routers | `src/routers/` | HTTP validation + delegation only |
| Services | `src/services/` | Orchestrate only, no raw SQL |
| Engines | `src/engines/` | Pure functions, no DB access |
| Repositories | `src/repositories/` | SQL only, extends BaseRepository |

### Allowed/Forbidden Imports

| Layer | Can Import | Cannot Import |
|-------|------------|---------------|
| Routers | Services, Models, DTOs | FinanceDB, repositories |
| Services | Engines, Repositories, Models | FinanceDB directly |
| Engines | Models only | FinanceDB, sqlite3, repositories |
| Repositories | FinanceDB, Models | None |

## Entry Point

- `backend/src/api.py` — FastAPI app with routers registered
- `backend/src/db.py` — FinanceDB SQLite manager with schema creation

## Key Architectural Rules

| Rule | Description |
|------|-------------|
| QEA-1 | Engines are pure functions (no sqlite3, repos, routers, FastAPI) |
| QEA-2 | Repositories only SQL (no business logic) |
| QEA-3 | Services orchestrate only (no raw SQL) |
| QEA-4 | Routers validate + delegate only |
| QEA-5 | Money: INTEGER paise (₹1.00 = 100 paise) |
| QEA-6 | Confidence: INTEGER bps |
| QEA-7 | Scope: accounts.owner_id/household_id is source of truth |

## Repository Boundary Rule

**Only `src/repositories/` may import `FinanceDB`.**

Violations:
- `sqlite3.connect()` calls inside engines (purity violation)

## Test Infrastructure (Decoupled from Memory Bank)

- Capability registry: `backend/tests/generated/capability-registry.yaml`
- Test suites:
  - `tests/unit/` — Unit tests
  - `tests/invariant/` — Invariant tests
  - `tests/property/` — Property-based tests
  - `tests/golden/` — Golden dataset tests

## Validation Workflow

```bash
# Backend
cd backend && ./venv/bin/python3 -m ruff check .
cd backend && ./venv/bin/python3 -m mypy .

# Frontend
cd frontend && npx tsc --noEmit
```

## Known Duplicate Code (Technical Debt)

| Component | Duplicate | Status |
|-----------|-----------|--------|
| `routers/behavior.py` | `routers/behaviour.py` | US/UK spelling |
| `services/behavior_service.py` | `services/behaviour_service.py` | Legacy wrapper |
| `engines/behavior_engine.py` | `engines/behaviour_engine/` | Deprecated vs canonical |
