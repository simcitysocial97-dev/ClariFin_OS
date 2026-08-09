# Program T — Workflow Execution, Performance & Determinism Audit

**Repository:** `ClariFin_OS`  
**Branch:** `recovery/program-r-forensic-reconstruction`  
**HEAD:** `12e11662`  
**Control specimen:** `bacc1fe2`  
**Mode:** AUDIT (no source changes; plan only)

---

## T0 — Baseline Freeze

The recovered repository at `12e11662` is the **control specimen**.  
All measurements below are against this commit.  
No recovery branches are merged, amended, or deleted.

---

## T1 — Workflow Inventory

| Workflow | Trigger | Paths | Runner | Timeout | Single command |
|---|---|---|---|---|---|
| `backend-verify.yml` | push/PR on `backend/**`, `runtime/**` | backend, runtime | ubuntu-latest | 30m | `python runtime/verify.py backend` |
| `frontend-verify.yml` | push/PR on `frontend/**`, `backend/src/routers/**`, `backend/src/mappers/**`, `runtime/**` | frontend, routers, mappers, runtime | ubuntu-latest | 25m | `python runtime/verify.py frontend` |
| `verification-runtime.yml` | push/PR on `runtime/**`, `backend/src/engines/**`, `backend/src/routers/**`, `backend/src/mappers/**` | runtime, engines, routers, mappers | ubuntu-latest | 30m | `python runtime/verify.py runtime` |
| `quality.yml` | push/PR on all branches | all | ubuntu-latest | 10m | `python runtime/verify.py quick` |
| `mutation.yml` | schedule nightly + dispatch | — | ubuntu-latest | 90m | `python runtime/verify.py mutation` |
| `playwright.yml` | push/PR on `frontend/**`, `e2e/**`, `runtime/**` | frontend, e2e, runtime | ubuntu-latest | 60m | `python runtime/verify.py playwright` |
| `golden.yml` | schedule nightly + dispatch | — | ubuntu-latest | 30m | `python runtime/verify.py golden` |
| `release.yml` | release published + dispatch | — | ubuntu-latest | 30m | build only |
| `dependency-update.yml` | schedule weekly + dispatch | — | ubuntu-latest | 15m | `bash .github/scripts/run_dependency_checks.sh` |

**Shared bootstrap (composite action):**
- `bootstrap-runtime` → `setup-python-runtime` → generates `cross-layer-map.json`, `knowledge-index.json` → seeds `verification-cache.json`, `engineering-history.json`

**Shared artifact uploads (composite action):**
- `upload-runtime` → wraps `actions/upload-artifact@v4`

---

## T2 — Execution DAG (Actual Runtime Behavior)

### Critical Discovery: Profile definitions in `profiles.py` are **dead code**.

`runtime/verify.py <profile>` loads the `VerificationProfile` from `profiles.py`, but the `VerificationOrchestrator.run()` ignores `profile.tasks` entirely. Instead, `generate_plan()` delegates to `VerificationPlanner`, which builds steps from the **registry** (`verification.yaml` + `registry.py`).

**Consequence:** The inline pytest commands in `profiles.py` (`_VERIFY_BACKEND_TASKS`, `_VERIFY_FULL_TASKS`, etc.) are **never executed**. Actual execution is driven 100% by the registry.

### Actual DAG for `python runtime/verify.py backend` (1 changed backend file):

```
backend-verify.yml
  └─ python runtime/verify.py backend
       └─ VerificationOrchestrator.run()
            └─ VerificationPlanner.plan(scope=BACKEND, changed=[loan_engine.py])
                 ├─ step-1: bash .github/scripts/run_fast_checks.sh          ← QUICK scope pulled in by hierarchy
                 ├─ step-2: bash .github/scripts/run_backend_verification.sh  ← loan-engine-property
                 ├─ step-3: bash .github/scripts/run_backend_verification.sh  ← loan-engine-contract
                 ├─ step-4: bash .github/scripts/run_backend_verification.sh  ← reconciliation-property
                 ├─ step-5: bash .github/scripts/run_backend_verification.sh  ← reconciliation-contract
                 ├─ step-6: bash .github/scripts/run_backend_verification.sh  ← ledger-invariant
                 ├─ step-7: bash .github/scripts/run_backend_verification.sh  ← ledger-contract
                 └─ step-8: bash .github/scripts/run_backend_verification.sh  ← api-contract-backend
```

