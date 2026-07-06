# Audit Context

## Audit Objective

Establish a verified understanding of the complete ClariFin_OS data pipeline. Identify architectural inconsistencies, dead code, unit mismatches, and pipeline gaps. Produce a prioritized implementation roadmap for architecture corrections and technical debt resolution.

---

## Audit Constraints

The audit is **READ ONLY** during documentation phases, but **implementation is now active** for Phase 7 (Architecture Corrections).

**During Phase 7:**
- ✅ Modify application code to fix critical blockers and high-priority issues
- ✅ Remove confirmed dead code
- ✅ Consolidate duplicate systems
- ✅ Resolve unit violations
- ✅ Update tests to reflect changes
- ✅ Refactor for maintainability

**Do not:**
- Add new features
- Expand scope beyond audit findings
- Implement unvalidated changes

---

## Evidence Standard

Every finding **must** include:

| Field | Required | Description |
|-------|----------|-------------|
| File path | ✅ | Absolute or relative to project root |
| Function name | ✅ | The function/method where the issue exists |
| Line number | ✅ | Exact line number(s) |
| Why it is incorrect | ✅ | Explanation of the problem |
| Downstream impact | ✅ | What breaks or is affected downstream |
| Confidence | ✅ | HIGH / MEDIUM / LOW |
| Audit ID | ✅ | Reference to compressed audit finding (e.g., B01, H03) |

This prevents vague statements like *"Looks duplicated"*.

Instead:

```
frontend/lib/api/client.ts
function fetchNetWorth()
Line 42
Calls GET /api/networth (no backend endpoint)
Downstream: useNetWorth hook fails with 404
Confidence: HIGH
Audit ID: B07
```

---

## Current Assumptions

These assumptions are frozen for the duration of Phase 7:

1. **Backend is source of truth** — All financial calculations originate from the FastAPI/SQLite backend
2. **Audit findings are authoritative** — The compressed audit reference document supersedes any prior documentation
3. **Financial correctness first** — Fix unit violations and financial calculation issues before cosmetic changes
4. **Dead code removal is safe** — Items marked as "SAFE TO DELETE" in the audit have zero consumers
5. **Implementation follows audit** — Every change must reference specific audit findings with evidence

---

## Audit Progress State

| Phase | Status | Layer | Current Target |
|-------|--------|-------|----------------|
| Phase 0 — Repository Discovery | **COMPLETE** | — | — |
| Phase 0 Addendum | **COMPLETE** | — | — |
| Phase 1 — Backend Contract Audit | **COMPLETE** | — | — |
| Phase 2 — Frontend Inventory | **COMPLETE** | — | — |
| Phase 3 — Pipeline Mapping | **COMPLETE** | — | — |
| Phase 4 — Financial Unit Consistency | **COMPLETE** | — | — |
| Phase 5 — Dead Code & Technical Debt | **COMPLETE** | — | — |
| Phase 6 — Runtime Validation | **COMPLETE** | — | — |
| **Phase 7 — Architecture Corrections** | **IN PROGRESS** | Immediate (XS) | Fix critical blockers and remove dead code |

---

## Compressed Audit Reference

The **Compressed Audit Reference Document** has been generated from the 6-phase audit report. This document is the authoritative source for all findings and serves as the implementation roadmap for Phase 7.

### Key Sections

1. **HEADER BLOCK**: Project metadata, audit date, pipeline health, phase 6 clearance status
2. **BLOCKERS TABLE**: 12 BLOCKER findings (B01-B12) — **MUST FIX BEFORE PHASE 8**
3. **HIGH PRIORITY TABLE**: 15 HIGH priority findings (H01-H15)
4. **MEDIUM PRIORITY TABLE**: 13 MEDIUM priority findings (M01-M13)
5. **API CONTRACT MAP**: 22 backend endpoints, 21 frontend→backend matches
6. **HOOK DEPENDENCY MAP**: 12 hooks, 2 dead, 10 active
7. **UNIT TRACE TABLE**: 7 financial values, 1 DOUBLE-SCALED, 1 UNKNOWN
8. **ROUTE STATUS TABLE**: 8 routes, 2 404s, 1 orphaned
9. **DEAD CODE REGISTER**: 15 dead hooks, 14 dead API functions, 2 dead routes, 4 dead type files
10. **TYPE SAFETY GAPS**: 4 type safety issues, 2 HIGH risk
11. **ENV VARIABLE STATUS**: 1 variable, status OK
12. **HARDCODED VALUES REGISTER**: 2 hardcoded values, LOW impact
13. **PHASE 6 PREREQUISITE CHECKLIST**: 4 MUST FIX, 4 RECOMMENDED, 13 ACCEPTABLE

