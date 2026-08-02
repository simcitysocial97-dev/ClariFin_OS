# Backend Cleanup & Organization Plan

## Overview
Address root-level clutter, resolve module duplication, and clean up pre-existing warnings in preparation for Program 6 frontend verification.

---

## Phase 1: Root-Level File Migration

### 1.1 db.py — PARKED with Deprecation Notice
**Current state**: Compatibility shim for old database access pattern (`FinanceDB`)
**Usage**: Only imported by `src/common/database.py` (TYPE_CHECKING)
**Action**: Add explicit deprecation warning at runtime, document removal timeline

```python
# Add at top of db.py:
import warnings
warnings.warn(
    "src.db.FinanceDB is deprecated. Use src.core.db.get_connection() instead.",
    DeprecationWarning,
    stacklevel=2
)
```

**Validation**: Ensure zero production callers exist before removal.

### 1.2 health.py — MIGRATE to core/db/health.py
**Current state**: Standalone health router with `/health` and `/ready` endpoints
**Migration path**:
1. Move `src/health.py` → `src/core/db/health.py`
2. Update import in `src/api.py`: `from src.core.db.health import register_health_routes`
3. Keep backward-compat shim at `src/health.py` that re-exports from new location

**Files affected**:
- `src/api.py` (line 21)
- `src/routers/health.py` (line 4)

### 1.3 ingest.py — MIGRATE to orchestration/ingest.py
**Current state**: CLI ingestion pipeline for PDF→transactions
**Migration path**:
1. Move `src/ingest.py` → `src/orchestration/ingest.py`
2. Update internal imports to use `src.extraction.*` (already done in Milestone 5)
3. Update CLI entry points if any reference `src.ingest`

**Validation**: Run `python src/orchestration/ingest.py --help` to verify CLI works.

### 1.4 validator.py — REMOVE (use extraction/validator.py)
**Current state**: Backward-compat shim created in Milestone 6
**Action**: Remove the shim after confirming all test imports are updated
**Note**: Tests import from `validator` — update them to `src.extraction.validator`

### 1.5 startup.py — MIGRATE to core/startup.py
**Current state**: Application boot validation helper
**Migration path**:
1. Move `src/startup.py` → `src/core/startup.py`
2. Update imports in `src/main.py`

### 1.6 api.py — KEEP
**Rationale**: Standard FastAPI app aggregation point. This is the canonical entry.

---

## Phase 2: Module Duplication Resolution

### 2.1 accounts_router.py — RETIRE (keep accounts.py as canonical)
**Analysis**:
- `accounts_router.py` (3.5KB) — Stage 4 intelligence workspace router
- `accounts.py` (current) — Main accounts router with DTOs, response_models
- `accounts_router.py` is NOT registered in `src/api.py` (only `accounts` is)
- It appears to be a legacy/staging file

**Action**: 
1. Verify no tests reference `accounts_router`
2. Mark `accounts_router.py` with `# DEPRECATED: Use src/routers/accounts.py`
3. Schedule for removal after milestone completion

### 2.2 accounts_service.py — RETIRE (keep account_service.py as canonical)
**Analysis**:
- `account_service.py` — Main service with full CRUD operations
- `accounts_service.py` (12KB) — Stage 4 intelligence workspace service
- Both exported from `src/services/__init__.py`

**Action**:
1. Verify `accounts_service` is only used by `accounts_router.py`
2. Mark `accounts_service.py` as deprecated
3. If `accounts_router.py` is retired, `accounts_service.py` can also be deprecated

### 2.3 utils/ and app/ — PRUNE OR UTILIZE
**Current state**: Empty directories with only `__init__.py`
**Decision**: 
- **Option A**: Remove directories (cleaner)
- **Option B**: Add `src/utils/__init__.py` with common utilities
- **Recommendation**: Keep `app/` for future page-level utilities, remove `utils/` if unused

---

## Phase 3: Warning Resolution & Technical Debt

### 3.1 Pydantic v2 Migration Warnings
**Issue**: `orm_mode` became `from_attributes = true` in Pydantic v2
**Action**: Search for and fix any remaining `orm_mode` references:
```bash
grep -rn "orm_mode" src/ tests/ --include="*.py"
```

### 3.2 RuntimeWarnings from Async DB Sessions
**Issue**: SQLite connection pooling may trigger ResourceWarning
**Action**: Add warning filters in `tests/conftest.py`:
```python
import warnings
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", message="unclosed.*sqlite")
```

### 3.3 OpenAPI Operation ID Duplicates
**Issue**: Two warnings about duplicate operation IDs in loans router
**Location**: `src/routers/loans.py` lines with `simulate_prepayment` and `simulate_foreclosure`
**Fix**: Add unique `operation_id` parameter to each endpoint decorator.

---

## Implementation Order

1. **Phase 1.1**: Add deprecation warning to `db.py` (non-breaking)
2. **Phase 1.2**: Migrate `health.py` → `core/db/health.py`
3. **Phase 1.3**: Migrate `ingest.py` → `orchestration/ingest.py`
4. **Phase 1.4**: Update test imports from `validator` to `src.extraction.validator`, then remove shim
5. **Phase 1.5**: Migrate `startup.py` → `core/startup.py`
6. **Phase 2.1-2.2**: Deprecate duplicate accounts modules
7. **Phase 2.3**: Decide on utils/app directories
8. **Phase 3.1-3.3**: Fix warnings and technical debt

---

## Validation Gates

| Gate | Check | Pass Criteria |
|------|-------|---------------|
| V1 | App loads | `from src.api import app` succeeds |
| V2 | All routes registered | 114+ API routes in OpenAPI |
| V3 | Tests pass | `pytest tests/` without errors (excluding known integration issues) |
| V4 | No deprecation warnings | Runtime output clean of DeprecationWarning |
| V5 | Health endpoints work | GET /health returns 200 |

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking external scripts using `src.ingest` | Low | Keep CLI working via relocation, not deletion |
| Missing validator imports in other repos | Low | Shim file provides compatibility |
| Health endpoint breakage during migration | Medium | Keep both files during transition period |
| Pydantic v2 migration regressions | Low | Run full test suite before/after |

---

## Open Questions

1. Should `accounts_router.py` and `accounts_service.py` be deleted immediately or kept with deprecation notices?
   - **Recommendation**: Deprecation notices for 1 sprint, then delete.

2. Should `utils/` and `app/` directories be removed entirely?
   - **Recommendation**: Keep `app/` (may be used for Next.js pages), remove `utils/` if truly empty.

3. What is the timeline for removing `db.py`?
   - **Recommendation**: Park for 2 sprints, monitor for zero production usage.
