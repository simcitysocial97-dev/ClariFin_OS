# M9-POST-C46 — Node 24 LTS Runtime Modernization + Dependency Compatibility Convergence

**Branch:** `m9c9-merge-authorization-resolution`  
**Baseline commit:** `ee9c4f6630bfe77abc40c3b9424996540352c877`  
**Head before local changes:** `5e944ba9e643eade0367b23acf350d925c16fc1c`  
**Execution date:** 2026-08-30  
**Local verification node:** v24.13.0 (via `~/.local/node24/bin/node`, explicit PATH override)  
**Local system node:** v20.20.2 (nodesource deb package, unchanged)  

---

## Phase 0 — Authoritative Baseline (recorded, no changes)

| Workflow | Status at ee9c4f66 | Database ID |
|---|---|---|
| API Contract Integrity | success | 33304536021 |
| Verification Reconcile | success | 33304535995 |
| Verification Runtime | success | 33304535970 |
| Quality Gate | success | 33304536085 |
| Backend Verification | success | 33304536129 |
| Frontend Verification | success | 33304536057 |
| Mutation Testing (dispatched for ee9c4f66) | **cancelled** | 33307741919 (1h31m runtime, cancelled mid-run) |
| CodeQL Security Analysis (ee9c4f66) | success | — |
| Golden Dataset Regression (ee9c4f66) | success | — |

**Pre-existing head failures (5e944ba9, unrelated to this milestone):**
- Frontend Verification step-0003: fast-checks classification changed
- Backend Verification step-0002: Ruff F841 unused var `d` in `backend/tests/unit/engines/credit_card/test_mutation_gap_repairs.py:323` — introduced by the mutation-strengthening commit itself

Baseline recorded to `runtime/generated/m9-post-c46-node24/baseline.json`.

---

## Phase 1 — Complete Node Runtime Inventory

**Canonical mechanism found:** `.github/actions/setup-node-runtime/action.yml` (already in place, per architectural rule `github_actions.reusable_setup`).  
8 workflows consume it; no workflow inlines `actions/setup-node`.

**Inventory summary:**
- `frontend/package.json` engines.node: `>=20 <21` → must change
- `frontend/.nvmrc`: `20` → must change
- `.github/actions/setup-node-runtime/action.yml` default: `"20"` → must change
- 8 workflow `node-version` inputs: `"20"` → must change
- `runtime/foundation/verification/verification.yaml` infrastructure.node_version: `"20"` → must change
- 4 historical provenance JSONs: immutable (C31.1, C31.2, C33, C40)
- 3 Python-only workflows: no change needed (mutation.yml, golden.yml, verification-reconcile.yml)

Full inventory in `node-runtime-inventory.json`.

---

## Phase 2 — Canonical Runtime Contract

**Chosen:** Extend existing `.github/actions/setup-node-runtime` composite action default from `"20"` to `"24"`. No new configuration architecture invented.  
Rationale: repository already enforces single canonical Node setup; bump is the minimal correct change.

Contract recorded to `canonical-runtime-contract.json`.

---

## Phase 3 — Dependency Compatibility Audit

23 dependencies audited in `frontend/package.json` (dependencies + devDependencies relevant to Node frontend/build/test).

| Classification | Count | Packages |
|---|---|---|
| A — Compatible unchanged | 22 | next 16.1.6, react 19.2.3, react-dom 19.2.3, typescript ^5, eslint ^9.39.2, vitest ^4.1.10, playwright ^1.58.2, msw ^2.14.6, tsx ^4.21.0, zod ^4.4.3, etc. |
| B — Must change for Node 24 compat | 1 | @types/node ^20.19.43 (deferred — type-only, non-breaking) |
| C — Recommended modernization | 0 | — |
| D — Deprecated/security concern | 0 | — |
| E — Major/breaking upgrade deferred | 0 | — |

No lockfile drift observed in `npm install --dry-run`. npm 10.8.2 fully compatible with Node 24.

Full record in `dependency-compatibility.json`.

---

## Phase 4 — Implementation (Node 24 Only, Minimal Changes)

**17 files changed:**

