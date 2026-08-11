# VEA-4 Quality Workflow Decision (M4)

**Status:** PARTIAL — modification not proven safe
**Date:** 2026-08-11

---

## 1. Question

Is `quality.yml`'s `verify.py quick` a:
1. strict duplicate
2. subset
3. complementary
4. different-condition execution

of the verification units already executed by applicable ordinary workflows?

---

## 2. Proof

### 2.1 For backend/frontend/runtime pushes that trigger other workflows

M2 proved that `quality.yml` executes a **strict subset** of `backend-verify.yml` and `frontend-verify.yml` for their respective trigger paths. The shared units are IDENTICAL_EXECUTION.

**Evidence:** Run manifests show both workflows execute `run_fast_checks.sh` and `run_runtime_verification.sh` for the same changed files.

### 2.2 For docs/.github/config pushes that do NOT trigger other workflows

`quality.yml` is the **sole verification** for:
- `docs/**` changes
- `.github/**` changes (except `.github/scripts/` is covered by no other workflow)
- Root config file changes (`*.yaml`, `*.yml`, `*.toml`, `*.ini`, `pyproject.toml`, etc.)

For these paths, `verify.py quick` resolves to QUICK scope only and runs `run_fast_checks.sh`. No other workflow executes.

**Evidence:** Path-filter analysis of all 9 workflows shows no other workflow triggers on `docs/**` or `.github/**`.

### 2.3 For runtime-only pushes

`quality.yml` adds `run_fast_checks.sh` (quick checks) that `verification-runtime.yml` does not run. This is **INTENTIONAL_COMPLEMENT**.

---

## 3. Classification

| Trigger condition | quality.yml classification |
|-------------------|---------------------------|
| `backend/**` or `runtime/**` (triggers backend-verify) | SUBSET — strict duplicate of quick-check portion |
| `frontend/**` (triggers frontend-verify) | SUBSET — strict duplicate of quick-check portion |
| `runtime/**` (triggers verification-runtime) | INTENTIONAL_COMPLEMENT — adds quick checks |
| `docs/**`, `.github/**`, config files | UNIQUE — sole verification |
| `frontend/**` on main/develop (triggers playwright) | SUBSET — playwright adds e2e, quality adds quick |

---

## 4. Proposed Modification (NOT IMPLEMENTED)

The smallest possible change would be a **trigger restriction** on `quality.yml` to exclude paths already covered by other workflows:

```yaml
on:
  push:
    branches:
      - "**"
    paths:
      - "docs/**"
      - "*.md"
      - ".github/**"
      - "**/*.yaml"
      - "**/*.yml"
      - "**/*.toml"
      - "**/*.ini"
      - "README*"
      - "CHANGELOG*"
      - "LICENSE*"
  pull_request:
    branches:
      - main
      - develop
    paths:
      - "docs/**"
      - "*.md"
      - ".github/**"
      - "**/*.yaml"
      - "**/*.yml"
      - "**/*.toml"
      - "**/*.ini"
      - "README*"
      - "CHANGELOG*"
      - "LICENSE*"
```

**This modification is NOT SAFE because:**

1. **Branch protection is UNKNOWN** (M3). We cannot prove that `quality.yml` is not a required status check. Removing its trigger for `backend/**` changes could silently reduce required-check coverage.
2. **Path filters are fragile.** Any new workflow added in the future would need to update `quality.yml`'s filters to avoid re-introducing duplication.
3. **The duplication is architectural, not YAML-level.** The planner's scope hierarchy always includes QUICK for non-runtime/golden/playwright profiles. Even with trigger restrictions, `backend-verify.yml` still runs the quick checks internally when it triggers.

---

## 5. Decision

**DO NOT MODIFY `quality.yml`.**

The duplication is proven but not safely removable because:
- `quality.yml` is the sole verification for uncovered paths
- Branch-protection requirements are UNKNOWN
- The root cause is the planner's scope hierarchy, not the workflow YAML

Record the duplication as a known issue for future remediation when branch protection is configured and the planner scope hierarchy is revisited.

---

## 6. Evidence

- `docs/verification/VEA4_EXECUTION_EQUIVALENCE.md` — M2 proof
- `docs/verification/VEA4_BRANCH_PROTECTION.md` — M3 branch-protection status
- Run manifests: `runtime/generated/evidence/run-manifest.json` (quick, backend, frontend profiles)
