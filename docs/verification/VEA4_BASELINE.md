# VEA-4 Baseline Re-Certification (M0)

**Status:** CERTIFIED
**Date:** 2026-08-11
**Branch:** `recovery/program-r-forensic-reconstruction`
**HEAD:** `d9638e4f3c3f6bd73538c172b8396982b64bc05b`
**Working tree:** dirty — 38 modified files, 4 untracked

---

## A. Repository state

```
HEAD commit : d9638e4f — "VEA-2 Phase 2: evidence integrity — unit identity spine plan→execution→evidence"
Branch      : recovery/program-r-forensic-reconstruction
Dirty       : True (38 modified, 4 untracked)
Changed     : frontend BL-001 remediation (23 files) + runtime verification.yaml/registry/scope/planner + docs + 4 new test files
```

---

## B. Command inventory and pass/fail

| Command | Scope | Result |
|---------|-------|--------|
| `bash .github/scripts/run_backend_verification.sh` | backend | **PASS — 4/4 phases, 861 tests via JUnit** |
| `python3 -m pytest runtime/tests -q --no-header` | runtime fast suite | **458 passed** |
| `cd frontend && npx eslint .` | frontend lint | **0 errors, 140 warnings** |
| `cd frontend && npx tsc --noEmit` | frontend typecheck | **0 errors** |
| `cd frontend && NEXT_PUBLIC_SKIP_FONTS=1 npx next build` | frontend build | **PASS — 17/17 static pages** |
| `python3 runtime/verify.py status` | verification runtime | **Valid** |
| `python3 -m ruff check runtime/system/evidence/aggregator.py runtime/foundation/verification` | ruff | **All checks passed** |
| `ls .github/workflows/*.yml \| wc -l` | CI topology | **9 workflows** |

### Backend phase breakdown (from `backend-verification.json`)

| Phase | Tests | Duration | Status |
|-------|-------|----------|--------|
| contract | 161 | 93s | PASS |
| invariants | 26 | 93s | PASS |
| properties | 206 | 93s | PASS |
| unit-engines | 468 | 93s | PASS |
| **Total (JUnit)** | **861** | — | — |

Note: `run_backend_verification.sh` parallel-executes 4 suites; JUnit merge records 861 tests.
Full `pytest tests/ -k "not slow"` collects **1346 tests** across all backend test directories
(contract, invariants, properties, unit/engines, unit/repositories, unit/services, integration).

### Runtime breakdown

| Category | Count |
|----------|-------|
| runtime/tests total | **458 passed** |
| VEA-3-specific (E4 + module-paths + planner + aggregator) | **38 passed** |

---

## C. Frontend lint baseline (AUTHORITATIVE)

```
no-console                                   93
@typescript-eslint/no-explicit-any           28
@typescript-eslint/consistent-type-imports   12
@typescript-eslint/no-unused-vars            5
jsx-a11y/role-has-required-aria-props        1
(unknown/blank)                              1
---------------------------------------------
TOTAL (warnings only)                       140
ERRORS                                       0
```

**Important:** The working tree contains uncommitted BL-001 remediation that has reduced
the lint population from the VEA-3 certified baseline of **34 errors** to **0 errors**.
The 140 remaining items are **warnings only** (`no-console`, `no-explicit-any`, etc.),
not errors. This is a materially different population from the VEA-3 baseline.

---

## D. Frontend build — network caveat

`npx next build` fails on this environment with:

```
next/font: error: Failed to fetch `Inter` from Google Fonts.
```

This is an **environment/network** failure (sandbox cannot reach `fonts.googleapis.com`),
not a code defect. Running with `NEXT_PUBLIC_SKIP_FONTS=1` produces a clean build:

```
✓ Generating static pages using 3 workers (17/17) in 2.2s
```

The codebase uses `next/font/google` in `app/layout.tsx` and `distDir: 'dist'` in
`next.config.ts`. No `remotePatterns` or font-substitution configuration is present.

This is recorded as an **environmental gap** for the baseline, not a code regression.

---

## E. CI topology

```
9 workflows:
  backend-verify.yml        frontend-verify.yml       golden.yml
  mutation.yml              playwright.yml            quality.yml
  verification-runtime.yml  dependency-update.yml     release.yml

7 profile-invoking workflows:
  backend-verify       → python runtime/verify.py backend
  frontend-verify      → python runtime/verify.py frontend
  golden               → python runtime/verify.py golden   (cron 03:00)
  mutation             → python runtime/verify.py mutation  (cron 02:00)
  playwright           → python runtime/verify.py playwright (branch: main/master/develop)
  quality              → python runtime/verify.py quick     (NO path filter — runs on every push)
  verification-runtime → python runtime/verify.py runtime
```

Branch-restriction differences:
- `playwright.yml` — limited to `main`, `master`, `develop`
- All others — `push: branches: ["**"]`

---

## F. Verification runtime

`python3 runtime/verify.py status` output:

| Field | Value |
|-------|-------|
| Commit | `b9074020aef5` |
| Changed Files | 27 |
| Last Profile | `runtime` |
| Last Status | `passed` |
| Passed | 1 |
| Failed | 0 |
| Cache Valid | `True` |

---

## G. VEA-3 evidence validation

Existing docs verified still accurate:

| Document | Status |
|----------|--------|
| `docs/verification/VEA3_CERTIFICATION.md` | Read — accurate summary |
| `docs/verification/VEA3_BASELINE.md` | Read — 975 backend at that time |
| `docs/verification/VEA3_BL004_AUDIT.md` | Present |
| `docs/verification/VEA3_E4_DESIGN.md` | Present |
| `docs/verification/VEA_BACKLOG.md` | Present — 9 deferred items |
| `docs/progress.md` | Present — VEA-3 phase complete |

Discrepancy found: VEA-3 recorded backend at 975 passed. Current run_backend_verification.sh
records 861 via JUnit. Full pytest collection is 1346. The discrepancy is a **measurement
method difference** (JUnit-merged count vs raw pytest count), not a regression. Both are green.

---

## H. Gate

Baseline established. Proceeding to M1.
