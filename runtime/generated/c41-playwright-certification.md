# M9-C41 — Playwright Defect Remediation Certification (Updated with D1+D2 Resolution)

**Status: CONDITIONAL** (chromium reproduced; full green not achieved)

- **HEAD**: `1d59e429676860890998b0e11fe5f95f57f5f3e4`
- **TREE**: `c43d6d20162735079e46d923a762644c771f44e4`
- **Command reproduced**: `python runtime/verify.py playwright` (chromium first, then all projects)

## C40 → C41 Chromium Delta

| Metric | C40 | C41 (after fixes) |
|--------|-----|------------------|
| Pass   | 203 | **213** |
| Fail   | 17  | **7** |
| Skip   | 13  | 13 |

## Failure Ledger (remaining 7)

| Test | Classification | Root Cause | Resolution |
|------|----------------|-----------|------------|
| visual: 7 snapshots | VISUAL_BASELINE_DEFECT | Layout fix changed InsightPanel position; baselines stale | **RESOLVED (C41.4/5) — 24/24 pass** |
| performance: home page | PERFORMANCE_DEFECT (env) | Passes in isolation <2s; load-dependent | Threshold NOT raised |
| dashboard: quick stats | SERVER/TIMEOUT (flaky) | Passes in isolation; full-parallel contention | Monitor |
| dashboard: nav sidebar | SERVER/TIMEOUT (flaky) | Passes in isolation | Monitor |

## Resolved in C41 (genuine)

| Fix | Classification | Evidence |
|-----|----------------|----------|
| Sidebar collapse state machine | APPLICATION_DEFECT | LeftRail wired to `useAppStore`; width 180px↔56px |
| Navigation selectors | SELECTOR_DEFECT | Corrected to actual LeftRail DOM |
| API-unavailable `<main>` assertions | TEST_DEFECT | Pages render Alert/empty states |
| Edge-case `<main>` + store leak | TEST/FIXTURE_DEFECT | Added `localStorage.clear()` beforeEach |
| NaN false-positive ("fi**NaN**cial") | TEST_DEFECT (false positive) | Leaf-text scan; proven no NaN/Infinity |
| Edge-case fixture isolation | FIXTURE_DEFECT | `localStorage.clear()` beforeEach |
| **Transactions click interception (D1)** | **CLICK_INTERCEPTION / LAYOUT_OVERLAP** | **PanelBody min-h-0 + Panel fill fix** |
| **Visual baselines (D2)** | **VISUAL_BASELINE_DEFECT** | **7 snapshots rebaselined with provenance (24/24 pass)** |

## C41.3 — D1 Click Interception Resolution (Genuine)

**Root cause**: InsightPanel (flex sibling after scrollable PanelBody) visually overlapped table rows. PanelBody `scrollable` had `flex-1 overflow-auto` but **lacked `min-h-0`**, so flex-1 couldn't shrink it. Panel's `fill` variant had conflicting `h-full`. InsightPanel rendered at y=444, covering row at y=484.

**Fix** (`frontend/components/primitives/panel/panel.tsx`):
- Panel fill variant: `flex-1 h-full` → `flex-1` (removed conflicting `h-full`)
- PanelBody scrollable: `flex-1` → `flex-1 min-h-0` (allows shrink below content size)

**Verification**:
- Transactions: 14/14 pass (was 2 timeout failures)
- Navigation: 28/28 pass
- Behavior/Reconciliation/Edge-cases: 73 passed, 2 skipped
- CSS integrity: 19 passed, 3 skipped
- Click interception **eliminated** — elementFromPoint at row center now resolves to `<tr>`, not InsightPanel

**Note**: `onRowClick={() => {}}` is no-op (no detail navigation wired). Row click now works; feature contract for row→detail must be confirmed separately.

## C41.4/5 — D2 Visual Baseline Resolution (Genuine)

**Root cause**: Panel/PanelBody layout fix changed InsightPanel position → 7 stale baselines.

**Fix**: Provenance-bound rebaseline of 7 snapshots:
- cards-page, behaviour-page, reconciliation-page, import-page, transactions-page
- transactions-mobile, categories-mobile

**Verification**: All 24 visual regression tests pass (24/24).

## Status

**CONDITIONAL** — 10 of 17 C40 failures resolved with evidence; 7 remain (1 performance env-dependent, 2 dashboard flaky timeouts). No green manufactured.