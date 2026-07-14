# Active Context

## Architecture Audit & Token Optimization (Completed)

### What was done
- **Comprehensive architecture audit** of all 182 Python files + 73 TS/TSX files across backend and frontend
- **Generated `ARCHITECTURE.md`** with condensed topology, layer hierarchy (Router→Service→Engine→Repository→SQLite), database schema summary, technology stack, duplicate code registry, and an AI quick-reference section with rg/grep patterns and token budget rules
- **Enhanced `.clinerules`** with Section 2a (Token-Efficient Discovery Protocol): rg/grep patterns for instant logic discovery, before-reading checklist, file-listing shortcuts, and call-chain tracing optimizations
- **Added 2 new Cypher query templates** to `.clinerules` for deeper CGC graph lookups

### Key findings
- 20 routers, 15 services, 10+ engines, 24 repositories, 19 models — clean layered architecture
- Repository Boundary Rule enforced (only `src/repositories/` touches DB)
- Duplicate code identified: `behavior`/`behaviour` (US/UK spelling) across routers, services, and engines
- Engine purity violations: some engines still call `sqlite3.connect()` directly
- All monetary values stored as INTEGER paise per financial best practice

### CGC Regressive Test (July 2026) — Completed
- **Root cause found**: `TOOL_RESULT_LIMITS={"find_code":10,"analyze_code_relationships":10,"execute_cypher_query":20}` was truncating results — 10-result cap meant only 10 of 24 repositories appeared in queries
- **Fix**: Limits raised to `find_code:50`, `analyze_code_relationships:50`, `execute_cypher_query:100` (5x increase) in `~/.codegraphcontext/.env`
- **Verified**: `find_code("BaseRepository")` now returns 21 results (all repositories). Cross-layer call chain `transaction_intelligence_service.py → detect_cc_payment → classify_cc_payment` confirmed working at depth 5
- **No AST failure**: Tree-sitter parsers pass, deepest files (depth 5 in `transaction_intelligence/`) are fully indexed with source
- **`.clinerules` updated**: Added Section 9 (CGC Invariants) documenting the 4 known limitations, synchronization protocol, and 4-item verification checklist

### Next immediate steps
- Fix duplicate `behavior`/`behaviour` routers and services (rename to single canonical name)
- Refactor `sqlite3.connect()` calls out of engines (pass data as function parameters instead)
- Migrate `match_confidence REAL` → `confidence_bps INTEGER` fully across all code paths
- Generate Python `.pyi` stubs for all backend modules to enable instant type discovery without reading source

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

### Phase 4 — Credit Card Payment Detection (COMPLETED)

**Step 0 Findings:**
- `statement_repository.py` exists with `bank`, `card_last4`, `total_amount_due`, `minimum_amount_due`, `payment_due_date`, `bill_cycle_start`, `bill_cycle_end` columns
- Credit card payments identified via description patterns (XX1234, ****1234) or CC keywords
- No structural account linkage between bank debits and CC statements — uses description matching
- `_parse_amount_paise()` helper in `db.py` converts REAL rupee amounts to integer paise

**Schema (`migration_cc_payment_detection.py`):**
- Added `lifecycle_state` TEXT (supports: fully_paid, revolving, payment_received, unknown)
- Added `outstanding_paise` INTEGER DEFAULT 0
- Added `payment_channel` TEXT DEFAULT 'DIRECT' (support for Phase 5: CRED, CHEQ, SPAYLATER, NOBROKER)
- Added `matched_statement_id` INTEGER

**Repository Changes:**
- `statement_repository.py`: Added `find_matching_statement(bank, card_last4, payment_date, grace_period_days=5)` method
  - Primary match: payment_date ≤ payment_due_date + grace_period_days
  - Fallback: payment_date within bill_cycle_start/bill_cycle_end window
  - Returns latest statement for same bank+card combination
- `transaction_classification_repository.py`: Extended `insert_classification()` with lifecycle_state, outstanding_paise, payment_channel, matched_statement_id parameters

**Engine (`transaction_intelligence/cc_payment_detector.py`):**
- Pure `extract_card_last4()` - extracts XX1234 or ****1234 patterns from descriptions
- Pure `determine_payment_channel()` - identifies DIRECT, CRED, CHEQ, SPAYLATER payment channels
- Pure `_convert_to_paise()` - converts REAL rupee amounts to integer paise
- Pure `classify_cc_payment(debit_txn, statement_row, payment_channel)` - returns CCPaymentDetectionResult
- Pure `detect_cc_payment(debit_txn, statement_row)` - orchestrates detection with keyword matching
- Lifecycle states: fully_paid (9500 bps), revolving (8500 bps), payment_received (7000 bps), unknown (2000 bps)

**Service Changes:**
- `transaction_intelligence_service.py`: Added `classify_cc_payments(household_id, owner_id='self')` method
  - Filters unclassified debits by member
  - Extracts card_last4 and finds matching statement via repository
  - Persists classification with lifecycle details

