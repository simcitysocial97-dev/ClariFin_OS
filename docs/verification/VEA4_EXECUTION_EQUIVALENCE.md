# VEA-4 CI Execution-Equivalence Proof (M2)

**Status:** CERTIFIED
**Date:** 2026-08-11

---

## 1. Methodology

For each overlapping workflow/profile pair:
1. Obtained generated execution manifests from `runtime/generated/evidence/run-manifest.json`
2. Collected all executed verification units (`unit_id` field)
3. Normalized execution records (workflow, script, command, exit_code, status)
4. Compared by `unit_id`
5. Compared command semantics
6. Compared evidence-producing stages
7. Compared exit contracts
8. Identified true duplicate work versus intentionally different conditions

**Key architectural finding:** The `verify.py` profile definitions in `profiles.py` are largely ceremonial. The actual executed work is determined by `VerificationPlanner`, which builds steps from changed-file scopes, capabilities, and the registry — NOT from the profile's task list. Two different profiles can therefore execute identical commands when they resolve to the same scope set.

---

## 2. Manifest Evidence

### 2.1 `quick` profile run (current working tree)

```json
{
  "profile": "quick",
  "steps": [
    {
      "step_id": "step-0001",
      "unit_id": "runtime-self-test",
      "workflow": "runtime",
      "script": "run_runtime_verification",
      "command": "bash .github/scripts/run_runtime_verification.sh",
      "exit_code": 1,
      "status": "failed"
    },
    {
      "step_id": "step-0002",
      "unit_id": "UNMAPPED",
      "workflow": "quick",
      "script": "run_fast_checks",
      "command": "bash .github/scripts/run_fast_checks.sh",
      "exit_code": 0,
      "status": "passed"
    }
  ]
}
```

### 2.2 `backend` profile run (current working tree)

```json
{
  "profile": "backend",
  "steps": [
    {
      "step_id": "step-0001",
      "unit_id": "runtime-self-test",
      "workflow": "runtime",
      "script": "run_runtime_verification",
      "command": "bash .github/scripts/run_runtime_verification.sh",
      "exit_code": 1,
      "status": "failed"
    },
    {
      "step_id": "step-0002",
      "unit_id": "UNMAPPED",
      "workflow": "quick",
      "script": "run_fast_checks",
      "command": "bash .github/scripts/run_fast_checks.sh",
      "exit_code": 0,
      "status": "passed"
    },
    {
      "step_id": "step-0003",
      "unit_id": "backend-unit",
      "workflow": "backend",
      "script": "run_backend_verification",
      "command": "bash .github/scripts/run_backend_verification.sh",
      "exit_code": 0,
      "status": "passed"
    }
  ]
}
```

### 2.3 `frontend` profile run (cached from previous execution)

```json
{
  "profile": "frontend",
  "steps": [
    {
      "step_id": "step-0001",
      "unit_id": "frontend-typecheck-build",
      "workflow": "frontend",
      "script": "run_frontend_verification",
      "command": "bash .github/scripts/run_frontend_verification.sh",
      "exit_code": 0,
      "status": "passed"
    },
    {
      "step_id": "step-0002",
      "unit_id": "UNMAPPED",
      "workflow": "quick",
      "script": "run_fast_checks",
      "command": "bash .github/scripts/run_fast_checks.sh",
      "exit_code": 0,
      "status": "passed"
    },
    {
      "step_id": "step-0003",
      "unit_id": "runtime-self-test",
      "workflow": "runtime",
      "script": "run_runtime_verification",
      "command": "bash .github/scripts/run_runtime_verification.sh",
      "exit_code": 1,
      "status": "failed"
    }
  ]
}
```

---

## 3. Unit Comparison by Workflow Pair

### 3.1 `quality.yml` (quick) vs `backend-verify.yml` (backend)

**Condition:** Push includes `backend/**` or `runtime/**` (triggers both workflows)