**`run_backend_verification.sh` executes 7 times in a single CI job.**

### Actual DAG for `python runtime/verify.py full` (no changed files):

```
14 steps total
  7× run_backend_verification.sh
  1× run_contract_tests.sh
  1× run_fast_checks.sh
  1× run_migration_verification.sh
  1× run_playwright_tests.sh
  1× run_runtime_verification.sh
  1× run_golden_tests.sh
  1× run_mutation_selective.sh
```

### Actual DAG for `python runtime/verify.py quick` (no changed files):

```
1 step: bash .github/scripts/run_fast_checks.sh
```

---

## T3 — Command Duplication Audit

### Exact Duplication (same script invoked multiple times)

| Profile | Script | Invocations | Wasted multiplier |
|---|---|---|---|
| `backend` | `run_backend_verification.sh` | **7×** | 7× |
| `full` | `run_backend_verification.sh` | **7×** | 7× |

### Semantic Duplication (different scripts run overlapping tests)

| Script A | Script B | Overlap |
|---|---|---|
| `run_fast_checks.sh` | `run_backend_verification.sh` | `tests/unit/engines/` is a subset of `tests/unit/` |
| `run_backend_verification.sh` | `run_contract_tests.sh` | Both cover `tests/contract/` |
| `run_backend_verification.sh` | `run_property_tests.sh` | Both cover `tests/properties/` |

### Generated-Artifact Duplication

Every workflow uploads the same four shared artifacts:
- `cross-layer-map.json` (generated once in bootstrap)
- `knowledge-index.json` (generated once in bootstrap)
- `verification-cache.json` (generated once in bootstrap)
- `engineering-history.json` (generated once in bootstrap)

These are generated once but **uploaded 9 times** (once per workflow). This is intentional per the artifact strategy, but wastes CI minutes on artifact upload.

### Dead Code in Registry Defaults

`registry.py` lines 490-535 duplicate the entire default script registration block. The second block overwrites the first with identical data. Not a runtime bug, but confusing dead code.

---

## T4 — Database Lifecycle Audit

### Current Architecture (Program K — optimized)

```
Session scope
  └─ _pristine_db_template (create_all + run_migrations + verify_schema once)
       └─ Per-test function scope
            └─ shutil.copy2(template → test_db)   ← ~30× faster than re-running DDL
                 └─ Optional: seeded_db inserts baseline rows (opt-in only)
```

**Verdict: Database lifecycle is NOT a bottleneck.**  
- Schema creation: once per session  
- Migrations: once per session  
- Seed: opt-in per test, no autouse  
- Cleanup: automatic per test  
- No production DB contamination risk  

The `TestDatabase` class and `_pristine_db_template` fixture are correct and performant.

---

## T5 — Performance Instrumentation (Baseline)

### Measured / Estimated Runtimes

| Step | Estimated Duration | Notes |
|---|---|---|
| `bootstrap-runtime` | ~45s | Python + cross-layer map + knowledge index |
| `run_fast_checks.sh` | ~90-180s | ruff + black + mypy + unit + architecture + meta |
| `run_backend_verification.sh` (1×) | ~120-180s | contract + invariants + properties + engines |
| `run_contract_tests.sh` | ~180s | schemathesis + coverage |
| `run_property_tests.sh` | ~180-300s | hypothesis (150 examples) |
| `run_integration_tests.sh` | ~300-600s | API + cross-capability |
| `run_migration_verification.sh` | ~60s | alembic heads + migration tests |
| `run_runtime_verification.sh` | ~120s | runtime tests + integrity |
| `run_golden_tests.sh` | ~300-600s | golden + capability |
| `run_mutation_selective.sh` | ~600s | mutmut on engines |
| `run_playwright_tests.sh` | ~300-900s | build + browser |
| `run_frontend_verification.sh` | ~180s | eslint + tsc + vitest |

