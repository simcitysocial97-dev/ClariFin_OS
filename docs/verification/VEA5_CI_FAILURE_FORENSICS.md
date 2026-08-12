# VEA-5 — M0 CI Failure Forensics

**Milestone:** VEA-5 M0 — Baseline + CI Failure Forensics
**Status:** COMPLETE
**Date:** 2026-08-11
**Constraint honored:** No `.github/workflows/` file was modified in M0.

---

## 1. Core question

> Why do local checks pass while GitHub Actions workflows fail?

**Answer (one sentence):** Local certification used the **raw full-suite scripts** (always
green for backend/frontend); CI delegates to **change-scoped `runtime/verify.py <profile>`**,
which — because this branch diverged from `origin/main` by **967 files** and never merged —
selects a **maximal blast radius** and runs heavy units (`run_runtime_verification.sh`,
`run_mutation_selective.sh`, `run_frontend_verification.sh`) that **fail for concrete,
reproducible reasons**. Locally, `verify.py` without CI env vars resolves `base_ref=None` →
0 changed files → it refuses to run, so "local `verify.py`" is a *third* behavior, not the
CI behavior.

Three behaviors, explicitly:

| # | Behavior | Changed files | Result |
|---|----------|---------------|--------|
| A | Raw full-suite scripts (`run_*_verification.sh`) | n/a (full) | GREEN (backend 468, frontend lint RED-but-known, etc.) |
| B | `verify.py <profile>` **in CI** (push, `GITHUB_EVENT_NAME=push` → merge-base → 967) | 967 | FAILS on runtime/mutation/frontend-lint units |
| C | `verify.py <profile>` **locally** (no `GITHUB_*` env → `base_ref=None` → `git diff HEAD`) | 0 | refuses to run (exit 1) |
| C' | `verify.py <profile>` locally **with `VERIFICATION_BASE_REF`** | 967 | reproduces CI failures (B) |

This directly motivates VEA-5's local/CI plan-equivalence milestone (M4) and the
"same plan + different environment" vs "different plan" distinction (M6).

---

## 2. CI failure matrix

9 workflows audited. 8 observed failing; `release.yml` has **no runs** (tag/manual
triggered) → not failing, recorded as N/A.

| # | Workflow | Trigger observed | Run ID | Conclusion | Failing step(s) |
|---|----------|------------------|--------|-----------|-----------------|
| W1 | backend-verify.yml | push (branch) | 31505903356 | failure | `run_runtime_verification.sh`, `run_mutation_selective.sh` |
| W2 | frontend-verify.yml | push (branch) | 31505903357 | failure | `run_mutation_selective.sh`, `run_runtime_verification.sh`, `run_frontend_verification.sh` |
| W3 | quality.yml | push (branch) | 31505903313 | failure | `run_runtime_verification.sh`, `run_mutation_selective.sh`, (+ cache exit-0 anomaly) |
| W4 | verification-runtime.yml | push (branch) | 31505903348 | failure | `run_runtime_verification.sh` (runtime self-test) |
| W5 | golden.yml | schedule (main) | 31457734672 | failure | `Download golden results` (Regression Comparison job) |
| W6 | mutation.yml | schedule (main) | 31455335382 | failure | `Aggregate Report` job |
| W7 | dependency-update.yml | schedule (main) | 31358599796 | failure | `Bootstrap Engineering Runtime` |
| W8 | playwright.yml | push/PR (main) | 31014121494 | failure | `Run Playwright Tests` |
| W9 | release.yml | — | — | no runs | N/A |

---

## 3. Per-workflow forensics

### W1 — Backend Verification (31505903356)

- **Command:** `python runtime/verify.py backend`
- **Plan (967 changed files):** backend units + `run_frontend_verification.sh` (passed) +
  `run_fast_checks.sh` (passed) + `run_backend_verification.sh` (passed) +
  `run_runtime_verification.sh` (**failed**) + `run_mutation_selective.sh` (**failed**).