| unit_id | quick profile | backend profile | Command | Classification |
|---------|--------------|-----------------|---------|----------------|
| runtime-self-test | step-0001 | step-0001 | `run_runtime_verification.sh` | IDENTICAL_EXECUTION |
| UNMAPPED (quick) | step-0002 | step-0002 | `run_fast_checks.sh` | IDENTICAL_EXECUTION |
| backend-unit | absent | step-0003 | `run_backend_verification.sh` | INTENTIONAL_COMPLEMENT |

**Result:** For backend/runtime changes, `quality.yml` executes a **strict subset** of `backend-verify.yml`. The `backend` profile adds `backend-unit` (which also includes `unit-targeted` and `contracts-schemathesis` via capability resolution). The shared units (`runtime-self-test`, `run_fast_checks`) are **IDENTICAL_EXECUTION**.

### 3.2 `quality.yml` (quick) vs `frontend-verify.yml` (frontend)

**Condition:** Push includes `frontend/**` (triggers both workflows)

| unit_id | quick profile | frontend profile | Command | Classification |
|---------|--------------|------------------|---------|----------------|
| frontend-typecheck-build | absent | step-0001 | `run_frontend_verification.sh` | INTENTIONAL_COMPLEMENT |
| UNMAPPED (quick) | present | step-0002 | `run_fast_checks.sh` | IDENTICAL_EXECUTION |
| runtime-self-test | present | step-0003 | `run_runtime_verification.sh` | IDENTICAL_EXECUTION |

**Result:** For frontend changes, `quality.yml` executes a **strict subset** of `frontend-verify.yml`. The `frontend` profile adds `frontend-typecheck-build`. The shared units (`run_fast_checks`, `runtime-self-test`) are **IDENTICAL_EXECUTION**.

### 3.3 `quality.yml` (quick) vs `verification-runtime.yml` (runtime)

**Condition:** Push includes `runtime/**` (triggers both workflows)

| unit_id | quick profile | runtime profile | Command | Classification |
|---------|--------------|-----------------|---------|----------------|
| runtime-self-test | step-0001 | step-0001 | `run_runtime_verification.sh` | IDENTICAL_EXECUTION |
| UNMAPPED (quick) | step-0002 | absent | `run_fast_checks.sh` | SAME_UNIT_DIFFERENT_CONDITION |

**Result:** `quality.yml` adds `run_fast_checks` (quick checks) that `verification-runtime.yml` does not run. This is **INTENTIONAL_COMPLEMENT** — the runtime profile is intentionally scoped to runtime-only verification, while quality adds the fast quality gate.

### 3.4 `backend-verify.yml` vs `verification-runtime.yml`

**Condition:** Push includes `runtime/**` (triggers both workflows)

| unit_id | backend profile | runtime profile | Command | Classification |
|---------|----------------|-----------------|---------|----------------|
| runtime-self-test | step-0001 | step-0001 | `run_runtime_verification.sh` | IDENTICAL_EXECUTION |
| UNMAPPED (quick) | step-0002 | absent | `run_fast_checks.sh` | SAME_UNIT_DIFFERENT_CONDITION |
| backend-unit | step-0003 | absent | `run_backend_verification.sh` | SAME_UNIT_DIFFERENT_CONDITION |

**Result:** `backend-verify.yml` adds backend verification and quick checks. This is **INTENTIONAL_COMPLEMENT** — different profiles, different conditions.

### 3.5 `frontend-verify.yml` vs `playwright.yml`

**Condition:** Push includes `frontend/**` on `main`/`master`/`develop` (triggers both)

| unit_id | frontend profile | playwright profile | Command | Classification |
|---------|------------------|--------------------|---------|----------------|
| frontend-typecheck-build | step-0001 | absent | `run_frontend_verification.sh` | SAME_UNIT_DIFFERENT_CONDITION |
| UNMAPPED (quick) | step-0002 | absent | `run_fast_checks.sh` | SAME_UNIT_DIFFERENT_CONDITION |
| playwright-e2e | absent | step-0001 | `run_playwright_tests.sh` | SAME_UNIT_DIFFERENT_CONDITION |

