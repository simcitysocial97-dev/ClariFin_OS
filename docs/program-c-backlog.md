# Program C — Production Backlog

**Status:** ACTIVE
**Date:** 2026-08-07
**Source:** `docs/program-c-gap-inventory.md`

---

## Backlog Item P1-01: Wire ContextPanel to Real Entity Data

**Gap:** #1 — ContextPanel entity data is synthetic/mock
**Priority:** P1 (HIGH)
**Milestone:** M1 — ContextPanel Data Binding

### Affected Feature
Right Context Panel — entity inspection across all workspaces.

### User Value
Users see actual financial data when selecting entities. The ContextPanel becomes a trusted inspector for decision-making instead of a fake preview.

### Architectural Owner
Frontend Lead + Backend Lead (capability contracts already exist)

### Dependencies
- Existing capabilities: `useAccountsCapability`, `useTransactionCapability`, `useLoansCapability`, `useCreditCardsCapability`, `useInvestmentsCapability`, `useReconciliationCapability`
- SelectionRuntime (frozen)
- No new backend endpoints required (all data already exposed via existing capabilities)

### Acceptance Criteria
1. AccountContext displays real account data (balance, institution, transaction count, opened date)
2. TransactionContext displays real transaction data (amount, description, category, merchant, date, confidence)
3. LoanContext displays real loan data (outstanding, EMI, rate, remaining months, lender)
4. CardContext displays real card data (name, last4, usage, limit, due date, utilization)
5. InvestmentContext displays real investment data (name, type, units, NAV, invested, current value, gain)
6. ReconciliationContext displays real reconciliation data (period, matched, unmatched, discrepancy, status)
7. All context components handle loading and error states
8. No hardcoded synthetic data remains in context components
9. TypeScript compiles with 0 errors
10. Existing ContextPanel tests pass

### Verification Strategy
- Local: `npm run test` (frontend unit tests for context components)
- CI: `python runtime/verify.py frontend` via GitHub Actions
- Manual: Select entities in each workspace and verify ContextPanel shows real data

---

## Backlog Item P1-02: Fix Command Center Forecast Data Mapping

**Gap:** #2 — Command Center forecast data wired to cashflow
**Priority:** P1 (HIGH)
**Milestone:** M1 — Command Center Data Correctness

### Affected Feature
Command Center — unified financial dashboard.

### User Value
Users see actual forecast projections in the Command Center instead of duplicated cashflow data.

### Architectural Owner
Frontend Lead

### Dependencies
- `useForecastCapability` (already exists)
- No backend changes required

### Acceptance Criteria
1. Command Center fetches forecast data via `useForecastCapability()`
2. Forecast panel displays net worth projections, cashflow projections, and scenario comparisons
3. No `forecast: cashflowData` mapping remains
4. TypeScript compiles with 0 errors
5. Command Center tests pass

### Verification Strategy
- Local: `npm run test` (frontend tests for command-center)
- CI: `python runtime/verify.py frontend` via GitHub Actions
- Manual: Navigate to Command Center and verify forecast panel shows projection data, not cashflow data

---

## Backlog Item P2-01: Implement Verification Capability (Frontend)

**Gap:** #3 — Verification capability missing from frontend
**Priority:** P2 (MEDIUM)
**Milestone:** M2 — Verification UX

### Affected Feature
Data integrity verification and audit trail visualization.

### User Value
Users can verify ledger integrity, view hash verification results, and audit reconciliation trails from the UI.

### Architectural Owner
Frontend Lead + Backend Lead

### Dependencies
- Backend: `AuditService` and `/api/audit/report` endpoint (already exist)
- Frontend: New `useVerificationCapability` hook
- New verification workspace page

### Acceptance Criteria
1. `useVerificationCapability` hook created in `frontend/lib/capabilities/`
2. Capability exposes: overall status, ledger integrity, hash verification, audit log
3. Verification workspace page created at `frontend/app/verification/`
4. Workspace displays integrity score, verification details, and audit trail
5. Capability follows existing pattern (React Query + mapper)
6. TypeScript compiles with 0 errors
7. Capability contract tests pass

### Verification Strategy
- Local: `npm run test` (frontend capability and workspace tests)
- CI: `python runtime/verify.py frontend` via GitHub Actions
- Manual: Navigate to Verification workspace and confirm data loads from `/api/audit/report`

---

## Backlog Item P2-02: Implement ResizableLayout with Persisted State

**Gap:** #4 — ResizableLayout is a skeleton implementation
**Priority:** P2 (MEDIUM)
**Milestone:** M2 — Shell UX Completeness

### Affected Feature
Panel resizing across the Financial OS Shell.

### User Value
Users can resize the left rail, right context panel, and bottom intelligence shelf to match their workflow preferences.

### Architectural Owner
Frontend Lead

### Dependencies
- shadcn/ui Resizable Panels (already in project dependencies)
- StateRuntime for persisting panel sizes (or localStorage fallback)

