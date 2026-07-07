# Active Context

## Current Mission

**Phase 7: Architecture Corrections & Technical Debt Resolution**

The project has completed a comprehensive 6-phase audit and runtime validation. The current mission is to **execute the prioritized implementation roadmap** derived from the audit findings. This phase focuses on **fixing critical blockers**, **removing dead code**, **resolving unit violations**, and **consolidating duplicate systems** to prepare the codebase for Phase 8 (Feature Implementation).

## Current Phase

| Phase | Status | Artifact |
|-------|--------|----------|
| Phase 0 — Repository Discovery | **COMPLETE** | Audit_Report.md |
| Phase 0 Addendum | **COMPLETE** | Audit_Report.md |
| Phase 1 — Backend Contract Audit | **COMPLETE** | Audit_Report.md |
| Phase 2 — Frontend Inventory | **COMPLETE** | Audit_Report.md |
| Phase 3 — Pipeline Mapping | **COMPLETE** | Audit_Report.md |
| Phase 4 — Financial Unit Consistency | **COMPLETE** | Audit_Report.md |
| Phase 5 — Dead Code & Technical Debt | **COMPLETE** | Audit_Report.md |
| Phase 6 — Runtime Validation | **COMPLETE** | Audit_Report.md |
| Phase 1 — Monetary Architecture | **COMPLETE** | docs/PHASE1_IMPLEMENTATION_REPORT.md |
| Phase 3 — Architecture Consolidation | **COMPLETE** | Architecture_Consolidation_Report.md |
| **Phase 7 — Architecture Corrections** | **IN PROGRESS** | **This document + code changes** |
| **Phase 7B — Backend Capability Audit** | **COMPLETE** | **See below** |

## Backend Capability Audit — Key Findings

A comprehensive backend capability audit was completed on 2026-07-07. Key findings:

### Backend Structure
- **api.py is monolithic**: 1805 lines, 28 routes, 10 helpers, 6 Pydantic models — all in one file
- Modular directories exist as empty scaffolding: `app/`, `audits/`, `db/`, `parsers/`, `reports/`, `routers/`, `utils/` — **zero .py files**
- `core/` directory has DTOs/mappers/domain models but **not wired into api.py**
- The extraction package (`engine/camelot_extractor.py`, `hybrid_extractor.py`) exists but is **not used** by the upload flow (which uses `statement_extractor.py` directly)

### DB Schema
- **5 tables**: `statements`, `transactions`, `members`, `import_mappings`, `reconciliations`
- **NO `loans` table** — loan-related data is detected by the behavior engine (loan_app_pattern_flag detected, 415 loan credit count, ₹2.82L monthly EMI) but not stored as structured records
- **NO `investments` table** — none exist
- **NO `accounts` table** — accounts are computed dynamically from transactions via `balance_engine.get_accounts_list()`

### Features Ready for Immediate Frontend Use
| Feature | API | Data Available |
|---------|-----|----------------|
| Analytics Dashboard | `GET /api/analytics` | Highest month, avg spend, 24-month trend, day-of-week, top 10 merchants, 12 recurring charges, top 10 largest txns |
| Behavior Score Widget | `GET /api/behavior/score` | Health score (64.5), 5 component scores, India-specific risk flags (loan app pattern detected) |
| Behavior Insights Panel | `GET /api/behavior/insights` | List of insights, nudges, top nudge, summary |
| Reconciliation UI | 6 endpoints | Pending matches, confirm/reject workflow |
| Overview Page | `GET /api/overview` | Total spend, category chart, bank chart, behavioral insights |

### Features Requiring New Backend Code
| Feature | What's Needed |
|---------|--------------|
| Loans | New `loans` DB table + API endpoints |
| Investments | New `investments` DB table + API endpoints |
| Net Worth | Aggregate accounts + loans + investments |
| Gmail Ingestion | Gmail API integration, OAuth |
| Persistent Accounts | Replace in-memory store with DB-backed table |

