# M9-C41 — Final Certification

## M9-C41 STATUS: CONDITIONAL

**HEAD**: `aafa14e7eb38525f36b3fe3edb3e43bd34fcbb8f`
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
| Workflows | 9/9 | 9/9 |

## Permanent Architectural Fixes

1. **Sidebar collapse state machine (genuine APPLICATION_DEFECT)** — `LeftRail` now sources collapse from the authoritative `useAppStore` (`sidebarCollapsed`/`toggleSidebar`) and the rail width actually transitions 180px↔56px. Resolves C40 navigation/collapse defects.

## Tests Added/Modified (no app behavior change)

- navigation.spec: corrected to actual `LeftRail` DOM (links + mobile rail).
- behaviour/reconciliation/edge-cases: corrected `<main>` assertions to actual degraded/loaded UI; added localStorage isolation.
- e2e-financial-logic/edge-cases: replaced `text=NaN` substring match (false-positive on "fi**NaN**cial") with leaf-text scan. **Proven: app renders no actual NaN.**

## Provenance

- Commits: `64817bc2` (C41.1 collapse+nav), `aafa14e7` (C41.2 assertion corrections).
- Artifacts: `c41-playwright-certification.{json,md}`, `c41-ci-forensics.{json,md}`, `c41-browser-matrix.{json,md}`, `c41-final-certification.{json,md}`.

## Evidence (remaining defects)

- **D1 (high)**: transactions click interception — `absolute inset-0` workspace overlay intercepts table rows. OPEN.
- **D2 (med)**: visual baselines (cards/behaviour/reconciliation) — stale/leaked-state; needs provenance-bound rebaseline. OPEN.
- **D3 (med)**: home-page 2s threshold — passes in isolation; load-dependent; threshold NOT raised. OPEN.
- **D4 (low)**: dashboard timeouts — pass in isolation; full-parallel contention. OPEN.
- **D5**: mutation nightly — Finding B unverified. OPEN.

## Next Logical Milestone

Resolve **D1** (transactions click-interception overlay) — the only remaining genuine high-severity UI defect blocking full browser certification. Then execute the full 6-project matrix in CI and the nightly mutation job to convert CONDITIONAL → CERTIFIED GREEN.

## Critical Principle

No green was manufactured. Failures were forensically classified; only genuine defects fixed and demonstrably-incorrect tests corrected. 5 browser projects and the nightly mutation job were explicitly **NOT CERTIFIED** rather than falsely claimed green.