- **Root causes:**
  1. **Planner over-selection (scope policy).** 967-file branch divergence → maximal blast
     radius → CI runs `runtime` and `mutation` units even though the pushed change may not
     touch them. (See §5.)
  2. **Genuine runtime self-test failure** — `test_backend_exit_contract_holds_both_directions`
     times out at 30s (see W4).
  3. **Genuine mutation unit failure** — `run_mutation_selective.sh` runner uses `python`
     (not `python3`) → `FileNotFoundError: 'python'` (see W6).
- **Local reproduction:** `VERIFICATION_BASE_REF=… python3 runtime/verify.py backend` →
  `Failed: 2` (same unit identities). **Reproducible.**
- **Classification:** `planner divergence` (scope) + `verification-runtime failure`
  (timing) + `dependency/environment` (mutation `python` binary).
- **Backend application tests:** GREEN (the full backend suite passes; this is NOT an app defect).

### W2 — Frontend Verification (31505903357)

- **Command:** `python runtime/verify.py frontend`
- **Plan (967 changed files):** `run_backend_verification.sh` (passed) + `run_fast_checks.sh`
  (passed) + `run_mutation_selective.sh` (**failed**) + `run_runtime_verification.sh`
  (**failed**) + `run_frontend_verification.sh` (**failed on lint, 450.6s**).
- **Root causes:** same as W1 (runtime + mutation) **plus** frontend lint = 34 pre-existing
  errors (VEA-2/VEA-4 BL-001). The frontend lint failure is **pre-existing and unrelated** to
  the backend change (classified `PRE_EXISTING` in VEA-2 Phase 1.5, deliberately out of scope).
- **Local reproduction:** `VERIFICATION_BASE_REF=… python3 runtime/verify.py frontend` →
  `Failed: 3`, step-0005 failed on lint. **Reproducible.**
- **Classification:** `planner divergence` + `verification-runtime failure` (timing) +
  `dependency/environment` (mutation) + `frontend toolchain` (pre-existing lint, known).

### W3 — Quality Gate (31505903313)

- **Command:** `python runtime/verify.py quick`
- **Plan (967 changed files):** same broad set as W1/W2. `Failed: 3`.
- **Additional finding — exit-code-contract violation (cache-induced):**
  Local `verify.py quick` printed `Verification FAILED` / `Failed: 3` but the process
  **exited 0** (cache-hit path; the verification cache fingerprint matched). CI exited 1
  (fresh cache fingerprint). The no-cache `verify.py runtime` run correctly recorded
  `Last Status: failed` and exited 1. **The verification cache must not mask failure exit
  codes.** This is a genuine verification-runtime defect, not a CI-environment issue.
- **Local reproduction:** `VERIFICATION_BASE_REF=… python3 runtime/verify.py quick` →
  `Failed: 3` + `QUICK_EXIT=0` (anomaly). **Reproducible.**
- **Classification:** `planner divergence` + `verification-runtime failure` (timing) +
  `dependency/environment` (mutation) + `verification-runtime / exit-code contract` (cache).

### W4 — Verification Runtime (31505903348)

- **Command:** `python runtime/verify.py runtime`
- **Failing unit:** `run_runtime_verification.sh` → runtime self-test
  `runtime/tests/test_backend_evidence.py::TestExitCodeContract::test_backend_exit_contract_holds_both_directions`.
- **Exact failure (local):** the test injects a failing probe and runs the real
  `run_backend_verification.sh` as a subprocess wrapped by `pytest-timeout` at **30s**. The
  full backend verification script now takes **~66–140s** (see W1 step-0003 66.3s,
  W2 step-0001 140.6s), exceeding the 30s wrapper →
  `Failed: Timeout (>30.0s) from pytest-timeout`.