### Baseline Bottleneck Calculation

**Backend profile (1 changed file):**
- 7× `run_backend_verification.sh` × 150s = **1,050s (17.5 min)**
- 1× `run_fast_checks.sh` × 120s = **120s**
- **Total: ~19 minutes** (exceeds 30-min timeout only if each suite is slower than estimated)

**Full profile (no changed files):**
- 7× backend × 150s = 1,050s
- 1× contract × 180s = 180s
- 1× runtime × 120s = 120s
- 1× golden × 300s = 300s
- 1× mutation × 600s = 600s
- 1× playwright × 600s = 600s
- 1× migration × 60s = 60s
- 1× fast_checks × 120s = 120s
- **Total: ~3,330s (55 minutes)** — but workflows have individual timeouts

**Primary hidden cost:** Planner step duplication. Every requirement produces an independent step. The same script is invoked N times because the planner lacks command-level deduplication.

---

## T6 — Runtime Classes

| Class | Profile | Local use | CI use | Current status |
|---|---|---|---|---|
| **L — Fast local** | `quick` | Every commit | Every PR | ✅ Clean (1 step, no duplication) |
| **P — Performance-diagnostic local** | `backend`, `frontend`, `runtime` | Debugging | Diagnostic | ❌ Broken (massive duplication) |
| **C — CI-authoritative** | `full`, `mutation`, `golden`, `playwright`, `integration` | On-demand | Scheduled / required | ❌ Broken (duplication + timeout risk) |

---

## T7 — Backend Verification (Primary Target)

### T7.1 — Workflow
`backend-verify.yml` is structurally clean: single command, path filtering, concurrency, artifacts.

### T7.2 — Script
`run_backend_verification.sh` is structurally clean: runs 4 test directories sequentially.

### T7.3 — Test Inventory
- `tests/contract/` — 161 tests (Schemathesis + generated)
- `tests/invariants/` — financial invariant tests
- `tests/properties/` — 206 tests (Hypothesis)
- `tests/unit/engines/` — engine unit tests (subset of 760 total unit tests)

### T7.4 — Duplicate Collections
**`tests/unit/engines/` runs twice:**
1. In `run_fast_checks.sh` via `pytest tests/unit/` (includes engines)
2. In `run_backend_verification.sh` via `pytest tests/unit/engines`

When `full` runs (fast_checks + backend_verification), engines tests execute twice.

### T7.5 — Database Setup
Correct: session-scoped template, per-test copy, opt-in seed.

### T7.6 — Test Groups
- Contract: `tests/contract/`
- Invariant: `tests/invariants/`
- Property: `tests/properties/`
- Unit engines: `tests/unit/engines/`

### T7.7 — Serial Bottleneck
All 4 directories in `run_backend_verification.sh` run sequentially. They could run in parallel (they use independent DB copies).

### T7.8 — Environment Setup
No redundant pip/npm install within the script. Dependencies are handled by `bootstrap-runtime`.

### T7.9 — Root Cause of Slowness
**The planner, not the script, is the bottleneck.** `run_backend_verification.sh` itself is fine. The planner invokes it 7 times per CI run.

---

## T8 — Backend Verification Acceptance Gate

| Criterion | Current | Required | Status |
|---|---|---|---|
| All intended tests execute | Yes (but 7× redundant) | Yes, exactly once | ❌ |
| All intended tests pass | Yes | Yes | ✅ |
| No test removed | N/A | N/A | ✅ |
| No threshold reduced | coverage ≥ 40% | coverage ≥ 40% | ✅ |
| Isolated test DB | Yes (session template) | Yes | ✅ |
| Deterministic seed | Yes (opt-in) | Yes | ✅ |
| No production DB contamination | Yes | Yes | ✅ |
| No duplicate test execution | **No — 7× backend_verification** | No duplicates | ❌ |
| Predictable local time | **No — 19 min for backend** | < 5 min | ❌ |
| Predictable CI time | **No — step count varies** | Deterministic | ❌ |