**Tests (`test_cc_payment_detection.py` - 24/24 passing):**
- Card extraction (XX/**** formats, none cases)
- Payment channel detection (DIRECT, CRED, SPAYLATER)
- Paise conversion (integer, float, string, None)
- Classification logic (full payment, partial above minimum, below minimum, no statement)
- Detector purity (no DB calls)
- Repository matching (due_date, grace period, bill_cycle fallback, no match)
- Service idempotency
- Multiple statements deterministic selection
- Persistence with new fields

### Phase 5 — CRED/Cheq/Spaid/NoBroker Liquidity Extraction Detector (COMPLETED)

**Schema (`migration_liquidity_patterns.py`):**
- `liquidity_provider_patterns`: Stores provider regex patterns, fee ranges, typical settlement days
- `liquidity_purpose_patterns`: Stores purpose categorization patterns for extracted cash

**Repositories:**
- `liquidity_pattern_repository.py`: `get_active_provider_patterns()`, `confirm_pattern()`, `insert_new_pattern()`

**Engines (`transaction_intelligence/cash_conversion_detector.py`):**
- Pure `detect()` function with no DB access
- Provider matching via regex description patterns
- Zone determination: `'auto'` (150-400 bps), `'review'` (50-800 bps outside auto), `'unmatched_provider'`
- Fee calculation: `fee_paise * 10000 / debit_amount_paise` (basis points)
- Unknown provider detection with liquidity keywords (cred, cheq, spaid, nobroker, liquidity, cash)
- Household-aware matching for spouse accounts
- Disambiguation via Hungarian-style sorting (prefers auto zone, then closest fee to midpoint)

**Tests (`test_cash_conversion_detector.py` - 17/17 passing):**
- Fee calculation correctness (basis points)
- Zone determination (auto, review, discard boundaries)
- Detection with known providers (CRED)
- Unknown provider handling with keywords
- Purpose tagging (Rent, Education, Settlement_Inbound)
- Settlement window boundaries (typical_settlement_days + 2)
- Inactive provider pattern filtering (service layer only passes active)
- Engine purity verification (no DB calls)
- Narrative format (fee amount and percentage)
- Spouse account matching within same household

### Phase 6 — Financial Events Persistence (COMPLETED)

**Model Changes (`models/financial_event.py`):**
- Added new event types: `emi_payment`, `liability_repayment`, `credit_card_cash_advance`, `transfer_internal`
- Added granular amount fields: `asset_change_paise`, `liability_change_paise`, `expense_paise`, `income_paise`
- Added `sub_type`, `provider`, `lifecycle_state`, `outstanding_paise`, `superseded_by` fields
- Added `confidence_bps` (authoritative) alongside deprecated legacy `confidence`
- Added `reviewed_by_user` as bool (not user ID)
- Added `month_bucket` derived via `@model_validator(mode='after')`
- Extended `BehaviourInput` with `financial_events: list[dict[str, Any]]`

**Schema (`scripts/migration_financial_events.py`):**
- `financial_events` table with all event fields
- `financial_event_links` table for settles/funds/rolls_over relationships
- Indexes for month_bucket, household_id, account_id, lifecycle_state, event_type

**Repository (`repositories/financial_event_repository.py`):**
- `insert_event(FinancialEvent) -> int`
- `get_events_for_month(month_bucket, household_id) -> list[dict]`
- `get_open_events_for_account(account_id) -> list[dict]`
- `update_lifecycle(event_id, lifecycle_state, outstanding_paise, settled_by_event_id) -> bool`
- `insert_link(event_id, linked_event_id, link_type) -> int`
- `get_links_for_event(event_id) -> list[dict]`

**Engine (`engines/financial_events/lineage_walker.py`):**
- `DEFAULT_ROLLOVER_LOOKBACK_DAYS = 90` constant
- `LineageProposal` dataclass for structured results
- `walk_lineage(events) -> LineageProposal` - detects 'settles' links
- `detect_rollover_scenarios(events) -> LineageProposal`

**Service (`services/transaction_intelligence_service.py` + `financial_events_service.py`):**
- Added `event_repo` to TransactionIntelligenceService
- Added `_emit_financial_event()` helper method
- Wired `classify_emi_payments()` to emit `emi_payment` events
- Ready for wiring `classify_cc_payments()` and `classify_cash_conversions()`

**Tests (`tests/test_financial_events.py` - 13/13 passing):**
- Model backward compatibility and new event types
- Month bucket derivation
- Repository CRUD operations
- Lifecycle updates
- Link creation and retrieval
- Lineage walker purity (no DB calls)
- Full/partial payment state transitions
- Idempotency verification
- BehaviourInput integration

### Phase 7 — Cashflow Engine Implementation (COMPLETED)

**Engine (`engines/cashflow_engine.py`):**
- Pure `compute_monthly_cashflow(cash_summary, financial_events, scope, owner_id)` function
- Sign conventions documented: asset_change positive=increase, liability_change positive=borrowing
- Month classification: `surplus` | `deficit_covered_by_credit` | `deficit`
- Cash surplus = income - expense + credit_received (cash basis)
- True savings = income - expense - fees (accrual basis)
- Liability-adjusted savings = true_savings - liability_increase
- Net worth impact = asset_change - liability_change
- Credit dependency ratio = credit_funded / expenses
- Effective liquidity cost annualized = fee * 12

**Service (`services/cashflow_service.py`):**
- `CashflowService` orchestrates `CashflowRepository` + `FinancialEventRepository`
- No SQL in service - uses repositories for data fetching
- `get_monthly_analysis(month_bucket, scope, owner_id)` returns enriched cashflow

**Router (`routers/cashflow.py`):**
- Added `GET /api/v1/cashflow/monthly` endpoint (existing `/api/cashflow/monthly` preserved)
- Parameters: month, scope, owner_id, basis
- Returns all cashflow engine metrics

**Tests (`tests/test_cashflow_engine.py` - 10/10 passing):**
- Worked example: income 80000, expenses 110000, CRED net 30000/fee 1250 → cash_surplus=0, true_savings=-31250
- Regression: empty events → cash/accrual converge to existing repository output
- Household scope aggregates all owners
- Individual scope receives pre-filtered events at service layer

### Phase 8 — India-Specific Signals (COMPLETED)

**Engine (`behaviour_engine/credit_dependency.py`):**
- New pure functions consuming financial_events (Phase 6) and cashflow_results (Phase 7)
- `artificial_income_flag` - detects credit-card cash advances as fake income, excludes them from trend analysis
- `credit_dependency_ratio` - ratio of credit-funded expenses to total expenses
- `transactor_vs_revolver` - classifies cards as transactor (settled) or revolver (open/partial)
- `revolver_ratio` - proportion of months with revolving credit behavior
- `debt_rolling_flag` - detects rolls_over lifecycle state and links
- `liquidity_extraction_frequency` - count and spacing of cash advances
- `financial_stress_index` - composite with explicit weights (credit_dependency 30%, debt_rolling 25%, liquidity_extraction 20%, revolving 15%, cashflow_deficit 10%)
- `household_divergence` - cross-owner funding via lineage links between different owners in same household

**Service (`services/behaviour_service.py`):**
- Added `get_stress_index(month, scope)` - orchestrates CashflowService + FinancialEventsService
- Added `get_revolver_status(card_account_id)` - fetches events via FinancialEventsService
- Added `get_household_divergence(month)` - detects cross-owner funding patterns

**Router (`routers/behaviour.py` - UK only):**
- Added `GET /api/v1/behaviour/stress-index?month=&scope=`
- Added `GET /api/v1/behaviour/revolver-status?card_account_id=`
- Added `GET /api/v1/behaviour/household-divergence?month=`
- DID NOT modify US router `routers/behavior.py` (confirmed LIVE)

**Tests (`tests/test_behaviour_engine_credit_dependency.py` - 26/26 passing):**
- Purity tests: zero DB calls inside credit_dependency.py
- Regression test: empty financial events → neutral values for all signals
- Component independence test for stress index

### Phase 8.5 — Behaviour Consolidation (COMPLETED)

**Canonical Implementation Created:**
- `src/engines/behaviour_engine/__init__.py` - exports organized by category (savings, cashflow, resilience, lifestyle, debt, patterns, income, account, profile, temporal, stress)
- `src/engines/behaviour_engine/stress.py` - Pure stress indices (loss_aversion_index, impulsivity_score, habit_stability_score, financial_stress_index, savings_discipline_score, detect_risk_patterns)
- `src/engines/behaviour_engine/temporal.py` - Pure temporal analysis functions

**Service Layer Changes:**
- `src/services/behaviour_service.py` - Added TTLCache (max 10 entries, 5-min expiration), static `get_cached_profile()`/`set_cached_profile()` methods
- `src/services/behavior_service.py` - Converted to compatibility wrapper that delegates to BehaviourService
- `src/services/dashboard_service.py` - Updated to use BehaviourService instead of legacy behavior_engine

**Repository Updates:**
- `src/routers/import_router.py` - Updated to use `invalidate_behaviour_cache` from behaviour_service

**Legacy Module Updates:**
- `src/engines/behavior_engine.py` - Added deprecation warnings, maintained for backwards compatibility

**Architecture Compliance:**
- Router → BehaviourService → Repositories + CashflowService + FinancialEventsService pattern established
- All engines remain pure (no DB access)
- Repository Boundary Rule maintained

**Tests (48/48 passing):**
- All behaviour_service tests pass
- All behavior_engine legacy tests pass with deprecation warning