- **Root cause:** the runtime self-test's subprocess timeout (30s) is shorter than the real
  backend verification runtime. This is a **test-isolation / timing** defect in the runtime's
  own test harness, **not** an application defect. It gates `verify.py runtime` and is pulled
  into `backend`/`frontend`/`quality` plans via over-selection.
- **Local reproduction:** `python3 -m pytest runtime/tests/ -q --timeout=30` →
  `1 failed, 457 passed`. **Reproducible.**
- **Classification:** `timing/concurrency` (verification-runtime test wrapper too tight) —
  genuinely fails, must be fixed, not suppressed.
- **Runtime suite regression:** VEA-4 certified "Runtime: 458 passed"; M0 measures
  **457 passed / 1 failed**.

### W5 — Golden Dataset Regression (31457734672, schedule on `main`)

- **Failing step:** Job `Regression Comparison` → `Download golden results` (the
  `Golden Datasets` job itself **succeeded**).
- **Root cause:** the **`main` branch's** golden workflow is a 2-job design; the comparison
  job downloads an artifact from the first job and fails. The current branch's
  `golden.yml` is **consolidated to a single job** (129 lines differ from `main`) and does
  **not** contain the `Regression Comparison` job. So this failure is a **stale-`main`
  workflow** issue, not present in the current branch's workflow.
- **Local reproduction:** not run (current branch workflow differs; would need `main`).
- **Classification:** `workflow command divergence` (stale `main` workflow) /
  `generated artifact` (cross-run artifact dependency). **Branch divergence between `main`
  and this branch is the underlying cause.**
- **Note:** `golden.yml` is identical to `main`? **No** — `git diff origin/main` shows
  129 changed lines. So `main` still runs the old failing design.

### W6 — Mutation Testing (31455335382, schedule on `main`)

- **Failing step:** `Aggregate Report` job (all 50+ per-engine mutation jobs succeeded or
  were skipped).
