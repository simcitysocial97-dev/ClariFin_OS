# Program C — Product Gap Inventory

**Status:** DRAFT
**Date:** 2026-08-07
**Scope:** User-facing functionality gaps only. Architecture gaps are excluded (frozen).

---

## Methodology

Gaps were identified by:
1. Auditing workspace pages against the Financial OS Shell Architecture spec
2. Comparing implemented capabilities vs. the 12-capability framework
3. Inspecting ContextPanel, Command Center, and shell region implementations
4. Reviewing known technical debt from `docs/EXECUTION_STATE.md`
5. Analyzing CAPABILITY_COVERAGE.md for uncovered capabilities

---

## Gap 1: ContextPanel Entity Data is Synthetic/Mock

**Severity:** HIGH
**Category:** Reconciliation UX / Explainability
**Affected Feature:** Right Context Panel entity inspection

### Current State
All entity context components (`AccountContext`, `TransactionContext`, `LoanContext`, `CardContext`, `InvestmentContext`, `ReconciliationContext`) generate hardcoded synthetic data:

```typescript
// Example from AccountContext
const context = useMemo(() => ({
  id: String(entity.id),
  name: `Account ${String(entity.id).slice(0, 8)}`,
  balance_paise: 2500000,           // hardcoded
  institution: 'HDFC Bank',         // hardcoded
  transactions_count: 142,          // hardcoded
}), [entity]);
```

### Expected State
ContextPanel should display real financial data fetched via the canonical capability pipeline:
- Account balance, institution, transaction count from `AccountService`
- Transaction amount, description, category, merchant from `TransactionService`
- Loan outstanding, EMI, rate from `LoanService`
- Card usage, limit, due date from `CreditCardService`
- Investment NAV, units, gains from `InvestmentService`
- Reconciliation matched/unmatched counts from `ReconciliationService`

### User Impact
Users inspecting entities see fake data that does not match their actual financial state. This breaks trust in the inspector and makes the ContextPanel useless for real decision-making.

---

## Gap 2: Command Center Forecast Data Wired to Cashflow

**Severity:** HIGH
**Category:** Forecasting / Command Center Behavior
**Affected Feature:** Command Center unified view

### Current State
In `frontend/app/command-center/page.tsx`, the forecast viewModel is incorrectly mapped to cashflow data:

```typescript
const viewModels: Record<string, unknown> = {
  // ...
  forecast: cashflowData,  // BUG: should be forecastData
};
```

This means the Command Center displays cashflow charts where forecast projections should appear.

### Expected State
Command Center should fetch and display actual forecast data via `useForecastCapability()`.

### User Impact
Users see incorrect data in the Command Center forecast panel. The forecasting workspace exists and works, but the unified command center shows the wrong dataset.

---

## Gap 3: Verification Capability Missing from Frontend

**Severity:** MEDIUM
**Category:** Incomplete Financial Workflows
**Affected Feature:** Data integrity verification

### Current State
- Backend has `AuditService` and `/api/audit/report` endpoint
- Frontend has NO `useVerificationCapability` hook
- Frontend has NO verification workspace page
- CAPABILITY_COVERAGE.md shows Verification capability with 2/7 coverage categories (FAIL for Unit, Property, Regression, Invariant, Golden)

### Expected State
A `VerificationCapability` should expose audit/verification data to the UI:
- Ledger integrity status
- Hash verification results
- Reconciliation audit trail access
- Data integrity scoring

### User Impact
Users cannot verify the integrity of their financial data from the UI. The audit/verification feature exists on the backend but is inaccessible to users.

---

## Gap 4: ResizableLayout is a Skeleton Implementation

**Severity:** MEDIUM
**Category:** Missing UI Capabilities
**Affected Feature:** Panel resizing

### Current State
`ResizableLayout` is a passthrough `<div>` with no actual resizing logic:

```typescript
export function ResizableLayout({ children, className }: ResizableLayoutProps) {
  return (
    <div className={cn('h-full w-full', className)}>
      {children}
    </div>
  );
}
```

The spec requires shadcn/ui Resizable Panels integration for:
- Left rail collapse/expand (180px / 56px)
- Right context panel resize (280px–420px)
- Bottom intelligence shelf expand (88px / 240px)

### Expected State
ResizableLayout should implement actual panel resizing with persisted state.

### User Impact
Users cannot resize panels. The shell is fixed-layout only, reducing usability on different screen sizes.

---

## Gap 5: Global Header Merged with TopCommandBar

**Severity:** LOW
**Category:** Incomplete UI Capabilities
**Affected Feature:** Shell region completeness

### Current State
The architecture specifies 8 distinct shell regions including a separate Global Header (48px) and Command HUD (44px). Currently, `TopCommandBar` (44px) serves as both the command HUD and the global header. There is no separate Global Header region.

### Expected State
A dedicated `GlobalHeader` component (48px) should exist alongside `TopCommandBar` (44px), with:
- Application identity (logo, app name)
- Active household name
- Active workspace title
- Global status indicators (sync state, connection state)

### User Impact
Minor UX inconsistency. The shell is functional but does not match the specified architecture.

---

## Gap 6: Timeline Scrubber Positioning Without Real Data Binding

**Severity:** LOW
**Category:** Timeline Experience
**Affected Feature:** Timeline scrubber interactivity

### Current State
The Timeline Scrubber uses localStorage-like positioning without real data binding to the financial timeline. Scrubber position does not drive actual period changes in workspace data.

### Expected State
Timeline scrubber should be bound to `TimelineRuntime` so that scrubbing updates the active period and triggers capability refetches.

### User Impact
Users can drag the scrubber but it does not change the displayed financial data period.

---

## Gap 7: Missing Integration Tests

**Severity:** MEDIUM
**Category:** Verification Strategy
**Affected Feature:** End-to-end workflow validation

### Current State
STEP-007 from the migration DAG was deferred: "add integration tests". No integration test suite exists for cross-service workflows (e.g., upload → extract → categorize → compute profile → update dashboard).

### Expected State
Integration tests validating full financial workflows from API endpoint to database.

### User Impact
Regression risk for cross-service workflows. Changes to one service may break workflows without detection until manual testing.

---

## Gap 8: Workspace Pages with Minimal Implementation

**Severity:** LOW
**Category:** Incomplete Workspaces
**Affected Feature:** Reconciliation and Forecast workspaces

### Current State
Some workspace pages are thin wrappers:
- `reconciliation/page.tsx` — 5 lines, delegates to `workspace-page.tsx`
- `forecast/page.tsx` — 5 lines, delegates to `workspace-page.tsx`

The underlying `workspace-page.tsx` files are functional but basic. They lack:
- Advanced filtering
- Bulk actions
- Export functionality
- Scenario comparison UI

### Expected State
Workspace pages should have full feature parity with the architecture spec.

### User Impact
Users can use the workspaces but miss advanced features.

---

## Summary

| # | Gap | Severity | Category | Blocking |
|---|-----|----------|----------|----------|
| 1 | ContextPanel mock data | HIGH | Reconciliation UX | Yes |
| 2 | Command Center forecast bug | HIGH | Forecasting | Yes |
| 3 | Verification capability missing | MEDIUM | Incomplete workflows | Partial |
| 4 | ResizableLayout skeleton | MEDIUM | Missing UI capabilities | No |
| 5 | Global Header merged | LOW | Incomplete UI | No |
| 6 | Timeline Scrubber no binding | LOW | Timeline Experience | No |
| 7 | Missing integration tests | MEDIUM | Verification Strategy | No |
| 8 | Minimal workspace pages | LOW | Incomplete workspaces | No |

**Total HIGH: 2**
**Total MEDIUM: 3**
**Total LOW: 3**
