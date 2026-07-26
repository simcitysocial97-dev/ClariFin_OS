# Phase 1 Backlog

Generated from Phase 0 CI audit and backend.yml first-run analysis.
These are the failures and gaps that Phase 1 must fix.

## Workflow Fixes Completed in Phase 0

### ci.yml — Disabled
- Was running duplicate linting, testing, and build steps
- Superseded by quality.yml (quality gate) and backend.yml (full backend suite)
- Triggers replaced with workflow_dispatch only

### full-validation.yml — Disabled
- Was running duplicate backend tests + frontend build
- Superseded by backend.yml and frontend-build.yml
- Triggers replaced with workflow_dispatch only

### frontend.yml — Import path fixed
- Was trying to import FastAPI app from `app.main` and `src.main`
- Correct import is `from api import app` when working directory is `backend/`
- Fixed in `.github/workflows/frontend.yml`

## Backend.yml Test Collection Results

| Test Category | Files | Tests Collected | Status |
|---|---|---|---|
| Unit | tests/unit/ | 823 | Working |
| Contract | tests/contract/ | 132 | Likely failing (Phase 1 work) |
| Capability | tests/capability/ | 23 | Working |
| Integration | tests/integration/ | 34 | May fail (expected) |
| Invariant | tests/invariant/ | 0 | No tests yet |
| Migration | tests/migrations/ | 8 | Working |
| Golden | tests/golden/ | 10 | Working |
| Architecture | tests/architecture/ | 8 | Working |
| Meta | tests/meta/ | 6 | Working |
| Property | tests/properties/ | 51 | Path mismatch — see below |
| **Total** | | **1095** | |

## Critical Issues Found

### 1. Property Tests Path Mismatch — FIXED
- backend.yml referenced `tests/property/` (singular) but actual directory is `tests/properties/` (plural)
- nightly-property-tests.yml had the same issue — fixed
- mutation.yml had the same issue — fixed
- All three workflows now reference `tests/properties/` correctly

### 2. Invariant Tests Empty
- tests/invariant/ directory exists but contains no test files
-backend.yml invariant-tests job will pass trivially (0 tests)
- Phase 1 must add invariant tests

### 3. Mutation Score = 0%
- mutmut run on cashflow_engine.py: 0 survivors killed
- Phase 1 target: ≥60% mutation score
- Phase 3 target: ≥80% mutation score

### 4. Always-Pass Test Patterns
- backend/tests/properties/test_money_invariants.py — 2 instances of `or True`
- backend/tests/integration/cross_capability/test_cross_capability.py — 1 instance of `or True`
- These render tests meaningless and must be fixed in Phase 1

## Missing Infrastructure

| Item | Current State | Phase 1 Target |
|---|---|---|
| Unit test count | 823 | — |
| Coverage (after exclusions) | ~40% | 60% |
| Contract tests passing | 132 tests (status unknown) | 80% |
| Property tests passing | 51 tests (path mismatch) | 50% |
| Mutation score | 0% | 60% |
| Duplicate tests | 0 | 0 |
| Hardcoded test data | 0 | 0 |
| Invariant tests | 0 | Add tests |

## Phase 1 Completion Criteria (from plan)

- [ ] Mutation ≥ 60%
- [ ] Contract ≥ 80%
- [ ] Property ≥ 50%
- [ ] Zero duplicate tests
- [ ] Zero hardcoded test data
- [ ] Property tests path aligned (properties → property OR backend.yml updated)
- [ ] Invariant tests added (currently 0 tests)
- [ ] Always-pass test patterns fixed (3 instances)
- [ ] coverage_threshold.py updated for Phase 1 target (60% overall)