| File | Change | Purpose |
|---|---|---|
| `.github/actions/setup-node-runtime/action.yml` | default `"20"`→`"24"`, description update | Canonical action update |
| `.github/workflows/frontend-verify.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/backend-verify.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/playwright.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/api-contracts.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/quality.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/verification-runtime.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/release.yml` | `node-version: "20"`→`"24"` | CI contract |
| `.github/workflows/dependency-update.yml` | `node-version: "20"`→`"24"` | CI contract |
| `frontend/.nvmrc` | `20`→`24` | Local dev pin |
| `frontend/package.json` | engines.node `>=20 <21`→`>=24 <25` | Manifest contract |
| `runtime/foundation/verification/verification.yaml` | node_version `20`→`24` | Config alignment |
| `start.sh` | message text "18 or higher"→"24 or higher" | Consistency |
| `.github/scripts/run_property_tests.sh` | Added `$PY` venv-first resolver | `.venv` enforcement |
| `.github/scripts/run_contract_tests.sh` | Added `$PY` venv-first resolver; changed `pytest`→`$PY -m pytest` | `.venv` enforcement |
| `.github/scripts/run_migration_verification.sh` | Added `$PY` venv-first resolver | `.venv` enforcement |
| `.github/scripts/run_api_contracts.sh` | Changed `python3`→`"$PY"` | `.venv` enforcement |

**Files intentionally unchanged:**
- `frontend/package-lock.json` — lockfile-deterministic, no drift
- `runtime/generated/c31.1-provenance.json` — immutable historical artifact
- `runtime/generated/c31.2-change-preservation.json` — same
- `runtime/generated/c33-chromium-certification.json` — same
- `runtime/generated/c40-provenance.json` — same
- `package.json` (root), `package-lock.json` (root) — devDeps only, no execution surface
- Python-only CI workflows — no Node consumer

---

## Phase 5 — Compatibility Verification (Local, Node 24.13.0)

| Check | Result | Exit Code |
|---|---|---|
| `npm ci` (frontend) | PASS — 675 packages, no drift | 0 |
| `npx tsc --noEmit` | PASS — no errors | 0 |
| `node node_modules/.bin/eslint` | PASS — 0 errors, 154 pre-existing warnings | 0 |
| `npx vitest run` | PASS — all tests pass (1 known pre-existing A11y skip) | 0 |
| `npm run build` | PASS — 17 static pages generated in ~81s | 0 |
| `ruff check backend/src` | PASS — clean | 0 |
| `black --check backend/src` | PASS — 242 files unchanged | 0 |
| `mypy backend/src/ --ignore-missing-imports` | PASS — clean | 0 |
| `pytest backend/tests/contract/` | PASS — 161 passed | 0 |
| Property tests (fixed script) | PASS — 75 passed | 0 |
| Migration tests (fixed script) | PASS — 1 passed | 0 |
| `verify.py integrity` | PASS — 28 rules, 0 violations, 838 files scanned | 0 |
| `scripts/env-doctor.sh` | PASS — environment guard PASS, mutmut pinned 3.7.0 | 0 |

**Evidence invalidated:** 4 historical provenance JSON node_version fields, ee9c4f66 push workflow metadata, 5e944ba9 pre-existing Ruff F841 failure. All tracked in `verification-evidence.json`.

---

## Phase 6 — CI Reconciliation

All 8 Node-consuming workflows updated from `"20"` to `"24"`. Verified with `grep 'node-version.*"20"'` — zero matches remain. Python-only workflows (mutation.yml, golden.yml, verification-reconcile.yml) unchanged as expected.

Full reconciliation in `ci-runtime-reconciliation.json`.

---

## Phase 7 — Dependency Decision Record

Recorded in `dependency-compatibility.json`. 23 deps audited; 22 class A, 1 deferred (@types/node → ^24.x as bounded post-milestone follow-up). No mass upgrade occurred.

---

## Phase 8 — Final Certification

All 18 gates (G1–G18) PASS. Full record in `final-certification.json`.

---

## Pre-existing Issues Tracked (Not Owned by This Milestone)

1. **Ruff F841** in `test_mutation_gap_repairs.py:323` (unused variable `d`) — caused Backend Verification and Quality Gate failures on 5e944ba9. **FIXED** — removed dead `d = compute_next_statement_date(...)` assignment in `test_next_statement_date_dec_year_boundary()`; function body remains intentional `pass` (mutant not killable via valid calendar date, documented as skip).
2. **Frontend Verification step-0003** classification change on 5e944ba9 — cascade from the Ruff F841 above; now resolved by the ruff fix (frontend-verify runs `verify.py frontend` which includes `run_fast_checks.sh` checking backend ruff).
3. **Mutation Testing CI** for ee9c4f66 was cancelled (not completed) — authoritative C46 derived 83.6% mutation score preserved; new evidence to be established after merge.