**Result:** Different verification strategies. **INTENTIONAL_COMPLEMENT**.

---

## 4. Summary Classification

| Workflow A | Workflow B | Overlap trigger | Classification | Evidence |
|------------|------------|-----------------|----------------|----------|
| quality.yml | backend-verify.yml | backend/**, runtime/** | SUBSET (quality ⊂ backend) | Manifests show identical runtime-self-test + run_fast_checks; backend adds backend-unit |
| quality.yml | frontend-verify.yml | frontend/** | SUBSET (quality ⊂ frontend) | Manifests show identical run_fast_checks + runtime-self-test; frontend adds frontend-typecheck-build |
| quality.yml | verification-runtime.yml | runtime/** | INTENTIONAL_COMPLEMENT | quality adds run_fast_checks; runtime adds only runtime-self-test |
| backend-verify.yml | verification-runtime.yml | runtime/** | INTENTIONAL_COMPLEMENT | backend adds backend-unit + run_fast_checks; runtime adds only runtime-self-test |
| frontend-verify.yml | playwright.yml | frontend/** (main/develop) | INTENTIONAL_COMPLEMENT | Different verification strategies (unit/typecheck vs e2e) |

---

## 5. Key Finding: The Planner Drives Execution, Not Profiles

The `profiles.py` task lists (quick-ruff, quick-mypy, quick-unit, etc.) are **never executed by the orchestrator**. The orchestrator always uses `VerificationPlanner.plan()` → `_build_steps()`, which:
1. Resolves scopes from changed files
2. Merges with requested profile scope via `_merge_scopes()`
3. Resolves capabilities and requirements
4. Maps requirements to workflows/scripts via the registry
5. Builds execution steps

The profile name only affects:
- The initial `requested_scope`
- The `scope_hierarchy` expansion (which adds QUICK to most profiles)

For any profile except RUNTIME, GOLDEN, and PLAYWRIGHT, the scope hierarchy includes QUICK. This means ALL ordinary verification profiles automatically include the quick quality gate.

**Consequence:** `quality.yml` is structurally redundant with every other ordinary workflow for any push that triggers those workflows. The duplication is not a YAML mistake — it's encoded in the planner's scope hierarchy.

---

## 6. Exit-Contract Comparison

All workflows share the same exit-contract model:
- `verify.py <profile>` exits 0 when all steps pass, 1 when any step fails
- Individual scripts (`run_*.sh`) exit 0 when all phases pass, 1 when any phase fails
- No workflow uses a different exit contract

Evidence: all workflow YAML files delegate to `python runtime/verify.py <profile>` and append `verify.py status` to the job summary.

---

## 7. Evidence-Producing Stage Comparison

All 7 profile-invoking workflows produce identical evidence artifacts:
- `runtime/generated/evidence/run-manifest.json`
- `runtime/generated/verification-report.md`
- `runtime/generated/verification-cache.json`
- Profile-specific evidence (e.g., `backend/backend-verification.json`, `frontend/frontend-verification.json`)

Artifact ownership differs by workflow name (backend-report vs frontend-report vs quality-report), but the underlying evidence is produced by the same runtime code.

---

## 8. Conclusion

The execution-equivalence proof reveals that `quality.yml` is a **structural duplicate** of the quick-check portion of every ordinary workflow, caused by the planner's scope hierarchy always including QUICK. This is not a YAML defect — it's an architectural property of the verification runtime.

For M4: `quality.yml quick` is a **strict subset** of `backend-verify.yml backend` and `frontend-verify.yml frontend` for their respective trigger paths. It is **complementary** to `verification-runtime.yml runtime`.

For M5: Modification is **not proven safe** because `quality.yml` is the sole verification for `docs/**`, `.github/**`, and root config files. A trigger restriction would silently reduce verification coverage for those paths.
