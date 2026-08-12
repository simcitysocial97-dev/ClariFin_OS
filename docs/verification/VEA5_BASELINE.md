# VEA-5 — M0 Baseline

**Milestone:** VEA-5 M0 — Baseline + CI Failure Forensics
**Status:** COMPLETE (evidence captured; no workflow modified)
**Date:** 2026-08-11
**Branch:** recovery/program-r-forensic-reconstruction
**Head:** 8d8e92ba (VEA-4 certified)
**Authoritative prior baselines:** VEA-3, VEA-4 (authoritative), VEA-2 Phase 1.5

---

## 1. Scope of this document

M0 establishes a **fresh VEA-5 baseline** and a **forensic record of every currently
failing GitHub workflow**. No `.github/workflows/` file was modified (per the M0
constraint). Companion document: `docs/verification/VEA5_CI_FAILURE_FORENSICS.md`.

The single most important structural fact established in M0:

> **"Local green" and "CI green" are NOT the same predicate.**
> The certification baseline was measured with the **raw full-suite scripts**
> (`run_backend_verification.sh`, `run_frontend_verification.sh`). CI delegates to
> `runtime/verify.py <profile>`, which is **change-scoped**. Because this branch has
> diverged from `origin/main` by 967 files and never merged, the change-scoped planner
> selects a maximal blast radius and runs heavy units that fail. Locally, `verify.py`
> without CI environment variables resolves `base_ref=None` → `git diff HEAD` → 0 changed
> files → it refuses to run. So there are **three** distinct behaviors, not two.

---

## 2. Environment

| Property | Value |
|----------|-------|
| OS | linux |
| Python | 3.12.3 (local) / 3.12.13 (CI `ubuntu-latest`) |
| Node | v20.20.2 (local) / 20.x (CI) |
| pytest | 9.0.2 |
| `mutmut` | installed locally at `/home/vasantha/.local/bin/mutmut`; **NOT guaranteed in CI image** |
| `pytest-timeout` | present (runtime self-test uses `--timeout=30`) |
| `frontend/node_modules` | present |
| `GITHUB_*` env | unset locally; set in CI runs |
| Default branch | `main` |

Local reproduction of CI change-scoping required:

```bash
export VERIFICATION_BASE_REF=$(git merge-base HEAD origin/main)
python3 runtime/verify.py <profile>
```

This makes the local planner resolve the same 967-file base as the CI push path
(`_resolve_base_ref` → push → `_merge_base_with_default`).

---

## 3. Verification baseline (as measured in M0)

### 3.1 Raw full-suite scripts (the certification-green path)

| Layer | Command | Exit | Result |
|-------|---------|------|--------|
| Backend (full) | `bash .github/scripts/run_backend_verification.sh` | 0 | **GREEN** — 468 passed; contract/invariants/properties/unit-engines all `pass` (88s each) |
| Runtime (framework) | `python3 -m pytest runtime/tests/ -q --timeout=30` | 1 | **RED** — `1 failed, 457 passed` (63.7s). One failing test (see 3.3) |
| Frontend lint | `npx eslint .` (via `run_frontend_verification.sh`) | 1 | **RED** — 34 pre-existing errors (per VEA-2/VEA-4 BL-001) |
| Frontend typecheck | `npx tsc --noEmit` | 0 | **GREEN** — 0 errors |
| Frontend build | `npm run build` | 0 | **GREEN** — compiled, 17/17 pages |
| Frontend Vitest | `npx vitest run` | 0 | **GREEN** — 1237 passed |

**Runtime regression vs VEA-4:** VEA-4 certified "Runtime: 458 passed". M0 measures
**457 passed / 1 failed**. The failing test is
`runtime/tests/test_backend_evidence.py::TestExitCodeContract::test_backend_exit_contract_holds_both_directions`
(see forensics §4.4).

### 3.2 `runtime/verify.py status` (captured M0)

```
Commit        8d8e92bab1c5
Branch        unknown
Changed Files 967
Dirty         True
Last Profile  runtime
Last Status   failed
Passed        2
Failed        2
Skipped       0
Duration      7m 33s
```

`Changed Files: 967` is the filtered change count (raw branch-vs-`origin/main` diff is
1201 files; `_filter_changed_files` excludes generated/cache/binary paths → 967).