---

## Critical Findings Summary

### BLOCKERS (MUST FIX BEFORE PHASE 8)
| ID  | Issue | Status | Evidence |
|-----|-------|--------|----------|
| B01 | Backend syntax error prevents startup | **FIXED** | backend/src/api.py:193 — markdown delimiter |
| B02 | Account balance 100x too high | **FIXED** | frontend/app/accounts/page.tsx:88 — unit violation |
| B03 | useNetWorth in sidebar fails | **PENDING** | sidebar.tsx — dead endpoint |
| B04 | useDeleteStatement in cards page always errors | **PENDING** | cards/page.tsx — removed endpoint |
| B05 | /loans and /investments routes cause 404 | **PENDING** | navigation.ts — missing pages |
| B06 | /projections chain-redirects to 404 | **PENDING** | navigation.ts — broken redirect |

### HIGH PRIORITY
| ID  | Issue | Status | Evidence |
|-----|-------|--------|----------|
| H01-H15 | 15 dead API client functions and hooks | **PENDING** | client.ts, use-query-finance.ts — dead endpoints |
| R3 | Two parallel hook systems | **PENDING** | use-finance-data.ts, use-query-finance.ts — duplicate hooks |
| R4 | 11 dead API functions, 10 dead React Query hooks | **PENDING** | client.ts, use-query-finance.ts — dead code |
| R6 | In-memory accounts store loses data | **PENDING** | api.py — no database persistence |
| D1 | Duplicate overview hooks | **PENDING** | useOverview vs useOverviewQuery — duplicate fetching |
| D3 | Two dashboard pages with overlap | **PENDING** | / vs /dashboard — duplicate rendering |

---

## Implementation Roadmap

### Immediate (XS, <15 min)
1. **Fix B05**: Remove /loans and /investments from navigation (navigation.ts)
2. **Fix B06**: Redirect /projections to /dashboard (navigation.ts)
3. **Fix B03**: Remove useNetWorth hook and sidebar display (sidebar.tsx, use-finance-data.ts)
4. **Fix B04**: Remove useDeleteStatement hook and delete button (cards/page.tsx, use-finance-data.ts)
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

---

## Verification Protocol

After each change, verify:

1. **Runtime Validation**: Confirm the application starts and core functionality works
2. **Console Errors**: Check for new errors or warnings
3. **Network Traffic**: Verify no unexpected 404s or failed requests
4. **Financial Correctness**: Confirm monetary values display correctly
5. **Navigation**: Ensure all routes work as expected
6. **Tests**: Run relevant Playwright and pytest tests

---

## Deliverables

| Phase | Deliverable | Status |
|-------|-------------|--------|
| Phase 0 | Audit_Report.md — Phase 0 | ✅ Complete |
| Phase 0 Addendum | Audit_Report.md — Phase 0 Addendum | ✅ Complete |
| Phase 1 | Audit_Report.md — Phase 1 | ✅ Complete |
| Phase 2 | Audit_Report.md — Phase 2 | ✅ Complete |
| Phase 3 | Audit_Report.md — Phase 3 | ✅ Complete |
| Phase 4 | Audit_Report.md — Phase 4 | ✅ Complete |
| Phase 5 | Audit_Report.md — Phase 5 | ✅ Complete |
| Phase 6 | Audit_Report.md — Phase 6 | ✅ Complete |
| Phase 7 | **Compressed Audit Reference Document** | ✅ Complete |
| Phase 7 | **Code Changes** | ⏳ In Progress |
| Phase 7 | **Updated Memory Bank** | ⏳ In Progress |

---

## Audit_Report.md Status

- **File**: `Audit_Report.md` (project root)
- **Policy**: Append-only. Never rewrite previous phases.
- **Current Sections**: Phase 0 through Phase 6 (complete)
- **Next Section**: Phase 7 — Architecture Corrections (to be appended after completion)

---

## Next Steps

1. **Execute Immediate Tasks (XS)**: Fix critical blockers and remove dead code
2. **Verify Each Change**: Confirm fixes with runtime validation and tests
3. **Update Memory Bank**: Reflect current state after each change
4. **Proceed to Low-Risk Cleanup (S)**: Remove remaining dead code and consolidate formatters
5. **Tackle Medium Refactors (M)**: Consolidate hooks, migrate to React Query, fix accounts page
6. **Append Phase 7 to Audit_Report.md**: Document all changes and verification results