## Completed Audit Phases

### Phase 0 — Repository Discovery
- Repository statistics: 394 source code files (Python: 182, TypeScript: 127, TSX: 55)
- 33 FastAPI endpoints across 5 categories
- 47 UI components (22 shadcn/ui + 25 business)
- Backend uses raw SQLite3 (no ORM) with inline DDL
- No TODO/FIXME hotspots found
- Excluded paths properly configured in .gitignore
- Artifacts: `Audit_Report.md` (Phase 0 + Phase 0 Addendum)

### Phase 1 — Backend Contract Audit
- 33 backend endpoints catalogued in SQLite `audit_endpoints` table
- 8 database tables inventoried in `audit_financial_fields`
- 7 engine modules mapped
- 19 unused backend endpoints identified
- Backend dependency graph constructed
- Artifacts: `Audit_Report.md` (Phase 1)

### Phase 2 — Frontend Inventory
- 6 active routes + 1 orphaned test route
- 25 API client functions in `frontend/lib/api/client.ts`
- 24 hooks (13 legacy + 11 React Query)
- 23 business components
- 8 type definition files
- 22 shadcn/ui components
- Dual hook system identified (legacy + React Query)
- Artifacts: `Audit_Report.md` (Phase 2)

### Phase 3 — Pipeline Mapping
- Complete end-to-end dependency graph constructed
- 8 fully connected pipelines
- 6 partially connected pipelines
- 19 disconnected backend endpoints
- 11 dead API client functions
- 10 dead React Query hooks
- 3 dead legacy hooks
- 2 duplicate hook pairs
- 2 routes without pages (/loans, /investments)
- Artifacts: `Audit_Report.md` (Phase 3)

### Phase 4 — Financial Unit Consistency
- Dual-unit crisis identified (paise + rupees coexist)
- 1 confirmed unit violation (account balance 100x too high - **FIXED**)
- 5 unit violations documented
- Complete financial field lineages traced
- 8 format functions inventoried
- 2 duplicate formatter systems identified (**RESOLVED**)
- Chart unit consistency verified (1 consistent, 1 unknown)
- Artifacts: `Audit_Report.md` (Phase 4)

### Phase 5 — Dead Code & Technical Debt
- ~3,500+ lines of dead code identified
- 19 unused backend endpoints
- 11 dead API client functions
- 10 dead React Query hooks
- 5 dead type files
- 7 unused business components
- 18 technical debt items registered
- 20 safe deletion candidates identified
- 33 refactoring tasks organized by complexity (XS to XL)
- Artifacts: `Audit_Report.md` (Phase 5)

### Phase 6 — Runtime Validation
- Backend syntax error fixed (**B01 - RESOLVED**)
- Runtime validation complete
- 3 BLOCKER findings verified at runtime
- 2 HIGH priority findings verified
- 1 CRITICAL financial unit violation confirmed (**B02 - FIXED**)
- 2 navigation routes confirmed as 404 (**B05 - PENDING**)
- Application health: Backend ✅, Frontend ❌ (with errors)
- Artifacts: `Audit_Report.md` (Phase 6)

## Current Deliverables

1. **Compressed Audit Reference Document** — Generated from 6-phase audit report
2. **Phase 7 Implementation Plan** — Prioritized roadmap for architecture corrections
3. **Backend Capability Matrix** — Feature readiness assessment for Phase 8 planning
4. **Code Changes** — Implementation of fixes for critical blockers and high-priority issues

## Current Rules

1. **Evidence-Based Implementation**: Every change must reference specific audit findings with file path, line number, and evidence
2. **Financial Correctness First**: Fix unit violations and financial calculation issues before cosmetic changes
3. **Dead Code Removal**: Remove confirmed dead code before adding new features
4. **Consolidation Before Expansion**: Consolidate duplicate systems before implementing new functionality
5. **Append-Only Documentation**: Update memory bank files to reflect current state after each change
6. **Verification After Each Change**: Confirm fixes with appropriate tests and runtime validation

