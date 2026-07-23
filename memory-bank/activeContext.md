# Active Context — ClariFin_OS Recovery

## Current Branch
`recovery/phase-1-verification-infra` (commit `549149ca`)

## Phase 2 — Backend Recovery & Modular Integration ✅ COMPLETE

### Changes Made (July 2026)
- Restored 3 engine packages: `financial_intelligence/` (7 files), `transaction_intelligence/` (5 files), `financial_events/` (2 files)
- Merged 3 behaviour engine modules: `credit_dependency.py`, `stress.py`, `temporal.py`
- Restored 3 services: `financial_intelligence_service`, `financial_events_service`, `transaction_intelligence_service`
- Restored 4 repositories: `financial_event_repository`, `financial_goal_repository`, `transaction_classification_repository`, `liquidity_pattern_repository`
- Merged `balance_repository.get_running_balance_rows()` into `account_balance_repository`
- Restored missing repo methods from Recon-V2: `cashflow_repository`, `statement_repository`, `loan_repository`
- Restored models: `financial_goal.py`, updated `financial_event.py` with `LifecycleState`
- Restored router: `financial_intelligence.py`
- Updated package `__init__.py` exports for models, repositories, services
- Fixed imports: relative imports in `transaction_intelligence` package, `src.engines.loan_engine.emi` in `scenario.py`
- Fixed type: `cast(event_type, EventType)` in `financial_events_service`

### Verification
- ruff: all checks passed
- mypy: pass (excluding pre-existing pandas/camelot/uvicorn stubs)
- All Phase 2 modules import successfully

## Engine Package Audit (July 2026)
- Audited 5 engines against Recon-V2 commit `363ea27e`
- **Finding:** No modular structure was lost during branch divergence
- All engines maintain identical structure in both versions:
  - 4 monolithic engines: reconciliation_engine, balance_engine, nudge_engine, insight_generator
  - 1 package-based engine: recommendation_engine
- **Decision:** KEEP CURRENT — No recovery actions required
- Report: `docs/ENGINE_PACKAGE_AUDIT_REPORT.md`
- **Backend engine architecture: FROZEN**

## Phase 3 — Runtime Capability & Pipeline Audit ✅ COMPLETE

### Changes Made (July 2026)
- Completed capability-level audit of all 14 financial domains
- Discovered 22 repositories, 18 services, 11 engines, 22 routers
- Mapped complete execution pipelines for each domain
- Identified 6 broken edges in runtime pipeline
- Generated Capability Graph: `docs/PHASE_3_CAPABILITY_GRAPH.md`
- Generated Integration Gap Report: `docs/PHASE_3_INTEGRATION_GAP_REPORT.md`

### Key Findings
- **Backend completeness:** 85% (14/16 components complete)
- **Pipeline integrity:** 70% (3 broken edges identified)
- **Critical gaps:**
  - Missing router for Financial Events service
  - Duplicate behaviour routers (`behaviour.py` + `behavior.py`)
  - Missing TransactionService layer
  - No auto-trigger from upload to Intelligence/Recommendations
- **Dead endpoints confirmed:** `/loans`, `/investments`

### Deliverables
- Capability Graph with 14-domain status matrix
- Integration Gap Report with priority remediation plan
- Evidence-based findings with file:line references

### Backend Architecture: FROZEN

## Phase 4 — Runtime Capability Verification & Repair ✅ COMPLETE

### Changes Made
- Fixed 6 frontend capability hook URL mismatches (behaviour, networth, cashflow, loans, investments, reconciliation)
- Fixed Dashboard DTO: `DashboardService.get_summary()` now returns `DashboardSummaryDTO` instead of `DashboardSummary` model; router `response_model` updated
- Fixed Behaviour endpoint: frontend now calls `/api/v1/behaviour` (workspace endpoint) instead of `/api/v1/behavior/summary`
- Integrated `TransactionIntelligenceService` into `StatementProcessingOrchestrator` as Stage 6 (EMI/CC/cash classification)
- Quality gates: ruff ✅, mypy ✅ (no new errors), tsc ✅

### Files Modified
- Frontend: 6 capability hooks in `frontend/lib/capabilities/`
- Backend: `dashboard.py`, `dashboard_service.py`, `statement_orchestrator.py`
- Docs: `docs/PHASE_4_VERIFICATION_REPORT.md`

### Next Steps
- Phase 5: Frontend dashboard mapper alignment (verify `dashboard-mapper.ts` handles new DTO fields)

## Phase 5 — Pipeline Integrity Audit & Repair ✅ COMPLETE

### Changes Made
- Removed dead duplicate `BehaviorService` (American spelling) from `services/__init__.py` exports
- Verified complete runtime pipeline: upload → orchestrator → all 6 stages → routers
- Produced `docs/PIPELINE_INTEGRITY_REPORT.md`

### Verification
- ruff: all checks passed ✅
- mypy src/: 8 pre-existing errors (none introduced) ✅
- Backend startup: 114 routes, 86 OpenAPI paths ✅
- Pipeline integrity: all 6 orchestrator stages execute at runtime ✅

### Next Steps
- Phase 6: Frontend dashboard mapper alignment (verify `dashboard-mapper.ts` handles new DTO fields)