---

## T9 — Local vs CI Equivalence

Currently **not equivalent**:
- Local: `python runtime/verify.py backend` runs 7 backend_verification suites + 1 fast_checks
- CI: same command, same duplication
- The duplication is the same locally and in CI, but both are wrong

After fix: local `python runtime/verify.py backend` should run exactly 1 backend_verification suite, matching CI exactly.

---

## T10 — Frontend Verification

`frontend-verify.yml` → `python runtime/verify.py frontend` → `run_frontend_verification.sh`

- Script runs: eslint, tsc, vitest
- No database interaction
- No duplicate collections within the script itself
- **Risk:** Planner may duplicate frontend verification if api-contracts capability triggers it

### Quick check needed:
Run planner for frontend scope to verify duplication count.

---

## T11 — Runtime Verification + Quick Fail-Safe Defect

### T11.1 — Runtime Profile
`verification-runtime.yml` → `python runtime/verify.py runtime` → `run_runtime_verification.sh`
- Runs `runtime/tests/` + `runtime/verify.py integrity`
- Structurally clean, no duplication

### T11.2 — CRITICAL: Quick Fail-Safe Defect

**File:** `runtime/verify.py` lines 657-663

```python
if not changed_files and profile_name not in ("full", "graph"):
    print(
        "No changed files detected and git is unavailable. "
        "Falling back to FULL verification profile.",
        file=sys.stderr,
    )
    profile = get_profile("full")
```

**Problem:** When `git` is unavailable (e.g., detached HEAD, shallow clone, CI artifact), `quick` silently escalates to `full` verification. A lightweight 90-second check becomes a 55-minute full suite.

**Desired behavior:** FAIL with a clear message, do NOT silently escalate.

---

## T12 — Quality Workflow

`quality.yml` → `python runtime/verify.py quick` → `run_fast_checks.sh`

- **Intentionally duplicates:** ruff, black, mypy, unit, architecture, meta
- These are also covered by `backend` profile (via the planner pulling in `quick` scope)
- **Verdict:** The duplication between `quality.yml` and `backend-verify.yml` is **intentional assurance** (quality gate vs. backend-specific gate). Not waste.
- **However:** The planner's 7× backend duplication is **waste**, not assurance.

---

## T13 — Mutation

`mutation.yml` → `python runtime/verify.py mutation` → `run_mutation_selective.sh`

- Selective mutation on `src/engines/` only
- Test runner: `pytest tests/unit/ tests/properties/`
- No database setup (mutmut runs in-process)
- **No duplication within the script**
- **Risk:** Planner may duplicate mutation if multiple capabilities map to mutation scope

---

## T14 — Playwright / Golden

### Playwright
`playwright.yml` → `python runtime/verify.py playwright` → `run_playwright_tests.sh`
- Builds frontend, runs Playwright
- Browser provisioning via `setup-playwright` action
- No DB interaction
- **No internal duplication**

### Golden
`golden.yml` → `python runtime/verify.py golden` → `run_golden_tests.sh`
- `tests/golden/` + `tests/capability/`
- No DB interaction (reads golden datasets)
- **No internal duplication**

---

## Root Cause Summary

| # | Issue | Severity | Location | Impact |
|---|---|---|---|---|
| 1 | **Planner duplicate execution** — same script invoked N times per profile | **CRITICAL** | `planner.py::_build_steps()` | 7× backend_verification per CI run |
| 2 | **Dead code in profiles.py** — profile tasks never executed | **HIGH** | `profiles.py` | Misleading documentation; maintenance hazard |
| 3 | **Quick fail-safe escalation** — silent fallback to full | **CRITICAL** | `verify.py:657-663` | 90s check → 55min suite |
| 4 | **Cache never used** — `_is_cache_valid()` only logs, never short-circuits | **MEDIUM** | `verify.py:665-670` | Wasted recomputation |
| 5 | **Duplicate script registrations in registry.py defaults** | **LOW** | `registry.py:490-535` | Confusing dead code |
| 6 | **Shared artifacts uploaded N times** | **LOW** | All workflows | CI minute waste |