## Current Priorities

### MUST FIX BEFORE PHASE 8 (BLOCKERS)
1. **B01** — Backend syntax error (**RESOLVED**)
2. **B02** — Account balance 100x too high (unit violation) (**FIXED**)
3. **B05** — /loans and /investments routes cause 404 — Remove from navigation or create page files
4. **B06** — /projections chain-redirects to 404 — Redirect to /dashboard instead

### HIGH PRIORITY (COMPLETED THIS SESSION)
1. **Fix 1**: Dashboard net_cash_flow unit mismatch — Backend returns `net_cash_flow_paise`, contract test updated, MSW mock fixed
2. **Fix 2**: Accounts management persistence — Added MSW handlers (CRUD) + fixtures
3. **Fix 3**: Removed inline formatINR duplicates — Accounts page now uses canonical import
4. **Fix 4**: Resolved @ts-ignore in cashflow chart — Type-safe dynamic imports for recharts
5. **Fix 5**: Cleaned up unused dashboard components — Deleted 4 orphaned files

### HIGH PRIORITY (PENDING)
- **R6**: In-memory accounts store loses data — **PENDING** (will be addressed last)

### Features Ready for Phase 8
Based on the backend capability audit, the following features are ready for frontend implementation:
1. **Analytics Dashboard** — Full backend exists, needs UI
2. **Behavior Score Widget** — Full backend exists, needs small card UI
3. **Behavior Insights Panel** — Full backend exists, needs list/render component
4. **Reconciliation UI** — Full backend exists (6 endpoints), needs CRUD UI
5. **Overview Page** — Backend works, frontend has mock handlers

### Features Requiring Backend Work
1. **Loans** — Need DB table + API endpoints (behavior engine already detects loan patterns)
2. **Investments** — Need DB table + API endpoints
3. **Net Worth** — Need accounts + loans + investments aggregation
4. **Gmail Ingestion** — Need Gmail API integration
5. **Persistent Accounts** — Need DB-backed accounts table

## Key Findings Summary (UPDATED)

### Critical Blockers (RESOLVED)
1. **B01**: Backend syntax error prevents startup — **FIXED** (removed markdown delimiter)
2. **B02**: Account balance 100x too high — **FIXED** (now uses balance_paise and formatINR)

### Critical Blockers (RESOLVED)
1. **B05**: /loans and /investments routes cause 404 — **FIXED** (removed from navigation)
2. **B06**: /projections chain-redirects to 404 — **FIXED** (redirects to /dashboard)

### High Priority (RESOLVED)
1. **R7**: formatINR/formatRupees ambiguity — **RESOLVED** (formatINR is now canonical)
2. **B03**: useNetWorth in sidebar fails — **FIXED** (removed dead hook, em dash placeholder)
3. **B04**: useDeleteStatement in cards page always errors — **FIXED** (removed dead hook and delete button)
4. **R4**: 11 dead API functions, 10 dead React Query hooks — **FIXED** (removed in Batch 1-2)
5. **R3**: Two parallel hook systems — **RESOLVED** (legacy use-finance-data.ts removed, all hooks now use React Query)
6. **D3**: Consolidate two dashboard pages — **RESOLVED** (root page redirects to /dashboard)

### High Priority (PENDING)
1. **R6**: In-memory accounts store loses data — **PENDING** (will be addressed last)

## Technical Debt (UPDATED)
- **enrich_transaction()** — Deprecated but still used for behavioral insights (non-monetary)
- **compute_is_large()** — Disabled (uses deprecated `amount` field)
- **formatRupees / formatRupeesCompact** — Deprecated, kept for backward compatibility (**PENDING REMOVAL**)
- **Empty modular directories**: `app/`, `audits/`, `db/`, `parsers/`, `reports/`, `routers/`, `utils/` — shell directories with no .py files
- **Unused extraction modules**: `camelot_extractor.py`, `hybrid_extractor.py` — exist on disk, not wired into upload flow
- **Unwired core DTOs/mappers**: `core/dtos/`, `core/mappers/`, `core/domain/` — exist but not imported by api.py

