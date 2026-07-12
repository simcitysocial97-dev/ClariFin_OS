# Active Context

## Current Phase: Phase 3 — Service Layer (COMPLETE)

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

### Phase 3 Implementation Summary

**Service Layer** (`src/services/account_service.py`)
- CRUD methods: `create_account()`, `get_account()`, `list_accounts()`, `update_account()`, `deactivate_account()`
- Balance snapshot methods: `insert_balance_snapshot()` (with validation), `get_balance_history()`, `get_latest_balance()`
- Balance analytics (engine delegation): `calculate_average_balance()`, `calculate_balance_change()`, `calculate_balance_growth()`, `calculate_balance_trend()`, `calculate_balance_velocity()`
- Cash flow (engine delegation): `calculate_cash_flow()` with balance history proxy
- Dormancy (engine delegation): `get_account_status()`, `is_account_dormant()`
- Metrics (engine delegation): `get_account_metrics()`
- Institution orchestration: `create_institution()`, `get_institution()`, `list_institutions()`, `update_institution()`
- Account linking: `link_accounts()` (with validation), `unlink_accounts()`, `get_linked_accounts()`

**Tests**
- `test_account_service.py` — 17 mocked tests verifying repository and engine delegation

### Validation Results
- ruff: All checks passed
- mypy: No issues found in 2 source files
- pytest: 17 service tests passing

### Next Phase
- Router Layer integration (account_router endpoints)