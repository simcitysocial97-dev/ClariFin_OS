# VEA-3 Certification — Evidence Integrity Foundation Hardened

**Status:** CERTIFIED
**Date:** 2026-08-11
**Branch:** `recovery/program-r-forensic-reconstruction`
**Scope:** Preserve and prove the VEA-2 evidence-integrity foundation, replace the E-4
keyword/substring attribution defect with unit-keyed graph traversal, and resolve the
deferred backlog items BL-001, BL-002, BL-003 (E-4), BL-004, BL-005, BL-009.

---

## 1. Certification statement

The VEA-2 evidence-integrity foundation (unit identity spine:
`VerificationUnit.id` → `step.unit_id` + `provenance` → `ExecutionResult.unit_id` +
`provenance` → `run-manifest/v1` → `EvidenceSummary.unit_failures` →
`ObservedFailure` → attribution) is **intact and unchanged in semantics**. The E-4
attribution defect has been **replaced** with a unit-keyed, canonical-graph traversal
that never guesses by substring, never selects the first chain entry, and preserves
`UNKNOWN`/`UNMAPPED`. Every deferred backlog item targeted by VEA-3 is either **fixed
with regression tests** or **evidenced as stale/deferred with a documented rationale**.
The repository is green across backend, runtime, and frontend suites.

---

## 2. Milestone ledger

| ID | Milestone | Status | Evidence |
|----|-----------|--------|----------|
| M0 | Baseline re-certification | CERTIFIED | `docs/verification/VEA3_BASELINE.md` — 443/458 runtime pass, lint baseline 34 established, 9-workflow topology recorded |
| M1 | E-4 causal-attribution design | CERTIFIED | `docs/verification/VEA3_E4_DESIGN.md` — defect located, canonical graph authority identified, traversal specified |
| M2 | E-4 graph-traversal implementation | CERTIFIED | `aggregator.py::_resolve_chain_for_failure` added; legacy `_find_chain_for_failure`/`_find_dependency_chain` retained-but-unused |
| M3 | E-4 negative/mutation tests A–H | CERTIFIED | `test_e4_graph_attribution.py` — 8 tests; first-entry (G) and substring (H) mutants shown to diverge from correct answer |
| M4 | Phase 1.5 verdict preservation | CERTIFIED | `test_diagnose_failures.py` + `test_failure_attribution.py` — `len(attributions)==6`, `in_blast_radius==()`, `outside==6`, `change_is_implicated is False` unchanged |
| M5 | BL-009 planner determinism | CERTIFIED | `planner.py::_resolve_workflows_and_scripts` iterates sorted `capabilities`/`categories`; `TestPlannerDeterminismBL009` runs under 5 hash seeds — byte-identical step order |
| M6 | BL-001 frontend lint | CERTIFIED | `npx eslint .` → **0 errors** (was 34); 23 components fixed via real corrections (no suppression) |
| M7 | BL-005 verification.yaml path sync | CERTIFIED | `verification.yaml` + `registry.py` + `scope.py` module paths synced to `backend/src/engines/*`; `test_verification_module_paths.py` locks it |
| M8 | BL-002 credit-card over-prediction | RESOLVED-STALE | Live blast radius for `loan_engine` change = `loan_engine`/`useLoansCapability`/`loans-view-model` only; `test_loan_change_does_not_reach_credit_card` locks it |
| M9 | BL-004 CI workflow audit | AUDITED | `docs/verification/VEA3_BL004_AUDIT.md` — 9 workflows unchanged; all profiles via `verify.py`; no workflow files modified |
| M10 | BL-006 / BL-007 assessment | DEFERRED | Not in VEA-3 resolution set; remain expansion work, appropriate only post-attribution (which VEA-3 establishes) |
| M11 | Full verification sweep | CERTIFIED | backend 975 passed, runtime 458 passed, frontend 0 lint errors + tsc clean, `verify.py status` valid |
| M12 | Certification | CERTIFIED | this document + `docs/progress.md` updated |

---

## 3. Backlog resolution summary

