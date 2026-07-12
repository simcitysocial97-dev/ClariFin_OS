# Active Context

## Current Phase: Phase 2 — Account Engine Persistence (COMPLETE)

### Phase 1 Completion (Reference)
**Engine Layer** (`src/engines/account_engine/`)
- `lifecycle.py` — Account status transitions (ACTIVE/DORMANT/CLOSED)
- `dormant.py` — Dormancy detection (days since activity, configurable threshold)
- `balance.py` — Average balance, balance change, growth percentage (basis points)
- `cashflow.py` — Net flow, daily rate, income/expense ratio (basis points)
- `history.py` — Balance trend (IMPROVING/STABLE/DECLINING), velocity (paise/day)
- `metrics.py` — Aggregate deterministic account metrics

### Phase 2 Implementation Summary

**Migration** (`scripts/migration_004_account_engine.py`)
- Created `account_balance_history` table with UNIQUE(account_id, date_iso) constraint
- Created `institutions` reference table for bank metadata
- Created `account_links` relationship table with CHECK constraints for TRANSFER/JOINT/GUARANTOR

**Repository Layer**
- `AccountRepository` — Extended with `get_accounts_by_type()`, `get_accounts_by_institution()`, `get_active_accounts()`, `deactivate_account()`
- `AccountBalanceRepository` — New: `insert_balance_snapshot()`, `get_balance_history()`, `get_latest_balance()`, `get_balance_on_date()`, `delete_snapshot()`
- `InstitutionRepository` — New: `create()`, `get()`, `list()`, `update()`, `delete()` with INSERT OR IGNORE
- `AccountLinkRepository` — New: `link_accounts()`, `unlink_accounts()`, `get_linked_accounts()`, `relationship_exists()`

**Tests**
- `test_account_balance_repository.py` — 7 tests for snapshot operations
- `test_institution_repository.py` — 7 tests for CRUD operations
- `test_account_link_repository.py` — 7 tests for link operations

### Validation Results
- ruff: All checks passed
- mypy: No issues found in 4 source files
- pytest: 21 repository tests passing

### Next Phase
- Service Layer (AccountService, AccountHealthService)