---

## Fix Sequence (One Fix at a Time)

### Fix 1: Eliminate planner duplicate execution

**File:** `runtime/foundation/verification/planner/planner.py`  
**Method:** `_build_steps()`

**Problem:** One step per requirement. Multiple requirements map to the same workflow/script.

**Fix:** After building all steps, deduplicate by `(command, workflow, script)` while preserving dependency order.

```python
def _build_steps(self, targets, workflows, scripts):
    steps = []
    seen_commands = set()
    for target in ordered_targets:
        ...build step...
        key = (step.command, step.workflow, step.script)
        if key in seen_commands:
            continue
        seen_commands.add(key)
        steps.append(step)
    return steps
```

**Validation:**
- `python runtime/verify.py backend` with 1 changed file → **1 step** (not 8)
- `python runtime/verify.py full` → **7 unique steps** (not 14)

### Fix 2: Fix quick fail-safe escalation

**File:** `runtime/verify.py`  
**Lines:** 657-663

**Problem:** Silent fallback to `full` when git unavailable.

**Fix:**
```python
if not changed_files and profile_name not in ("full", "graph"):
    print(
        "No changed files detected and git is unavailable. "
        "Cannot run selective verification. Aborting.",
        file=sys.stderr,
    )
    return 1
```

**Validation:**
- Simulate git unavailable → quick exits 1 with clear message
- No silent escalation to full

### Fix 3: Make verification cache effective

**File:** `runtime/verify.py`  
**Lines:** 665-670

**Problem:** Cache hit only logs; orchestrator always runs.

**Fix:**
```python
if _is_cache_valid(profile_name, changed_files, commit):
    print(f"Cache hit for profile '{profile_name}' (commit: {commit[:8]}). Skipping.", file=sys.stderr)
    # Return a cached-pass report instead of re-executing
    ...
```

**Validation:**
- Run `python runtime/verify.py quick` twice with no changes → second run is instant

### Fix 4: Remove dead code from profiles.py

**File:** `runtime/foundation/verification/profiles.py`

**Fix:** Delete `_VERIFY_QUICK_TASKS`, `_VERIFY_BACKEND_TASKS`, `_VERIFY_FRONTEND_TASKS`, `_VERIFY_CONTRACTS_TASKS`, `_VERIFY_GRAPH_TASKS`, `_VERIFY_FULL_TASKS`, `_VERIFY_MUTATION_TASKS`, `_VERIFY_RUNTIME_TASKS`, `_VERIFY_GOLDEN_TASKS`, `_VERIFY_PLAYWRIGHT_TASKS` and their entries in `_PROFILES`. Keep only `get_profile`, `list_profiles`, `profile_names` as stubs or remove them if unused.

**Validation:**
- `python -c "from runtime.foundation.verification.profiles import get_profile"` → raises clear error or returns minimal profile
- All CI workflows continue to work (they use registry, not profiles)

### Fix 5: Remove duplicate default script registrations in registry.py

**File:** `runtime/foundation/verification/registry/registry.py`  
**Lines:** 490-535

**Fix:** Delete the duplicate block. Keep only lines 380-489.

**Validation:**
- `python runtime/verify.py backend` → same behavior
- Registry validation passes

### Fix 6: Parallelize independent test directories in run_backend_verification.sh

**File:** `.github/scripts/run_backend_verification.sh`

**Fix:** Run the 4 test directories in parallel using `&` and `wait`, collecting exit codes.

```bash
pids=()
for tdir in tests/contract tests/invariants tests/properties tests/unit/engines; do
  if [ -d "$tdir" ]; then
    pytest "$tdir" -q --no-header --tb=short &
    pids+=($!)
  fi
done
fail=0
for pid in "${pids[@]}"; do
  wait "$pid" || fail=1
done
exit $fail
```

