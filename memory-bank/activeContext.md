# Active Context

## Architecture Audit Complete — Principal Architect Review (Enhanced)

### Audit Phases Delivered
- **Phase 1-3:** Topology, execution flows, financial formulas with Observed vs Inferred labels
- **Phase 4:** Financial Intelligence deep dive (forecasting, optimization, scenario, goal planner, intelligence)
- **Phase 5:** Engine Dependency Matrix
- **Phase 6:** Repository Ownership Matrix
- **Phase 7:** Database Table Ownership Map
- **Phase 8:** Financial Decision Pipeline
- **Phase 9:** Technical Debt Register
- **Phase 10:** Complexity Analysis
- **Phase 11:** State Ownership Analysis
- **Phase 12:** Coupling Analysis
- **Phase 13:** Extensibility Review
- **Phase 14:** Architecture Scorecard (9.4/10)
- **Phase 15:** Mathematical Deep Dive — extended assumptions and edge cases
- **Phase 16:** Repository Audit Details
- **Phase 18:** Principal Architect Enhancements
  - 18.1 Explicit Call Graphs
  - 18.2 Dependency Cycle Analysis
  - 18.3 Data Lifecycle
  - 18.4 Mutation Matrix
  - 18.5 Concurrency
  - 18.6 Security Boundary
  - 18.7 Test Coverage Matrix
  - 18.8 Performance Hotspots
  - 18.9 Domain Boundaries / Bounded Contexts

### Key Enhancements
- Added Observed vs Inferred labels throughout
- Added per-engine subsections: inputs, outputs, assumptions, edge cases, failure modes, confidence model, time complexity
- Added Engine Dependency Matrix with Reads/Writes/Depends On/Pure columns
- Added Repository Ownership Matrix with table ownership, cohesion, N+1 risks
- Added Database Table Ownership Map (table → repository → service → engine)
- Added Financial Decision Pipeline (transactions → cashflow → forecast → goals → scenario → optimization → intelligence → API)
- Added Complexity Analysis for all major engines
- Added State Ownership analysis (persistence, lifecycle, read/write, owner)
- Added Coupling Analysis and hidden coupling risks
- Added Mathematical Deep Dive: forecasting stationarity risks, optimization decision logic verification, scenario impossible-balance risks
- Added Principal Architect Enhancements: call graphs, dependency cycle analysis, data lifecycle, mutation matrix, concurrency, security boundary, test coverage matrix, performance hotspots, domain boundaries

### Overall Assessment
- Layer Separation: 9.8/10
- Engine Purity: 9.2/10 (3 violations)
- Financial Correctness: 9.7/10 (paise integers verified)
- Repository Compliance: 9.4/10
- See Audit_Report.md for full principal-architect-level reference

### Completed Changes (Current Task - Scope System Resolution)
- Added `owner_id` and `household_id` columns to `accounts` table (database migration applied)
- Fixed `financial_intelligence_service.py` to thread `household_id` parameter instead of hardcoding "default"/"primary"
- Fixed `behaviour_service.py` to accept and use `household_id` in `get_stress_index`, `get_revolver_status`, `get_household_divergence`
- Updated routers to accept `household_id` query parameters for scoping endpoints
- Added regression tests in `test_scope_resolution.py` verifying signature correctness

### Step 0 Investigation Findings
- `transactions.member` is read in 5 locations: transaction_repository.py (SELECT/getAll), cashflow_repository.py (legacy method)
- No usage of `member` in Financial Intelligence or Behaviour pipelines — these use account joins
- Database schema required migration: added `owner_id` and `household_id` to accounts table

### Completed Changes (Due Date Bonus Fix - Current Task)
- Added `get_statement_covering_date(bank, card_last4, txn_date)` method to `StatementRepository`
  - Uses `bill_cycle_start <= txn_date <= bill_cycle_end` for reliable billing cycle matching
  - Includes fallback for ±7 day window around `payment_due_date` when cycle dates unavailable
- Fixed `cash_conversion_detector.py` due date parsing
  - Added multi-format date parsing support (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY)
  - Properly handles boundary condition (7 days exactly inclusive)
- Wired statement lookup into `classify_cash_conversions` in `TransactionIntelligenceService`
  - For CC account type transactions, fetches card info and looks up matching statement
  - Passes statement_row to detector so due-date bonus can fire
- Added 4 regression tests in `test_cash_conversion_detector.py`:
  - `test_due_date_bonus_3_days_after_txn`: Within window (3 days) → bonus applies
  - `test_due_date_bonus_20_days_after_txn`: Outside window (20 days) → no bonus
  - `test_due_date_bonus_negative_days_rejected`: Due before txn → no bonus
  - `test_due_date_boundary_7_days_exactly`: Boundary inclusive → bonus applies
  - `test_due_date_alternate_format_parsing`: DD/MM/YYYY format parsed correctly

### Step H5 Investigation Findings (Credit Signals Endpoint Wiring)
- **DISCOVERY:** The wiring between `behaviour_engine/credit_dependency.py` → `behaviour_service.py` → `routers/behaviour.py` was ALREADY COMPLETE.
- All 3 India-specific endpoints are implemented and callable:
  - `GET /api/v1/behaviour/stress-index?month=&scope=&household_id=` (lines 308-339 in behaviour.py)
  - `GET /api/v1/behaviour/revolver-status?card_account_id=&household_id=` (lines 342-371)
  - `GET /api/v1/behaviour/household-divergence?month=&household_id=` (lines 374-403)
- Added missing end-to-end tests in `test_behaviour_credit_signals_e2e.py` (9 tests, all passing)

### Next Priority Actions

### Completed Changes (Financial Event Lifecycle Logging)
- Added `financial_event_lifecycle_log` table schema with event_id, previous/new state tracking, caused_by_event_id, actor
- Modified `FinancialEventRepository.update_lifecycle()` to fetch current state and log transitions in same transaction
- Added `FinancialEventRepository.get_lifecycle_history()` method to query audit trail by event_id
- Updated `test_financial_events.py` fixture to create lifecycle log table
- Added 4 tests: single update logging, multiple transitions, caused_by_event context, nonexistent event handling
