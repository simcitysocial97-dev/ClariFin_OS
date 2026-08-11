# VEA-4 Workflow Consolidation (M5)

**Status:** BLOCKED — no workflow files modified
**Date:** 2026-08-11

---

## 1. Decision

**NO WORKFLOW CONSOLIDATION PERFORMED.**

M2 proved that `quality.yml` is a structural duplicate of the quick-check portion of `backend-verify.yml` and `frontend-verify.yml` for their respective trigger paths. However:

- **M3 STOP CONDITION:** Branch-protection required checks are UNKNOWN. Modifying any workflow without proving its required-check status is prohibited by VEA-4 governance.
- **M4 finding:** Modification is not proven safe because `quality.yml` is the sole verification for `docs/**`, `.github/**`, and root config files.
- **Root cause:** The duplication is architectural (planner scope hierarchy), not YAML-level. Even with trigger restrictions, the underlying duplication persists.

---

## 2. What Was Considered

| Proposed change | Safety assessment | Decision |
|-----------------|-------------------|----------|
| Add path filters to `quality.yml` | UNKNOWN — branch protection unreadable; would silently drop coverage for some paths | REJECTED |
| Remove `quality.yml` | UNKNOWN — may be a required status check; sole verification for docs/.github | REJECTED |
| Merge `quality.yml` into `backend-verify.yml` | Would change trigger semantics; not proven safe | REJECTED |
| Change planner scope hierarchy to exclude QUICK from non-quick profiles | Architectural change; out of scope for M5 | REJECTED |

---

## 3. Remaining Issue

The duplication identified in M2/M4 remains. It is recorded here as a known issue for future remediation when:
1. Branch protection is configured and readable
2. The planner scope hierarchy is revisited (requires explicit decision, not opportunistic refactor)

---

## 4. Evidence

- `docs/verification/VEA4_EXECUTION_EQUIVALENCE.md`
- `docs/verification/VEA4_BRANCH_PROTECTION.md`
- `docs/verification/VEA4_QUALITY_DECISION.md`
- Zero `.github/workflows/*.yml` files modified (verified: `git status --porcelain .github/workflows/` → empty)
