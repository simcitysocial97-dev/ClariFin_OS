# Architecture Map

## Backend Folder Structure

```
backend/src/
├── 182 .py files organized into 9 layers
├── app/           # FastAPI application setup
├── audits/        # Audit-related code
├── common/        # Shared utilities
├── core/          # Core domain logic
├── data/          # Data access layer
├── engines/       # Pure computation engines (12+ packages)
├── extraction/    # PDF/table extraction
├── models/        # Domain models (19 files)
├── reports/       # Report generation
├── repositories/  # SQL repositories (26 files)
├── routers/       # FastAPI routers (25 files)
├── services/      # Orchestration services (17 files)
├── structural/    # Structural helpers
├── utils/         # Utilities
└── venv/ + requirements.txt
```

## Application Layers

### Layer Hierarchy (Dependency Direction)

```
Router (HTTP) ─→ Service (orchestration) ─→ Engine (pure logic) ─→ Repository (SQL) ─→ SQLite
```

| Layer | File Count | Path | Key Contract |
|-------|------------|------|--------------|
| Routers | 25 | `src/routers/` | HTTP validation + delegation only |
| Services | 17 | `src/services/` | Orchestrate only, no raw SQL |
| Engines | 10+ | `src/engines/` | Pure functions, no DB access |
| Repositories | 26 | `src/repositories/` | SQL only, extends BaseRepository |

### Allowed/Forbidden Imports

| Layer | Can Import | Cannot Import |
|-------|------------|---------------|
| Routers | Services, Models, DTOs | FinanceDB, repositories |
| Services | Engines, Repositories, Models | FinanceDB directly |
| Engines | Models only | FinanceDB, sqlite3, repositories |
| Repositories | FinanceDB, Models | None |

## Entry Point

- `backend/src/api.py` — FastAPI app with 22 routers registered
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

## Known Duplicate Code (Technical Debt)

| Component | Duplicate | Status |
|-----------|-----------|--------|
| `routers/behavior.py` | `routers/behaviour.py` | US/UK spelling |
| `services/behavior_service.py` | `services/behaviour_service.py` | Legacy wrapper |
| `engines/behavior_engine.py` | `engines/behaviour_engine/` | Deprecated vs canonical |

## Engine Purity Violations

Some engines call `sqlite3.connect()` directly instead of accepting data via parameters, violating the Repository Boundary Rule.