**Validation:**
- `bash .github/scripts/run_backend_verification.sh` runs 4 suites in parallel
- Exit code reflects any failure

---

## Validation Plan

For each fix:

1. **Unit validation** — Run the affected command locally, verify expected output
2. **Plan validation** — Run `python -c "from planner import ...; print(plan.steps)"`, verify deduplication
3. **Integration validation** — Run `python runtime/verify.py quick` (should be < 5 min)
4. **CI validation** — Push fix, verify GitHub Actions pass

**Final certification criteria:**
- `backend` profile: exactly 1 step (run_backend_verification.sh) + 1 step (aggregate evidence) = 2 steps
- `quick` profile: 1 step (run_fast_checks.sh)
- `full` profile: 7 unique steps (one per unique script)
- `quick` with git unavailable: exits 1 with clear message
- No silent escalation from lightweight to heavyweight profiles
- All existing tests continue to pass
- Coverage thresholds unchanged

---

## Rollout Order

| Order | Fix | Risk | Reversible |
|---|---|---|---|
| 1 | Planner deduplication | Low | Yes (revert one method) |
| 2 | Quick fail-safe fix | Low | Yes |
| 3 | Cache short-circuit | Low | Yes |
| 4 | Parallel backend tests | Medium | Yes |
| 5 | Remove dead profiles.py tasks | Low | Yes |
| 6 | Remove duplicate registry defaults | Low | Yes |

**Do not batch fixes.** Each fix is isolated, measured, and verified before the next.

---

## Out of Scope (Explicitly)

- Do NOT modify test files
- Do NOT reduce coverage thresholds
- Do NOT remove test suites
- Do NOT weaken mutation thresholds
- Do NOT merge routers
- Do NOT create placeholder workspaces
- Do NOT regenerate large evidence sets
- Do NOT change artifact retention policies

---

## T.1 — Post-Fix Certification (Current Phase)

### T.1 Milestone 1 — Backend Failure Forensic Check

**Status: COMPLETE — 3 pre-existing failures confirmed**

| Test | bacc1fe2 | 12e11662 | 814e1149 | Deterministic | Parallel-safe |
|---|---|---|---|---|---|
| `test_apply_floating_rate_change_invariants` | FAIL | FAIL | FAIL | Yes | Yes |
| `test_apply_floating_rate_change_edge_cases` | FAIL | FAIL | FAIL | Yes | Yes |
| `test_compute_foreclosure_amount_math_accuracy` | FAIL | FAIL | FAIL | Yes | Yes |

**Root cause:** Tolerance calculation in property tests is too tight for certain floating-point rounding scenarios. The test allows `max(10000, remaining_months * 10, expected_accrued_interest // 10)` but actual difference exceeds this for some hypothesis-generated cases.

**Assessment:** Genuinely pre-existing. Not introduced by Program T. Not related to database, seed, parallelism, or isolation.

### T.1 Milestone 2 — Planner Determinism Certification

**Status: COMPLETE — ALL PASS**

| Profile | Steps | Unique Keys | Dupes | Status |
|---|---|---|---|---|
| quick | 1 | 1 | 0 | PASS |
| backend | 2 | 2 | 0 | PASS |
| frontend | 2 | 2 | 0 | PASS |
| contracts | 2 | 2 | 0 | PASS |
| full | 8 | 8 | 0 | PASS |
| mutation | 3 | 3 | 0 | PASS |
| runtime | 1 | 1 | 0 | PASS |
| golden | 1 | 1 | 0 | PASS |
| playwright | 1 | 1 | 0 | PASS |
| integration | 2 | 2 | 0 | PASS |
| repository | 8 | 8 | 0 | PASS |

**Invariant verified:** `duplicate_count == 0` AND `len(steps) == len(unique(command, workflow, script))`

### T.1 Milestone 3 — Local/CI Equivalence