## Audit Artifacts

- **Primary Report**: `Audit_Report.md` (~3,000 lines, 6 phases)
- **Compressed Audit Reference**: Generated from audit report (this phase)
- **Architecture Consolidation Report**: `Architecture_Consolidation_Report.md`
- **Monetary Architecture**: `docs/MONETARY_ARCHITECTURE.md`
- **ADR-001**: `docs/adr/ADR-001-canonical-monetary-units.md`
- **Implementation Report**: `docs/PHASE1_IMPLEMENTATION_REPORT.md`

## API Performance Optimization (COMPLETED)

### Changes Made
1. **Added cachetools dependency** to `backend/requirements.txt`
2. **Implemented in-memory TTL cache** in `backend/src/engines/behavior_engine.py`:
   - `TTLCache(maxsize=10, ttl=300)` - 5-minute cache
   - `invalidate_behavior_cache()` - clears cache on data changes
   - `get_cached_behavior_profile()` / `set_cached_behavior_profile()` - cache accessors
3. **Updated behavior endpoints** to use caching:
   - `/api/behavior/summary`
   - `/api/behavior/score`
   - `/api/behavior/insights`
   - `/api/dashboard/summary`
4. **Added cache invalidation** to data mutation endpoints:
   - `/api/upload` (PDF statement upload)
   - `/api/import/execute` (CSV import)

### Performance Results
- **Before**: 5-10 seconds for behavior endpoints
- **After**: 0.42 seconds (cold cache), ~0.0001s (warm cache)
- **All 36 tests pass**

### Note on Database Indexes
The database indexes for `date_iso`, `type`, and `category` were already present in `db.py` (lines 67, 69, 305).

## Phase 7 Implementation Roadmap

### Immediate (XS, <15 min) — COMPLETE
- ~~Fix B05: Remove /loans and /investments from navigation~~
- ~~Fix B06: Redirect /projections to /dashboard~~
- ~~Fix B03: Remove useNetWorth hook and sidebar display~~
- ~~Fix B04: Remove useDeleteStatement hook and delete button~~
- ~~Remove dead code items~~
- ~~Remove dead type files~~
- ~~Remove dead formatters~~

### Low-Risk Cleanup (S, 15-60 min) — ACTIVE
- ~~Remove 10 dead React Query hooks~~ **DONE**
- ~~Remove 11 dead API client functions~~ **DONE**
- ~~Remove unused hooks~~ **DONE**
- ~~Remove unused API functions~~ **DONE**
- ~~Remove test route~~ **DONE**
- ~~Consolidate formatters~~ **DONE**
- **Fix 1**: Dashboard net_cash_flow unit mismatch **DONE**
- **Fix 2**: Accounts management persistence **DONE** (MSW handlers)
- **Fix 3**: Remove inline formatINR duplicates **DONE**
- **Fix 4**: Resolve @ts-ignore in cashflow chart **DONE**
- **Fix 5**: Clean up unused dashboard components **DONE**
- **Backend Capability Audit** **DONE**

### Medium Refactors (M, 1-4 hours) — READY FOR PHASE 8
- Build Analytics Dashboard UI
- Build Behavior Score Widget
- Build Reconciliation UI
- Build Overview Page (live data)

### High-Risk Refactors (L, 0.5-2 days)
- Replace in-memory accounts store with DB: api.py + db.py
- Remove 19 unused backend endpoints: api.py

### Architecture Improvements (XL, multi-day)
- Loans DB table + API
- Investments DB table + API
- Net Worth computation
- Gmail Ingestion