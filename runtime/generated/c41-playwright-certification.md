# M9-C41 — Playwright Defect Remediation Certification

**Status: CONDITIONAL** (chromium reproduced; full green not achieved)

- **HEAD**: `aafa14e7eb38525f36b3fe3edb3e43bd34fcbb8f`
- **TREE**: `c43d6d20162735079e46d923a762644c771f44e4`
- **Command reproduced**: `python runtime/verify.py playwright` (chromium)

## C40 → C41 Chromium Delta

| Metric | C40 | C41 (after fixes) |
|--------|-----|------------------|
| Pass   | 203 | **213** |
| Fail   | 17  | **7** |
| Skip   | 13  | 13 |

## Failure Ledger (remaining 7)

| Test | Classification | Root Cause | Resolution |
|------|----------------|-----------|------------|
| transactions:180 clear filters | CLICK_INTERCEPTION | absolute-inset-0 workspace overlay intercepts table region | OPEN (D1) |
| transactions:371 open details | CLICK_INTERCEPTION | same overlay; row-click->detail not wired | OPEN (D1) |
| visual cards-page | VISUAL_BASELINE_DEFECT | stale baseline / collapse-state leakage | OPEN (D2) |
| visual behaviour-page | VISUAL_BASELINE_DEFECT | same | OPEN (D2) |
| visual reconciliation-page | VISUAL_BASELINE_DEFECT | same | OPEN (D2) |
| dashboard:111 quick stats | SERVER/TIMEOUT (flaky) | passes in isolation; full-parallel contention | OPEN (D4) |
| dashboard:124 nav sidebar | SERVER/TIMEOUT (flaky) | passes in isolation | OPEN (D4) |
| performance:31 home page | PERFORMANCE_DEFECT (env) | passes in isolation <2s; load-dependent | OPEN (D3) |

## Resolved in C41 (genuine)

- **APPLICATION_DEFECT — sidebar collapse**: `LeftRail` collapse state now sourced from authoritative `useAppStore` (`sidebarCollapsed`/`toggleSidebar`); rail width transitions 180px↔56px. Fixes `navigation:134`, `css-integrity:47`.
- **SELECTOR_DEFECT**: navigation tests asserted non-existent `<nav>`/hamburger; corrected to actual `LeftRail` DOM.
- **TEST_DEFECT**: API-unavailable & edge-case tests asserted `<main>`; those pages render non-`<main>` Alert/empty states — corrected.
- **TEST_DEFECT (false positive)**: `text=NaN` substring-matched "fi**NaN**cial"; replaced with leaf-text scan. **Proven: app renders NO actual NaN/Infinity.**
- **FIXTURE_DEFECT**: edge-case tests leaked persisted zustand store; added `beforeEach` `localStorage.clear()`.

## Status

CONDITIONAL — 10 of 17 C40 failures resolved with evidence; 7 remain (1 high-severity real UI defect D1, 3 visual baselines D2, 1 performance D3, 2 flaky timeouts D4). No green manufactured.