- **Root cause (two layers):**
  1. The **`main`** mutation workflow is the old 50+ job design; its `Aggregate Report` job
     fails (218 lines differ from current branch's consolidated `mutation.yml`).
  2. The **current branch's** `mutation.yml` runs `python runtime/verify.py mutation` →
     `run_mutation_selective.sh`, which **fails locally with `FileNotFoundError: 'python'`**
     (the runner command hardcodes `python` instead of `python3`). So even the current
     branch's mutation path fails, on a genuine, reproducible defect.
- **Exact defect:** `.github/scripts/run_mutation_selective.sh` mutmut runner:
  `"python -m pytest tests/unit/ tests/properties/ -x -q --timeout=30"`. On
  `ubuntu-latest`, `python` is not on PATH (only `python3`). `subprocess.Popen` raises
  `FileNotFoundError: [Errno 2] No such file or directory: 'python'`. Run locally → identical
  1.3s failure.
- **Local reproduction:** `bash .github/scripts/run_mutation_selective.sh backend` →
  `FileNotFoundError: 'python'`. **Reproducible.**
- **Classification:** `workflow command divergence` (stale `main`) +
  `dependency/environment` (mutation runner hardcodes `python` not `python3`).

### W7 — Dependency Updates (31358599796, schedule on `main`)

- **Failing step:** `Bootstrap Engineering Runtime`.
- **Exact error (from raw CI log):**
  ```
  ##[error]Can't find 'action.yml', 'action.yaml' or 'Dockerfile' under
  '/home/runner/work/ClariFin_OS/ClariFin_OS/.github/actions/bootstrap-runtime'.
  Did you forget to run actions/checkout before running your local action?
  python: can't open file '/home/runner/work/ClariFin_OS/ClariFin_OS/runtime/verify.py':
  [Errno 2] No such file or directory
  ```
- **Root cause:** the checkout step did **not** populate the working tree at execution time
  (the bootstrap action and `runtime/verify.py` were absent). The same
  `bootstrap-runtime` action **succeeded in backend/frontend/golden/mutation/verification-runtime
  runs on the same day**, so this is **not** a code defect in the action — it is a
  **transient checkout / runner-workspace state** issue (incomplete checkout, likely a
  runner workspace-not-cleaned condition). `dependency-update.yml` is **identical to `main`**.
- **Local reproduction:** the bootstrap generator (`tools/generators/build_cross_layer_map.py`)
  runs clean locally (exit 0); the failure is environment/runner-state, not reproducible by
  source change.
- **Classification:** `environment / filesystem-path` (transient checkout / runner workspace
  state). **Confidence: medium** — exact trigger is a runner condition; evidence shows the
  same action works elsewhere, pointing away from a code defect.

### W8 — Playwright Tests (31014121494, push/PR on `main`)

- **Failing step:** `Run Playwright Tests`.
- **Exact error (from raw CI log):**
  ```
  [WebServer] Error: Could not find a production build in the 'dist' directory.
  Try building your app with 'next build' before starting the production server.
  Error: Process from config.webServer was not able to start. Exit code: 1
  ```
- **Root cause:** the `main` playwright workflow (164 lines differ from current branch)
  runs `npx playwright test` without first building the frontend. The current branch's
  `run_playwright_tests.sh` **does** `npm run build` (line 27) before `npx playwright test`,
  addressing the VEA4-3 "Playwright CLI environment gap" in this branch. `main` still runs
  the stale version that omits the build step.
- **Local reproduction:** not run (browser/E2E environment); root cause is the missing
  `next build` step, confirmed from the log and from the current-branch script diff.
- **Classification:** `workflow command divergence` (missing build step on `main`) /
  `filesystem-path` (`dist/` not built). Corresponds to deferred item **VEA4-3**.
- **Note:** `playwright.yml` triggers only on `main`/`master`/`develop`, so it does not run
  on this recovery branch regardless.

### W9 — Release (release.yml)

- **Observed runs:** none (`gh run list` returned empty). Triggered by tag/release or
  `workflow_dispatch`. **Not failing** — recorded as N/A. Audited for topology only (M7
  later). No change made.

---

## 4. Classification summary (taxonomy from VEA-2 §11)

| Workflow | Primary classification | Secondary |
|----------|------------------------|-----------|
| W1 backend-verify | `planner divergence` (scope) | `verification-runtime failure` (timing), `dependency/environment` (mutation) |
| W2 frontend-verify | `planner divergence` (scope) | `verification-runtime failure`, `dependency/environment`, `frontend toolchain` (pre-existing lint) |
| W3 quality | `planner divergence` (scope) | `verification-runtime failure`, `dependency/environment`, `verification-runtime / exit-code contract` (cache) |
| W4 verification-runtime | `timing/concurrency` | genuine verification-runtime test defect |
| W5 golden | `workflow command divergence` (stale `main`) | `generated artifact` |
| W6 mutation | `workflow command divergence` (stale `main`) | `dependency/environment` (mutation `python`) |
| W7 dependency-update | `environment / filesystem-path` (transient checkout) | confidence medium |
| W8 playwright | `workflow command divergence` (missing build) | `filesystem-path` (VEA4-3) |
| W9 release | N/A | no runs |

**No failure was classified "genuine application failure" for the branch-triggered
workflows** — the backend application suite is GREEN. The genuine defects are in the
**verification runtime's own test harness** (W4) and the **mutation script's `python`
binary** (W6), both of which are CI tooling, not product code.

---

## 5. Architectural failure (the real finding)

**The change-scoped planner computes blast radius against `origin/main` via merge-base.
Because this long-lived branch has 967 unmerged files, every push looks "all changed", so
the planner selects the maximal unit set and runs expensive units (`mutation`, `runtime
self-test`) that fail.** This is the structural reason CI is red while the raw suite is
green, and it is exactly what VEA-5's three-tier model (local/PR/deep) must fix:

- **Tier 1 (local):** should scope to the *actual* change, not `origin/main` divergence.
- **Tier 2 (PR):** should explain every exclusion (no unexplained skips).
- **Tier 3 (deep):** should own mutation/golden/E2E explicitly, not pull them into every
  push via over-selection.

The 967-file divergence is **not** something M0 can or should "fix" by editing workflows —
it is the branch topology. But it must be made explicit so Tier 2 can say:
"mutation excluded: not in the change's blast radius; scheduled for deep tier."

---

## 6. Known environment limitations (recorded, not resolved in M0)

- **Branch divergence:** `recovery/program-r-forensic-reconstruction` is 967 files ahead of
  `origin/main` and unmerged → maximal blast radius on every push.
- **`mutmut` binary:** installed locally; not guaranteed on `ubuntu-latest` and the runner
  command uses `python` (absent). Both feed W6.
- **`python` vs `python3`:** `ubuntu-latest` provides `python3`, not `python` (W6).
- **Playwright `dist/` build:** `main`'s playwright path omits `next build` (W8 / VEA4-3).
- **Verification cache can mask failure exit codes** under a matching fingerprint (W3).
- **Transient checkout state** observed once for `dependency-update` (W7).

---

## 7. Deferred VEA-4 items — status in M0

- **VEA4-1 (quality.yml duplication / planner scope hierarchy):** confirmed relevant —
  `quality.yml` selects the same broad units as `backend`/`frontend` (over-selection). Not
  resolved in M0; revisit in M2/M7 with planner evidence. **Still OPEN.**
- **VEA4-2 (branch protection visibility):** not observable from CI logs; branch protection
  is a repo setting, not a workflow. Recorded as **UNKNOWN**; defer to M8 with explicit
  evidence.
- **VEA4-3 (Playwright CLI environment gap):** root cause confirmed — `main` omits
  `next build` (W8). Current branch's `run_playwright_tests.sh` already builds. The branch
  divergence between `main` and this branch is the remaining gap. **Partially addressed in
  branch; not merged to `main`.**

---

## 8. Recommended M1 actions (handoff)

1. **M1** — Author `docs/verification/VEA5_EXECUTION_MODEL.md` defining local/PR/deep tiers,
   triggers, scope behavior, full-run behavior, evidence/environment/exit/manifest/verdict
   semantics. Do not implement speculative functionality first.
2. **M2** — Audit the planner for `unit_id / capability / impact_kinds / dependencies /
   scope policy / execution cost / environment / tier eligibility`. Add the smallest
   extension so Tier 2 can emit explained exclusions (directly addresses W1–W3
   over-selection).
3. **M3/M5** — Fix the two genuine CI-tooling defects before wiring PR gating:
   - W4: raise/remove the 30s `pytest-timeout` wrapper around the backend-script subprocess
     in `test_backend_exit_contract_holds_both_directions` (or run a lighter probe).
   - W6: change `run_mutation_selective.sh` runner `python` → `python3`.
4. **M4/M6** — Build local/CI plan equivalence + reconciliation so "same plan + different
   environment" is distinguishable from "different plan" (addresses the three-behavior split
   in §1).
5. **M3 (cache):** ensure the verification cache never masks a failure exit code (W3).
6. **M7/M8** — Re-audit workflow topology; resolve VEA4-1 with planner evidence; record
   branch-protection status explicitly (VEA4-2). Do **not** consolidate/delete workflows
   without evidence.
7. **M9** — Audit CodeQL (default setup enabled) and record `AUDITED — NO CHANGE REQUIRED`
   or justified changes.
8. **M10** — Define the deep profile contract (golden/mutation/E2E home).

---

## 9. M0 VERDICT

**CERTIFIED** (forensics complete; baseline recorded; no workflow modified; all 8 failing
workflows have evidence-backed root causes; the local-green/CI-red question is answered with
a structural (not hand-waved) explanation).

Outstanding items are deferred to later milestones with explicit prerequisites (§8), per the
"do not force completion" discipline. No speculative framework introduced; no functionality
deleted; no tests weakened.
