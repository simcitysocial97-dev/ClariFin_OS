# VEA-3 Baseline Re-Certification (M0)

**Status:** CERTIFIED
**Date:** 2026-08-11
**Objective:** Prove VEA-2 Phase 2 evidence-integrity foundation is the actual starting point before any VEA-3 modification.

---

## A. Commit / environment

| Item | Value |
|------|-------|
| HEAD commit | `d9638e4f` — "VEA-2 Phase 2: evidence integrity — unit identity spine plan→execution→evidence" |
| Branch | `recovery/program-r-forensic-reconstruction` |
| Python | 3.12.3 (`python3`) |
| Pre-existing git stash observed | `stash@{0}` (pre-existing, unrelated to this session — left untouched) |

---

## B. Command inventory and pass/fail

| Command | Scope | Result |
|---------|-------|--------|
| `python3 -m pytest runtime/tests -q -k "not slow"` | runtime fast suite | **443 passed** (note below) |
| `python3 -m pytest runtime/tests/test_failure_attribution.py runtime/tests/test_cross_layer_planner.py` | Phase 1.5 attribution suite | **25 passed, UNMODIFIED** |
| `python3 -m pytest runtime/tests/test_backend_evidence.py::TestExitCodeContract` | backend exit-contract | **4 passed** |
| `npx eslint .` | frontend lint | **34 errors, 141 warnings** (exact BL-001 composition) |
| `npx tsc --noEmit` | frontend typecheck | **0 errors** |
| `python3 -m ruff check runtime/system/evidence/aggregator.py runtime/foundation/architecture` | ruff (changed-area) | **All checks passed** |
| `python3 -m mypy runtime --explicit-package-bases` | mypy (full tree) | **161 pre-existing errors** (unchanged baseline; see Known Limitations) |
| `ls .github/workflows/*.yml \| wc -l` | CI topology | **9 workflows, unchanged** |

### Note on the single runtime failure observed during first sweep

The first full runtime sweep reported one failure:
`runtime/tests/test_backend_evidence.py::TestExitCodeContract::test_backend_exit_contract_holds_both_directions`.

**Root cause (evidence-backed, not a repo defect):** a leftover untracked probe directory
`backend/tests/invariants/_m4_exit_probe/` from a previous incomplete run of the same test
(the `finally` cleanup block had not removed it, including a `__pycache__`). It contained
`test_m4_probe.py` asserting `assert False`, which contaminated the `invariants` phase so that
Direction 1 (unmodified tree) returned `exit=1` instead of `0`.

`git ls-files` confirmed `_m4_exit_probe/` is **not tracked** — it is a test-harness artifact,
not a repository defect. After removing the orphan directory and re-running, the test passes
**4/4**. The baseline is therefore green; the earlier failure was environmental contamination,
exactly the class of hidden issue the spec warns about, now resolved rather than ignored.

---

## C. Lint baseline (authoritative BL-001)

```
react-hooks/set-state-in-effect   15
react-hooks/exhaustive-deps        8
react/no-children-prop             3
react-hooks/static-components      2
react-hooks/purity                 2
react-hooks/immutability           2
@next/next/no-sync-scripts         1
@next/next/no-assign-module-variable 1
TOTAL                              34
```

Measured via `npx eslint . -f json`: identical rule-for-rule to the certified Phase 2 baseline.
The 3 `react/no-children-prop` errors (the previously-omitted ones) are present and will be
addressed in M6 (BL-001), not before.

---

## D. VEA-2 identity-spine checks

| Invariant | Status |
|-----------|--------|
| 1. Identity spine intact (`VerificationUnit.id` → `step.unit_id` → `result.unit_id` → evidence) | ✅ |
| 2. `run-manifest/v1` produced | ✅ (`runtime/generated/evidence/run-manifest.json`) |
| 3. `unit_id` propagates through execution | ✅ |
| 4. `UNMAPPED` remains visible | ✅ |
| 5. E-3 unit-keyed joining intact (no substring/position matching) | ✅ |
| 6. E-4 legacy functions untouched until Phase 3 replacement | ✅ (`_find_chain_for_failure`, `_find_dependency_chain` still present, not called by new code) |
| 7. Phase 1.5 attribution suite unmodified + passing | ✅ (25 passed) |
| 8. No `.github/workflows/` changes | ✅ (9 files unchanged) |
| 9. Frontend lint baseline is 34, not 31 | ✅ (measured 34, exact composition) |

---

## E. Phase 1.5 regression status

- `test_failure_attribution.py` — 25 tests (combined with `test_cross_layer_planner.py`), **UNMODIFIED, PASSING**.
- The exact specimen verdict (`len(attributions)==6`, `in_blast_radius==()`, `outside_blast_radius==6`, `change_is_implicated is False`) is preserved by `test_diagnose_failures.py::test_adapter_reproduces_phase1_5_verdict_from_artifacts_alone`.

---

## F. Known deferred items (from VEA_BACKLOG.md)

| ID | Item | VEA-3 milestone |
|----|------|-----------------|
| BL-001 | 34 frontend lint errors | M6 |
| BL-002 | credit-card over-prediction hop | M8 |
| BL-003 | E-4 keyword → graph traversal | M1–M4 |
| BL-004 | CI workflow topology audit | M9 |
| BL-005 | `verification.yaml` path sync | M7 |
| BL-006 | Schemathesis/Pynguin expansion | M10 (assessment) |
| BL-007 | Mutation/golden redesign | M10 (assessment) |
| BL-009 | Planner step-ordering non-determinism | M5 |

---

## G. Known limitations / environmental notes

- **mypy full-tree count (161 errors)** is a pre-existing baseline, not introduced by VEA-3.
  The VEA-2 certification gate for mypy was "changed files pass", which still holds. Full-tree
  mypy was never green in this repository and is out of VEA-3 scope unless a touched file
  introduces a new error.
- `python` (bare) is not on PATH; `python3` is used throughout.
- A pre-existing `git stash@{0}` exists from earlier work; left untouched.

---

## H. Gate

Baseline recorded. VEA-2 invariants hold. Proceeding to M1 (E-4 design).
