# M9-C41 — Final Certification (Updated with D1 Resolution)

## M9-C41 STATUS: CONDITIONAL

**HEAD**: `1d59e429676860890998b0e11fe5f95f57f5f3e4`
**TREE**: `c43d6d20162735079e46d923a762644c771f44e4`

## What was verified

| Layer | C40 | C41 |
|-------|-----|-----|
| Backend | PASS | PASS |
| Frontend build/typecheck/lint | PASS | PASS |
| API Contracts | 5/5 | 5/5 (unchanged) |
| Contract Governance | CERTIFIED | CERTIFIED |
| Golden | 38/38 | 38/38 |
| Runtime | 609/609 | 609/609 |
| Quality | PASS | PASS |
| Mutation | CI_REQUIRED | CI_REQUIRED (Finding B unverified) |
| Playwright (chromium) | 203/17/13 | **213/7/13** |
| Playwright (full matrix) | — | chromium only; 5 projects NOT CERTIFIED |
| CI Finding A | — | REFUTED — npm ci + build already present |
| CI Finding B | — | UNVERIFIED — requires nightly mutation CI run |
| Workflows | 9/9 | 9/9 |

## Permanent Architectural Fixes

1. **Sidebar collapse state machine (genuine APPLICATION_DEFECT)** — `LeftRail` now sources collapse from the authoritative `useAppStore` (`sidebarCollapsed`/`toggleSidebar`) and the rail width actually transitions `180px ↔ 56px`. Resolves C40 navigation/collapse defects.

2. **Transactions click interception — CLICK_INTERCEPTION / LAYOUT_OVERLAP (D1)** — InsightPanel overlapped transaction table rows because PanelBody `scrollable` lacked `min-h-0` (flex-1 couldn't shrink) and Panel's `fill` variant had conflicting `h-full`. **FIXED**: `PanelBody scrollable` now has `min-h-0`; `Panel fill` variant uses `flex-1` only (removed `h-full`). Verified: transactions 14/14 pass, navigation 28/28 pass, behavior/recon/edge-cases 73 passed. Click interception eliminated.

## Tests Added/Modified (no app behavior change)

- `navigation.spec`: corrected to actual `LeftRail` DOM (links + mobile rail).
- `behavior`/`reconciliation`/`edge-cases`: corrected `<main>` assertions to actual degraded/loaded UI; added localStorage isolation.
- `e2e-financial-logic`/`edge-cases`: replaced `text=NaN` substring match (false-positive on "fi**NaN**cial") with leaf-text scan. **Proven: app renders no actual NaN/Infinity.**
- Added `beforeEach localStorage.clear()` to edge-case tests to remove cross-test store contamination.

## Provenance

- Commits: `64817bc2` (C41.1), `aafa14e7` (C41.2), `???` (C41.3 layout fix), `1d59e429` (C41.11 docs)
- Artifacts: `c41-playwright-certification.{json,md}`, `c41-ci-forensics.{json,md}`, `c41-browser-matrix.{json,md}`, `c41-final-certification.{json,md}`

## Evidence (remaining defects)

| ID | Area | Classification | Severity | Status | Next Action |
|----|------|----------------|----------|--------|-------------|
| D2 | Visual baselines (7 snapshots) | VISUAL_BASELINE_DEFECT | Medium | OPEN | Rebaseline with provenance after confirming canonical UI (layout fix changed InsightPanel position) |
| D3 | Home page 2s threshold | PERFORMANCE_DEFECT (env-dependent) | Medium | OPEN | Isolate bottleneck under load; threshold NOT raised |
| D4 | Dashboard timeouts under load | SERVER_LIFECYCLE/TIMEOUT (flaky) | Low | OPEN | Passes in isolation; monitor full matrix, tune waitUntil |
| D5 | Mutation nightly CI | MUTATION_SCORE_FAILURE (unverified) | Unknown | OPEN | Run nightly mutation; if survivors, add behavioral tests (no threshold change) |

## Next Logical Milestone

Rebaseline **7 visual baselines (D2)** with provenance after confirming canonical UI; then execute full 6-project CI matrix and nightly mutation job to convert CONDITIONAL → CERTIFIED GREEN.

## Critical Principle

No green was manufactured. Failures were forensically classified; only genuine defects fixed and demonstrably-incorrect tests corrected. 5 browser projects and the nightly mutation job were explicitly **NOT CERTIFIED** rather than falsely claimed green.