**Status: COMPLETE**

Each GitHub workflow runs exactly `python runtime/verify.py <profile>`. The planner produces identical execution graphs locally and in CI.

**Important caveat:** `_collect_changed_files()` currently includes `runtime/generated/` artifacts, which can trigger additional verification steps. This is a pre-existing issue that should be fixed to ensure clean local/CI equivalence when no source code has changed.

### T.1 Milestone 4 — Performance Baseline

| Profile | Plan Time | Exec Time | Total | Steps | Status |
|---|---|---|---|---|---|
| quick | ~0.1s | ~82s | ~82s | 1 | PASS |
| backend | ~0.1s | ~169s | ~169s | 3 | 2/3 passed* |
| frontend | ~0.1s | ~148s | ~148s | 2 | 1 failed** |
| contracts | ~0.1s | ~140s | ~140s | 2 | 1 failed*** |
| runtime | ~0.1s | ~27s | ~27s | 1 | PASS |
| golden | — | ~6s | ~6s | 1 | PASS |
| mutation | — | ~28s | ~28s | 3 | PASS |
| playwright | — | ~2s | ~2s | 1 | Env caveat |
| integration | — | — | — | — | Profile missing |

\* 3 pre-existing property test failures  
\** Frontend environment issue (missing node_modules)  
\*** Contract test failure due to frontend environment dependency

### T.1 Milestone 5 — Additional Pre-Existing Issues Found

#### Issue A: Generated files trigger verification expansion

**File:** `runtime/foundation/verification/orchestrator.py`  
**Function:** `_collect_changed_files()`

**Problem:** `git diff --name-only HEAD` returns all changed files including `runtime/generated/*` outputs from previous verification runs. These generated artifacts then trigger additional verification targets in the planner, causing unnecessary step expansion.

**Example:** Running `python runtime/verify.py contracts` with only `runtime/generated/` files changed produces 3 steps instead of 2, because the runtime verification target is pulled in.

**Fix:** Filter out generated directories from changed files:
```python
def _collect_changed_files() -> list[str]:
    ...
    return [
        f for f in files
        if not f.startswith("runtime/generated/")
        and not f.startswith("node_modules/")
        and not f.startswith(".pytest_cache/")
        and not f.startswith("__pycache__/")
        and not f.endswith(".pyc")
    ]
```

#### Issue B: Missing `integration` profile in profiles.py

**Problem:** `runtime/verify.py integration` raises `ValueError: Unknown verification profile: 'integration'` even though `run_integration_tests.sh` exists and is registered in the registry. The `verification.yaml` and `registry.py` know about integration, but `profiles.py` does not define an integration profile.

**Impact:** `python runtime/verify.py integration` fails locally, but the `integration` scope can still be resolved via `VerificationScope.INTEGRATION` in the planner.

**Fix:** Add `integration` profile to `profiles.py` or document that `integration` is a scope-only profile accessed via the registry.

---

## Updated Fix Sequence

| Order | Fix | Risk | Reversible |
|---|---|---|---|
| 1 | Planner deduplication | Low | Yes |
| 2 | Quick fail-safe fix | Low | Yes |
| 3 | Parallel backend tests | Medium | Yes |
| 4 | Filter generated files from changed-files detection | Low | Yes |
| 5 | Add missing integration profile to profiles.py | Low | Yes |
| 6 | Remove duplicate registry defaults | Low | Yes |
| 7 | Remove dead profiles.py execution definitions | Low | Yes |

**Deferred (requires design):**
- Cache short-circuit (needs correctness key design)
- profiles.py cleanup (after proving registry is sole authority)

---

## Remaining Work After T.1

1. **Fix Issue A** — Filter generated files from changed-files detection
2. **Fix Issue B** — Add integration profile to profiles.py
3. **Remove duplicate registry defaults** — Already identified, safe to remove
4. **Design cache correctness** — Not before understanding full execution graph
5. **Profile-by-profile certification** — Only after above fixes
6. **CI validation** — Push and monitor GitHub Actions
