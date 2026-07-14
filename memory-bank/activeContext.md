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

### Next Priority Actions
- Refactor balance_engine.py and ledger_audit_engine.py (High severity)
- Remove behavior/behaviour duplicate aliases (Low severity)
- Add correlation ID framework for observability
- Consider adding stationarity tests and outlier handling to forecast engine
- Close security gaps: auth, authorization, file upload validation, centralized audit logging