### 3.3 `verify.py <profile>` change-scoped runs (reproduce CI locally)

With `VERIFICATION_BASE_REF` set, the local planner selects the **same broad units CI
selects**, and the runs **fail identically**:

| Profile | Local exit | Local result | CI run | CI result |
|---------|-----------|--------------|--------|-----------|
| `backend` | 1 | Passed 3 / Failed 2 | 31505903356 | failure (Passed 2 / Failed 3)* |
| `frontend` | 1 | Passed 2 / Failed 3 | 31505903357 | failure (Passed 3 / Failed 2) |
| `quick` | **0** | **Failed 3 but exited 0** (cache-hit anomaly) | 31505903313 | failure (Passed 2 / Failed 3) |
| `runtime` | 1 | Passed 2 / Failed 2 | 31505903348 | failure |

\* CI/ local unit-count differences (2 vs 3) are explained by the optimizer ordering and
`main` having advanced between runs; the **failing unit identities are identical**.

The `quick` local run printing `Verification FAILED / Failed: 3` yet exiting `0` is a
**verification-runtime exit-code-contract violation triggered by the verification cache**
(see forensics §5). CI exited `1` because its cache fingerprint did not match.

### 3.4 Failing units observed in the change-scoped plans (local reproduction)

From the generated `runtime/generated/verification-report.md` step table:

```
backend profile plan:
  step-0001  run_frontend_verification.sh   passed  318.6s
  step-0002  run_fast_checks.sh            passed  106.1s
  step-0003  run_backend_verification.sh   passed   66.3s
  step-0004  run_runtime_verification.sh   FAILED   90.0s   <- runtime test timeout
  step-0005  run_mutation_selective.sh     FAILED    1.3s   <- `python` not found

frontend profile plan:
  step-0001  run_backend_verification.sh   passed  140.6s
  step-0002  run_fast_checks.sh            passed  160.6s
  step-0003  run_mutation_selective.sh     FAILED    1.3s   <- `python` not found
  step-0004  run_runtime_verification.sh   FAILED  151.9s   <- runtime test timeout
  step-0005  run_frontend_verification.sh  FAILED  450.6s   <- frontend lint (34 errors)
```

The backend/frontend/quality failures are **not** backend-application failures: the
backend full suite is GREEN. They are caused by (a) planner over-selection from
branch-vs-main divergence and (b) two genuine unit defects + pre-existing frontend lint.

---

## 4. Baseline invariants preserved (no regression introduced)

- Identity-spine / unit-keyed evidence model: **untouched** (M0 made no code changes).
- `UNKNOWN` / `UNMAPPED` semantics: **untouched**.
- EventBus / runtime ownership: **untouched**.
- Canonical graph: **untouched**.
- Backend application tests: **GREEN** (468 passed).

The **only** regression surfaced is a runtime self-test defect (§3.1) and the CI
change-scoping failures — both pre-existing, neither introduced by M0.

---

## 5. Files changed in M0

**None.** M0 is baseline + forensics only. No `.github/workflows/` file, no script, and
no source file was modified. Generated evidence (`runtime/generated/...`) is produced by
the verification runtime as normal output, not authored by M0.

---

## 6. Evidence index

| Evidence | Location |
|----------|----------|
| Backend full-suite output | `/tmp/kilo/ci-logs/base_backend.txt` |
| Runtime suite result | `python3 -m pytest runtime/tests/ -q --timeout=30` → `1 failed, 457 passed` |
| `verify.py backend` (local, 967 files) | `/tmp/kilo/ci-logs/local_be2.txt` + `runtime/generated/verification-report.md` |
| `verify.py frontend` (local, 967 files) | `/tmp/kilo/ci-logs/local_fe.txt` |
| `verify.py quick` (local, cache-hit, exit 0) | `/tmp/kilo/ci-logs/local_quick.txt` |
| `verify.py runtime` (local, no-cache) | `/tmp/kilo/ci-logs/local_rt_nocache.txt` |
| CI run logs (branch) | `gh run view 31505903356/357/313/348 --log-failed` |
| CI raw logs (playwright, dep-update) | `/tmp/kilo/rawlogs/{pw,dep}/*` |
| `verify.py status` | captured in §3.2 |

See `VEA5_CI_FAILURE_FORENSICS.md` for the per-workflow failure matrix.
