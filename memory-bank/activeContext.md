# Active Context

## Current Phase: Phase 4 — API Layer (COMPLETE)

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
- Added `get_days_since_activity()` method for dormancy endpoint
- Balance analytics (engine delegation): `calculate_average_balance()`, `calculate_balance_change()`, `calculate_balance_growth()`, `calculate_balance_trend()`, `calculate_balance_velocity()`
- Dormancy (engine delegation): `get_account_status()`, `is_account_dormant()`
- Metrics (engine delegation): `get_account_metrics()`
- Institution orchestration: `create_institution()`, `get_institution()`, `list_institutions()`, `update_institution()` — pure delegation, no calculations
- Account linking: `link_accounts()` (with validation), `unlink_accounts()`, `get_linked_accounts()`

**Tests**
- `test_account_service.py` — 18 mocked tests verifying repository and engine delegation

### Phase 4 Implementation Summary

**DTO Models** (`src/models/`)
- `account.py` — Extended with `AccountCreateRequest`, `AccountUpdateRequest`, `AccountResponse`, `AccountAnalytics`
- `account_balance.py` — New: `BalanceSnapshotRequest`, `BalanceSnapshotResponse`
- `institution.py` — New: `InstitutionCreateRequest`, `InstitutionUpdateRequest`, `InstitutionResponse`
- `account_link.py` — New: `AccountLinkRequest`, `AccountLinkResponse`

**Router Layer** (`src/routers/accounts.py`)
- Extended existing router with all account endpoints
- Account CRUD: `GET/POST /accounts`, `GET/PUT/DELETE /accounts/{account_id}`
- Balance Snapshot: `POST/GET /accounts/{account_id}/balance-history`, `GET /accounts/{account_id}/balance-history/latest`
- Analytics: `GET /accounts/{account_id}/analytics`, `GET /accounts/{account_id}/metrics`, `GET /accounts/{account_id}/status`, `GET /accounts/{account_id}/dormancy`
- Institutions: `GET/POST /institutions`, `GET/PUT /institutions/{institution_id}`
- Account Linking: `POST/DELETE/GET /accounts/{account_id}/links`

**Tests**
- `test_account_router.py` — 23 tests covering all endpoint categories (CRUD, balance, analytics, institutions, links)

**Validation Results**
- ruff: All checks passed (6 fixes applied)
- pytest: 23 router tests passing

### Behaviour Engine Phase 0 — Architecture Preparation (COMPLETE)
- Created `backend/docs/behaviour_engine_architecture.md` with input data sources, service boundaries, repository dependencies, and engine responsibilities
- Created `backend/src/models/financial_event.py` with FinancialEvent DTO, EventType Literal, FinancialEventBatch, and BehaviourInput interfaces
- Identified transaction repositories (Transaction, Loan, CreditCard, Account, Cashflow, Reconciliation) with income/expense fields
- Identified classification fields: `type` (credit/debit), `category`, `subcategory`
- Validation passed: ruff and mypy clean

### Behaviour Engine Phase 1 — Core Metrics (COMPLETE)
- Created `backend/src/engines/behaviour_engine/` package with pure functions
- Five metric modules: `utils.py`, `savings.py`, `cashflow.py`, `resilience.py`, `lifestyle.py`
- 10 functions: `compute_true_savings_rate`, `compute_borrowed_lifestyle_ratio`, `compute_monthly_surplus`, `compute_income_stability`, `compute_expense_stability`, `compute_cashflow_stability_index`, `compute_liquidity_months`, `compute_resilience_index`, `compute_lifestyle_inflation`, `compute_lifestyle_creep_index`
- All functions use integer paise for monetary inputs, Decimal for percentage outputs
- Validation: ruff clean, mypy clean on source files, 54 pytest tests passing

### Remaining Work
- Integration with Reconciliation layer for actual cash flow aggregation