| ID | Resolution | Notes |
|----|-----------|-------|
| BL-001 | FIXED | 34 → 0 lint errors; genuine React-correctness fixes (mounted→`useSyncExternalStore`, lazy-init, derived state, keyed remount, reduced closures) |
| BL-002 | STALE | Hop (`loan → credit_card` via `GET /report`) absent from normalized graph; over-prediction no longer occurs |
| BL-003 | FIXED | E-4 keyword/substring guessing replaced by unit-keyed graph traversal |
| BL-004 | AUDITED | Topology unchanged; consolidation deferred until execution equivalence proven |
| BL-005 | FIXED | Capability `modules` paths synced to real `backend/src/engines/*` layout |
| BL-006 | DEFERRED | Out of VEA-3 scope (test-generation expansion) |
| BL-007 | DEFERRED | Out of VEA-3 scope (mutation/golden strategy expansion) |
| BL-008 | N/A | Not touched (broad refactor prohibited) |
| BL-009 | FIXED | Deterministic planner step ordering via sorted iteration |

---

## 4. Verification evidence (final sweep)

| Suite | Result |
|-------|--------|
| `backend` unit/capability/contract/invariants | **975 passed** |
| `runtime/tests` (fast, `-k "not slow"`) | **458 passed** |
| `frontend` `npx eslint .` | **0 errors** (0 errors, 1 auto-fixable warning) |
| `frontend` `npx tsc --noEmit` | **0 errors** |
| `python runtime/verify.py status` | **Valid** (profiles: quick, runtime, frontend, contracts) |
| `ruff` on changed Python files | **All checks passed** |
| `mypy` on changed modules | No new errors (pre-existing baseline class in untouch `runtime.py` only) |
| VEA-3-specific tests (E4 + module-paths + planner + aggregator) | **38 passed** |

---

## 5. Identity-spine invariants (re-confirmed)

| Invariant | Status |
|-----------|--------|
| `unit_id` propagates plan → execution → evidence | ✅ |
| `run-manifest/v1` produced | ✅ |
| E-3 unit-keyed joining intact | ✅ |
| E-4 legacy functions untouched-until-replacement, now replaced | ✅ |
| `UNMAPPED` remains visible | ✅ |
| Phase 1.5 attribution verdict preserved | ✅ |
| No `.github/workflows/` changes | ✅ |
| Frontend lint baseline (34) reduced to 0, not suppressed | ✅ |

---

## 6. What changed (files)

**Runtime (Python):**
- `runtime/system/evidence/aggregator.py` — added `_unit_provenance_map`,
  `_resolve_chain_for_failure`, `_canonical_chain_map`, `_engines_for_capability`,
  `_chain_segment`, `_units_for_failure_type`; `_build_attention` now uses the
  graph resolver; legacy E-4 functions marked obsolete (retained).
- `runtime/foundation/verification/planner/planner.py` — BL-009 deterministic
  iteration in `_resolve_workflows_and_scripts`.
- `runtime/foundation/verification/registry/registry.py` — BL-005 module-path sync.
- `runtime/foundation/verification/models/scope.py` — BL-005 `MODULE_CAPABILITIES` sync.
- `runtime/foundation/verification/verification.yaml` — BL-005 module-path sync.
- `runtime/tests/test_e4_graph_attribution.py` — NEW (M3).
- `runtime/tests/test_verification_module_paths.py` — NEW (M7).
- `runtime/tests/test_cross_layer_planner.py` — BL-009 determinism + BL-002 precision.

**Frontend (TypeScript/React):**
- 23 component/hook files corrected for `set-state-in-effect`, `exhaustive-deps`,
  `no-children-prop`, `static-components`, `purity`, `immutability`,
  `no-sync-scripts`, `no-assign-module-variable`.
- `frontend/lib/hooks/use-mounted.ts` — NEW (`useSyncExternalStore`-based mounted hook).

**Docs:**
- `docs/verification/VEA3_BASELINE.md`, `VEA3_E4_DESIGN.md`, `VEA3_BL004_AUDIT.md`,
  this certification.

---

## 7. Known limitations

1. **mypy full-tree baseline** remains at the pre-existing error count; no change
   introduced by VEA-3. The VEA-2 gate ("changed files pass") holds.
2. **BL-006 / BL-007** are explicitly out of VEA-3 scope and remain deferred.
3. **BL-004 consolidation** is deferred to a phase that first proves `unit_id`-keyed
   execution equivalence across workflows (BL-004 prerequisite).
4. **E-4 legacy functions retained** per VEA-2 §0.3 (no opportunistic deletion); they
   are obsolete and no longer on any production path. Their removal is a separate,
   explicitly approved cleanup decision.
5. **`migrations` capability** has no source directory in `backend/src`; its
   `modules` path (`backend/src/migrations`) was intentionally left as-is because
   there is no real source location to sync to (changing it would be speculative).
