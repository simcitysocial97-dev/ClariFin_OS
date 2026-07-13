# Active Context

## Phase 0 Discovery Complete — Reconciliation Engine v2 Analysis

### Discovery Findings Summary

**Architecture Layers Verified:**
- Router → Service → Engine → Repository → SQLite flow confirmed
- Key violation: Engines have direct DB access (reconciliation_engine.py, behavior_engine.py)

**Matching Rules Found (reconciliation_engine.py):**
- Exact match: same amount, same date (0 days diff), different accounts
- Window match: same amount, date within 3 days, different accounts
- No disambiguation for multiple candidates
- Confidence: 0.4 (exact date) + 0.4 (exact amount) + 0.2 (transfer keywords)

**Existing Implementations:**
- Reconciliation: Engine, Repository, Service, Router, Model all exist
- Financial Events: Model exists but no table/repository (orphaned)
- Cash Flow: Repository exists but no engine
- Behaviour Engine: Two parallel systems (behavior_engine.py old, behaviour_engine/ new)
- Loan Engine: Full amortization schedule generation with reducing balance
- Credit Card Engine: Outstanding/interest calculations, no statement DB reads

### Key Technical Debt to Address
1. Engine purity violations (direct sqlite3.connect)
2. match_confidence REAL should be INTEGER basis points
3. interest_rate REAL should be INTEGER basis points
4. Duplicate behavior routers (US vs UK spelling)

### Phase 1 — Foundational Schema Changes (Completed)

**New migrations created:**
- `migration_006_household.py`: Adds `owner_id` and `household_id` columns to `accounts` table with backfill to `'self'`/`'primary'` defaults
- `migration_007_reconciliation_audit.py`: Adds `confidence_bps INTEGER` column to `reconciliations` with backfill from `match_confidence`, reports NULL/out-of-range rows, creates `reconciliation_audit_log` table with FK cascade

**Repositories extended:**
- `account_repository.py`: Added `get_household_accounts()`, `get_accounts_by_owner()`, `is_same_household()` (253→295 LOC, under 300 limit)
- `reconciliation_audit_repository.py` (new): `insert_audit_log()`, `get_audit_trail()` — split from reconciliation_repository.py to stay under 200 LOC
- `reconciliation_repository.py`: Added deprecation comment marking `match_confidence` as legacy, `confidence_bps` as authoritative

**Tests (26/26 passing):**
- `test_migration_confidence_bps.py` (4 tests): Backfill correctness, NULL handling, out-of-range flagging, idempotency
- `test_migration_household.py` (4 tests): Column addition, backfill, idempotency, new-account defaults
- `test_audit_repository.py` (6 tests): Insert/retrieve round-trip, multi-entry ordering, empty trail, FK violation (negative test), all-fields
- `test_household_repository.py` (12 tests): Multi-household querying, multi-owner filtering, `is_same_household` across boundaries with non-existent accounts

### Phase 2 — Reconciliation Engine Refactor (COMPLETED)

**Engine Changes (`reconciliation_engine.py`):**
- Renamed `find_potential_matches(db_path, ...)` → pure function `find_potential_matches(debits, credits, household_account_map, ...)`
- Added backward-compatible wrapper `find_potential_matches_with_db(db_path)` for test compatibility
- Upgraded `_calculate_confidence()` to graduated formula (returns tuple: confidence float + confidence_bps int)
- Added Hungarian algorithm (`_build_cost_matrix`, `_hungarian_solve`, `_hungarian_inline`) for bipartite disambiguation
- **Integrated Hungarian solver into `find_potential_matches()` for ambiguity resolution when multiple candidates exist**
- Named constants: `HUNGARIAN_DATE_WEIGHT=100`, `HUNGARIAN_AMOUNT_WEIGHT=1`

**Repository Changes (`reconciliation_repository.py`):**
- Added `get_unreconciled_debits(household_id)` and `get_unreconciled_credits(household_id)` methods
- Updated `insert_reconciliation()` to accept optional `confidence_bps` parameter (backward-compatible)
- Added `insert_audit_log()`, `_get_reconciliation_row()` methods
- Added `undo_reconciliation()` with configurable month boundary lock (`UNDO_MONTH_BOUNDARY_LOCK=True`)

**Service Changes (`reconciliation_service.py`):**
- Fixed `scan_potential_matches()` to use repository for data fetching, then call pure engine
- **Fixed `scan_for_transaction()` to use `TransactionRepository.get_transaction_by_id()` instead of direct sqlite3.connect()**
- Added `confirm_reconciliation_with_audit()` and `reject_reconciliation_with_audit()` with audit logging

**Repository Changes (`transaction_repository.py`):**
- Added `get_transaction_by_id(txn_id)` method to fetch single transaction via repository pattern

**Router Changes (`routers/reconciliation.py`):**
- Breaking change: POST `/create` now accepts `amount_paise: int` and `confidence_bps: int` instead of float params
- Added POST `/undo` endpoint for reverting confirmed reconciliations (blocked across month boundary)

**Tests (40/40 passing):**
- All reconciliation tests remain passing (zero regression)

### Phase 3 — EMI Detection Implementation (COMPLETED)

**Schema (`migration_emi_detection.py`):**
- `loan_amortization_schedule`: Stores computed/bank schedule rows with UNIQUE(loan_id, due_date)
- `transaction_classifications`: Stores classifier results with UNIQUE(transaction_id, classification)

**Repositories:**
- `loan_repository.py`: Added `get_schedule_rows()`, `has_schedule_rows()`, `persist_schedule_rows()`, `update_schedule_row_from_bank()`
- `transaction_classification_repository.py` (new): `insert_classification()`, `get_by_transaction_id()`, `list_unclassified_transaction_ids()`

**Engines (`transaction_intelligence/`):**
- `loan_emi_detector.py`: Pure `detect_emi_payment()` with ±1% amount tolerance, date proximity (±3 days), description keywords
- Priority scale: bank_statement=100, amount+date=85, amount+schedule=90, amount_only=80, date_proximity=75, description=60

**Services:**
- `transaction_intelligence_service.py`: `classify_emi_payments()` with lazy schedule generation, household-aware filtering (owner_id='self')

**Tests (11/11 passing):**
- `test_emi_detection.py`: Schedule generation, amount tolerance matching, bank statement override, detector purity, idempotency, household isolation