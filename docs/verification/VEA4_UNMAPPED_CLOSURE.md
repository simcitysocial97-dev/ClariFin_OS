# VEA-4 UNMAPPED Closure (M7)

**Status:** CERTIFIED
**Date:** 2026-08-11

---

## 1. Scope

Investigate every `UNMAPPED` execution observed during VEA-4 baseline runs.

---

## 2. Observed UNMAPPED Executions

From `runtime/generated/evidence/run-manifest.json` across all profiles:

| Profile | Step | Command | Unit ID | Reason |
|---------|------|---------|---------|--------|
| quick | step-0002 | `bash .github/scripts/run_fast_checks.sh` | UNMAPPED | no UNIT_TO_WORKFLOW mapping decision resolved for the owning registry workflow |
| backend | step-0002 | `bash .github/scripts/run_fast_checks.sh` | UNMAPPED | no UNIT_TO_WORKFLOW mapping decision resolved for the owning registry workflow |
| frontend | step-0002 | `bash .github/scripts/run_fast_checks.sh` | UNMAPPED | no UNIT_TO_WORKFLOW mapping resolved for the owning registry workflow |

---

## 3. Investigation

### 3.1 Does it correspond to a real VerificationUnit?

**NO.** The `run_fast_checks.sh` script runs ruff, black, mypy, pytest, and architecture checks. These are quality gate checks, not domain-specific verification units. There is no `VerificationUnit` entry for "fast checks" in the registry.

### 3.2 Is it intentionally outside the verification-unit model?

**YES.** The `quick` workflow is designed as a fast quality gate that runs on every push. It is intentionally broad and not tied to a specific domain capability. The registry correctly has no mapping for it.

### 3.3 Is mapping safe?

**NOT APPLICABLE.** Mapping would require inventing a VerificationUnit for a generic quality gate, which would:
- Blur the distinction between domain verification and infrastructure checks
- Create a unit that has no specific capability, module, or evidence requirements
- Violate the principle that UNMAPPED should remain UNMAPPED when no unit exists

### 3.4 Classification

| Execution | Classification | Rationale |
|-----------|----------------|-----------|
| quick profile run_fast_checks | INTENTIONALLY_UNMAPPED | General quality gate, no domain unit |
| backend profile run_fast_checks | INTENTIONALLY_UNMAPPED | Same script, same rationale |
| frontend profile run_fast_checks | INTENTIONALLY_UNMAPPED | Same script, same rationale |

---

## 4. Conclusion

All UNMAPPED executions are INTENTIONALLY_UNMAPPED. No mapping defects found. No fixes required. The `quick` workflow correctly executes without a VerificationUnit identity because it serves as a general quality gate rather than a domain-specific verification unit.