### Acceptance Criteria
1. ResizableLayout wraps LeftRail, WorkspaceHost, RightInspector, BottomIntelligenceShelf
2. Left rail resizable between 56px (collapsed) and 180px (expanded)
3. Right context panel resizable between 0px (hidden) and 420px (max)
4. Bottom intelligence shelf resizable between 88px (collapsed) and 240px (expanded)
5. Panel sizes persisted across sessions
6. TypeScript compiles with 0 errors
7. Resizable layout tests pass

### Verification Strategy
- Local: `npm run test` (frontend layout tests)
- CI: `python runtime/verify.py frontend` via GitHub Actions
- Manual: Resize panels, refresh page, verify sizes persist

---

## Backlog Item P2-03: Add Integration Tests for Core Workflows

**Gap:** #7 — Missing integration tests
**Priority:** P2 (MEDIUM)
**Milestone:** M2 — Verification Strategy

### Affected Feature
Cross-service workflow validation.

### User Value
Reduces regression risk for core financial workflows (upload → process → analyze).

### Architectural Owner
Backend Lead

### Dependencies
- Existing test infrastructure (pytest)
- Test database setup

### Acceptance Criteria
1. Integration test for statement upload → extraction → categorization → behaviour profile computation
2. Integration test for reconciliation workflow (create → match → confirm)
3. Integration test for loan simulation (create → schedule → prepayment → foreclosure)
4. All integration tests pass
5. Tests run in CI via existing workflow

### Verification Strategy
- Local: `pytest tests/integration/` (once created)
- CI: Existing backend-verify workflow

---

## Backlog Item P3-01: Separate Global Header from TopCommandBar

**Gap:** #5 — Global Header merged with TopCommandBar
**Priority:** P3 (LOW)
**Milestone:** M3 — Shell Polish

### Affected Feature
Shell region completeness per architecture spec.

### User Value
Clear visual hierarchy with distinct application identity region.

### Architectural Owner**
Frontend Lead

### Dependencies
- Frozen runtimes (NavigationRuntime, WorkspaceRuntime)
- No backend changes

### Acceptance Criteria
1. `GlobalHeader` component extracted (48px height)
2. `TopCommandBar` reduced to command/breadcrumb responsibilities (44px)
3. Both components present in AppShell
4. TypeScript compiles with 0 errors

### Verification Strategy
- Local: `npm run test`
- CI: `python runtime/verify.py frontend`

---

## Backlog Item P3-02: Bind Timeline Scrubber to TimelineRuntime

**Gap:** #6 — Timeline Scrubber positioning without real data binding
**Priority:** P3 (LOW)
**Milestone:** M3 — Timeline Completeness

### Affected Feature**
Timeline temporal navigation.

### User Value
Scrubbing the timeline actually changes the data period displayed in workspaces.

### Architectural Owner**
Frontend Lead

### Dependencies
- TimelineRuntime (frozen)
- Existing workspace capabilities

### Acceptance Criteria
1. Timeline scrubber publishes `TimelineScrubbed` events
2. Workspace capabilities refetch data when timeline period changes
3. Scrubber position reflects actual financial data range
4. TypeScript compiles with 0 errors

### Verification Strategy
- Local: `npm run test`
- CI: `python runtime/verify.py frontend`

---

## Backlog Item P3-03: Enhance Reconciliation and Forecast Workspaces

**Gap:** #8 — Minimal workspace pages
**Priority:** P3 (LOW)
**Milestone:** M3 — Workspace Completeness

### Affected Feature
Reconciliation and Forecast workspace feature completeness.

### User Value
Advanced filtering, bulk actions, export, and scenario comparison in workspaces.

### Architectural Owner**
Frontend Lead + Backend Lead

### Dependencies**
- Existing capabilities
- Existing backend endpoints

### Acceptance Criteria
1. Reconciliation workspace: advanced filters, bulk confirm/reject, export CSV
2. Forecast workspace: scenario comparison UI, horizon selector, export projections
3. TypeScript compiles with 0 errors

### Verification Strategy
- Local: `npm run test`
- CI: `python runtime/verify.py frontend`

---

## Execution Order

```
P1-02 (Command Center fix)      ← Quick win, unblocks correct data display
P1-01 (ContextPanel data)        ← High user impact, uses existing capabilities
P2-01 (Verification capability)  ← New capability, medium complexity
P2-02 (ResizableLayout)          ← UX improvement, medium complexity
P2-03 (Integration tests)        ← Verification strategy, backend-focused
P3-01 (Global Header)            ← Architecture compliance, low complexity
P3-02 (Timeline binding)         ← UX improvement, low complexity
P3-03 (Workspace enhancements)   ← Feature completeness, low complexity
```

---

## Out of Scope

The following are explicitly excluded from Program C:
- Architectural changes (frozen)
- Router restructuring (forbidden by constitution)
- Repository convergence (complete)
- Engineering platform modifications (frozen)
- New backend engines or services not tied to product gaps
- Placeholder workspace creation (constitutionally forbidden)
