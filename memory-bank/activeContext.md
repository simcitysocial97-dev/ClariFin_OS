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
3. **Code Changes** — Implementation of fixes for critical blockers and high-priority issues

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

### HIGH PRIORITY
1. **B03** — useNetWorth in sidebar fails — Remove dead hook and sidebar display
2. **B04** — useDeleteStatement in cards page always errors — Remove dead hook and delete button
3. **H01-H15** — Remove 15 dead API client functions and hooks
4. **R3** — Two parallel hook systems (legacy + React Query) — Consolidate to React Query
5. **R4** — 11 dead API functions, 10 dead React Query hooks — Remove dead code
6. **R6** — In-memory accounts store loses data — Add database persistence
7. **D1** — Consolidate duplicate overview hooks — Remove legacy useOverview
8. **D3** — Consolidate two dashboard pages — Decide which to keep

### MEDIUM PRIORITY
1. **M01-M13** — Remove 13 dead code items (hooks, utilities, type files, test routes)
2. **TD3** — Adopt canonical unit convention (paise or rupees) — Complete migration
3. **TD17** — formatINR vs formatRupees ambiguity — Remove deprecated formatters

## Key Findings Summary (UPDATED)

### Critical Blockers (RESOLVED)
1. **B01**: Backend syntax error prevents startup — **FIXED** (removed markdown delimiter)
2. **B02**: Account balance 100x too high — **FIXED** (now uses balance_paise and formatINR)

### Critical Blockers (PENDING)
1. **B05**: /loans and /investments routes cause 404 — **PENDING**
2. **B06**: /projections chain-redirects to 404 — **PENDING**

### High Priority (RESOLVED)
1. **R7**: formatINR/formatRupees ambiguity — **RESOLVED** (formatINR is now canonical)

### High Priority (PENDING)
1. **B03**: useNetWorth in sidebar fails — **PENDING**
2. **B04**: useDeleteStatement in cards page always errors — **PENDING**
3. **R3**: Two parallel hook systems — **PENDING**
4. **R4**: 11 dead API functions, 10 dead React Query hooks — **PENDING**
5. **R6**: In-memory accounts store loses data — **PENDING**

### Technical Debt (UPDATED)
- **enrich_transaction()** — Deprecated but still used for behavioral insights (non-monetary)
- **compute_is_large()** — Disabled (uses deprecated `amount` field)
- **formatRupees / formatRupeesCompact** — Deprecated, kept for backward compatibility (**PENDING REMOVAL**)

### Unit Consistency Fixes (COMPLETED)
- **bank-wise-chart.tsx** — Fixed to use `amount_paise` instead of `amount` for chart data
  - Interface: `amount: number` → `amount_paise: number`
  - dataKey: `"amount"` → `"amount_paise"`
  - tickFormatter: `value / 1000` → `value / 100 / 1000`
  - Tooltip formatter: Added `/ 100` conversion
- **transactions/page.tsx** — Fixed 3 monetary field accesses
  - Line 84: `t.amount >= minAmount` → `(t.amount_paise || 0) / 100 >= minAmount`
  - Line 129: `t.amount` → `(t.amount_paise / 100).toFixed(2)` (CSV export)
  - Line 462: `transaction.amount.toLocaleString('en-IN')` → `formatINR(transaction.amount_paise)`
- **upload-zone.tsx** — Fixed parser output mapping
  - `amount: t.amount` → `amount_paise: t.amount_paise`

## Audit Artifacts

- **Primary Report**: `Audit_Report.md` (~3,000 lines, 6 phases)
- **Compressed Audit Reference**: Generated from audit report (this phase)
- **Architecture Consolidation Report**: `Architecture_Consolidation_Report.md`
- **Monetary Architecture**: `docs/MONETARY_ARCHITECTURE.md`
- **ADR-001**: `docs/adr/ADR-001-canonical-monetary-units.md`
- **Implementation Report**: `docs/PHASE1_IMPLEMENTATION_REPORT.md`

## Phase 7 Implementation Roadmap

### Immediate (XS, <15 min)
1. **Fix B05**: Remove /loans and /investments from navigation
2. **Fix B06**: Redirect /projections to /dashboard
3. **Fix B03**: Remove useNetWorth hook and sidebar display
4. **Fix B04**: Remove useDeleteStatement hook and delete button
5. **Remove dead code**: due-date-logic.ts, query-client.ts, use-async-mutation.ts
6. **Remove dead type files**: investment.ts, loan.ts, recurring.ts, v2.ts
7. **Remove dead formatters**: formatRupeesCompact, truncateText

### Low-Risk Cleanup (S, 15-60 min)
8. **Remove 10 dead React Query hooks**: use-query-finance.ts
9. **Remove 11 dead API client functions**: client.ts
10. **Remove unused hooks**: useAnalytics, useCategories, useMembers
11. **Remove unused API functions**: fetchCategories, fetchAnalytics, fetchMembers
12. **Remove test route**: /test/metadata
13. **Consolidate formatters**: Remove lib/format.ts, use lib/utils/format.ts

### Medium Refactors (M, 1-4 hours)
14. **Consolidate duplicate overview hooks**: Remove legacy useOverview
15. **Migrate legacy hooks to React Query**: 3 hooks
16. **Fix accounts page**: Use API client instead of direct fetch
17. **Consolidate category color maps**: 2 files
18. **Remove deprecated _rupees fields**: Backend DTOs

### High-Risk Refactors (L, 0.5-2 days)
19. **Consolidate two dashboard pages**: Decide which to keep
20. **Replace in-memory accounts store with DB**: api.py + db.py
21. **Remove 19 unused backend endpoints**: api.py

### Architecture Improvements (XL, multi-day)
22. **Full migration from legacy hooks to React Query**: All consumers
23. **Type-safe financial units**: Branded types for paise/rupees
24. **Add backend unit tests**: Financial calculations
25. **Implement cross-account reconciliation**: New feature