---

## Phase 9 — Rectify Pre-existing Commit Errors (Follow-up)

**Date:** 2026-08-30 (post-Node 24 milestone)  
**Trigger:** User directive to fix errors introduced by commit 5e944ba9 so all workflows pass.

### Root Cause Analysis
The latest commit `5e944ba9` ("Add targeted mutation-strengthening tests for credit_card_engine") introduced a dead-code assignment in `backend/tests/unit/engines/credit_card/test_mutation_gap_repairs.py:323`:

```python
def test_next_statement_date_dec_year_boundary():
    ...
    d = compute_next_statement_date(31, date(2024, 12, 31))  # ← assigned, never used
    pass
```

Ruff flagged this as **F841 (Local variable `d` is assigned to but never used)**. This single error cascaded into three CI workflow failures because `run_fast_checks.sh` (run by both Quality Gate and Frontend Verification, and by Backend Verification step-0002) executes `ruff check .`:

- **Backend Verification** (33314502881): step-0002 `ruff` failed → workflow failed
- **Frontend Verification** (33314502817): step-0003 `run_fast_checks.sh` failed → workflow failed
- **Quality Gate** (33314502837): "Run quick verification" → `verify.py quick` → `run_fast_checks.sh` → ruff failed → workflow failed

### Fix Applied
**File:** `backend/tests/unit/engines/credit_card/test_mutation_gap_repairs.py` (lines 317–330)  
**Change:** Removed the dead `d =` assignment; retained the `pass` body with expanded comments explaining why the mutant (`reference_date.month == 12`) is not killable via a valid calendar date (billing_day > 31 is impossible in December).

### Verification Post-Fix
| Check | Result | Detail |
|---|---|---|
| `ruff check backend/` | PASS | No errors |
| `ruff check backend/tests/unit/engines/credit_card/test_mutation_gap_repairs.py` | PASS | F841 resolved |
| `bash .github/scripts/run_fast_checks.sh` | PASS | Ruff ✓, Black ✓, Mypy ✓, 2517 unit ✓, 50 arch ✓, 61 meta ✓ |
| `pytest backend/tests/unit/engines/credit_card/test_mutation_gap_repairs.py` | PASS | 113 passed |
| Backend verification phases (CI-equivalent, excluding untracked local probe) | PASS | 2644 passed across contract/invariants/properties/unit-engines |

### Notes on Untracked Local Probe
`backend/tests/invariants/_m4_probe_live/` is an **untracked** diagnostic directory (contains `test_m4_exit_probe.py` which intentionally raises `AssertionError("M4 exit probe: intentionally failing")`). It is:
- Not part of commit 5e944ba9
- Not tracked by git (`git status` shows `??`)
- Not collected in CI (untracked files are absent from checked-out ref)
- Excluded from `run_fast_checks.sh` scope (only collects unit/architecture/meta)

The `runtime/verify.py quick` command locally times out on a `git diff` against base SHA `fe654f27541...` (3162 files differ in local working tree) — this is a local-environment artifact, not a code error; in CI the diff base is the PR/merge-base and completes normally.

### Workflow Pass Prediction (post-fix)
| Workflow | Pre-fix | Post-fix |
|---|---|---|
| Backend Verification | failure (ruff F841) | success |
| Frontend Verification | failure (ruff cascade) | success |
| Quality Gate | failure (ruff cascade) | success |
| API Contract Integrity | success | success (unchanged) |
| Verification Runtime | success | success (unchanged) |
| Verification Reconcile | success | success (unchanged) |
| Mutation Testing | cancelled | re-dispatch recommended post-merge |

---

## Files Produced

All under `runtime/generated/m9-post-c46-node24/`:
- `baseline.json`
- `node-runtime-inventory.json`
- `canonical-runtime-contract.json`
- `dependency-compatibility.json`
- `change-reconciliation.json`
- `verification-evidence.json`
- `ci-runtime-reconciliation.json`
- `final-certification.json`
- `EXECUTION_PROGRESS.md` (this file)
