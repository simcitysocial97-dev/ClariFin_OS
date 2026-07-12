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

### Behaviour Engine Phase 2 — Debt Intelligence (COMPLETE)
- Added `round_decimal()` helper to `utils.py` for 4-decimal precision output
- Created `debt.py` with 4 debt metrics:
  - `compute_credit_dependency_ratio` — credit-funded expenses / total expenses
  - `compute_debt_cycle_score` — 0-100 score based on advances, revolving, and debt trend
  - `compute_foir` — Fixed Obligation to Income Ratio with HEALTHY/MODERATE/WARNING/CRITICAL bands
  - `compute_credit_revolver_ratio` — months with partial payment / active credit months
- All functions pure, integer paise inputs, Decimal outputs
- Validation: 23 tests passing, ruff clean, mypy clean on source files

### Behaviour Engine Phase 3 — Pattern Detection (COMPLETE)
- Created `patterns.py` with 5 pattern detection functions:
  - `detect_impulse_transactions` — weekend/night spending on shopping/food/entertainment
  - `compute_weekend_spend_ratio` — ratio of weekend spending to total
  - `compute_night_spend_ratio` — ratio of night-time spending (requires time_iso)
  - `detect_recurring_merchants` — merchants appearing across multiple months
  - `detect_subscription_patterns` — same-day/same-amount recurring patterns
- All functions accept optional `time_iso` field for future time-based detection
- Validation: 17 tests passing, ruff clean, mypy clean on source files

### Behaviour Engine Phase 4 — Income Intelligence (COMPLETE)
- Created `backend/src/engines/behaviour_engine/income.py` with income analysis functions:
  - `classify_income_source()` — Classifies transactions into SALARY, BUSINESS, INVESTMENT, TRANSFER, REFUND, BORROWING, or UNKNOWN with confidence scoring
  - `compute_salary_dependence_ratio()` — Ratio of salary income to total true income
  - `compute_income_diversification_score()` — Score based on unique true income sources (salary/business/investment)
  - `filter_true_income()` — Filters out TRANSFER/REFUND/BORROWING from income transactions
  - `compute_true_income_total()` — Sum of true income amounts
- Updated `backend/src/engines/behaviour_engine/__init__.py` to export income functions
- Created `backend/tests/test_behaviour_engine_income.py` with 40 tests covering:
  - All income classification categories
  - Salary dependence ratio calculations
  - Income diversification scoring (excludes non-true income)
  - Edge cases and determinism
- Validation: ruff clean, mypy clean on source files, 40 pytest tests passing

### Behaviour Engine Phase 5 — Account Intelligence (COMPLETE)
- Created `backend/src/engines/behaviour_engine/account.py` with 4 account analysis functions:
  - `compute_account_concentration()` — Ratio of largest liquid account balance to total liquid assets
  - `compute_idle_cash_amount()` — Detects idle cash based on loan/deposit rate differential (default 300bps threshold)
  - `detect_balance_volatility()` — Uses coefficient of variation on monthly balance history
  - `detect_low_balance_risk()` — Risk score (0-1) based on essential expenses coverage
- Updated `backend/src/engines/behaviour_engine/__init__.py` to export account functions
- Created `backend/tests/test_behaviour_engine_account.py` with 33 tests covering:
  - Multiple savings accounts (concentration analysis)
  - Idle funds detection (opportunity cost scenarios)
  - Uneven balances (volatility and low balance risk tests)
- Validation: ruff clean, mypy clean on source files, 33 pytest tests passing

### Behaviour Engine Phase 6 — Financial Personality Classification (COMPLETE)
- Created `backend/src/engines/behaviour_engine/profile.py` with personality classification
- Implemented `classify_financial_personality()` returning (profile, confidence, explanation)
- Five personality profiles: SAVER, BALANCED, SPENDER, DEBT_OPTIMIZER, DEBT_DEPENDENT
- Classification priority: DEBT_DEPENDENT > SAVER > DEBT_OPTIMIZER > SPENDER > BALANCED
- Confidence calculation based on strong conditions, secondary conditions, and transaction volume
- Updated `backend/src/engines/behaviour_engine/__init__.py` to export the function
- Created `backend/tests/test_behaviour_engine_profile.py` with 27 tests covering all profiles
- Validation: ruff clean, mypy clean on source files, 27 pytest tests passing

### Remaining Work

---

## CGC MCP Verification (Completed)

**Status:** CodeGraphContext MCP server is fully operational.

**Indexing Statistics:**
- 358 files indexed
- 2,790 functions parsed
- 249 classes extracted
- 1,590 parameters captured
- TypeScript interfaces indexed (10+ including Transaction, Money, StatementValidation)

**Tools Verified:**
- ✅ `find_code("SymbolName")` - Returns full source code with INDEX_SOURCE=true
- ✅ `execute_cypher_query` - Working for graph traversal
- ✅ `find_dead_code` - Identifies potentially unused functions
- ✅ `analyze_code_relationships` - NOW WORKING (was socket error, resolved automatically)

**Relationship Graph Stats:**
- 108 CALLS relationships between functions found
- Relationship types available: CALLS, IMPORTS, HAS_PARAMETER, INHERITS, CONTAINS

**Changes Applied:**
- Added CGC MCP priority rule to `.clinerules` (Section 7)
- Updated `servers/.mcp.json` with CGC MCP server configuration