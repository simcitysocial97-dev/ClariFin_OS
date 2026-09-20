# M9-C64-R2 Runtime Pipeline Attribution & Authority Reconciliation — Progress Record

**Status:** AUTHORITATIVE IMPLEMENTATION IN PROGRESS
**Date:** 2026-09-20
**Branch:** `m9c9-merge-authorization-resolution`
**Base commit:** `8990f3ae16e664d9b0f58737bd4f556bc82f52c9` (same as C64-R)
**Predecessor:** M9-C64-R Runtime Pipeline Forensic Validation
**Predecessor commit:** `8990f3ae16e664d9b0f58737bd4f556bc82f52c9`

## Objective

Remediate the concrete runtime-pipeline defects proven by M9-C64-R and re-run the forensic validation against the real canonical execution path.

Establish the invariant:
```
legitimate source change
    ↓
correct source classification
    ↓
correct symbol attribution
    ↓
correct capability attribution
    ↓
correct architecture / cross-layer attribution
    ↓
correct per-source obligation provenance
    ↓
correct verification tasks
    ↓
canonical execution
    ↓
complete evidence
    ↓
correct outcome
    ↓
correct diagnosis
    ↓
same truth in Platform Console
```

A change must never silently disappear from the verification pipeline.

## Mandatory Starting Conditions (COMPLETED)

1. ✅ Read the complete C64-R evidence set.
2. ✅ Inspected all required artifacts (progress.md, residual-findings.json, canonical-call-chain.json, etc.)
3. ✅ Confirmed current Git state (baseline.json recorded).
4. ✅ Preserved C64-R artifacts as immutable audit evidence (hashes recorded in baseline.json).
5. ✅ Established new C64-R2 progress document (this file).
6. ✅ Recorded exact baseline commit and working-tree state.

## Defects to Remediate

| ID | Category | Location | Description | Severity |
|----|----------|----------|-------------|----------|
| F001 | PIPELINE_CONTRACT_DEFECT | `control_plane_facade.py:895` | `_plan_to_obligations` uses `changed_files[0]` for ALL obligations; per-file provenance lost | HIGH |
| F002 | PIPELINE_CONTRACT_DEFECT | `capability_resolver.py:349-354` | Frontend component paths (`frontend/app/`, `frontend/components/`) not classified as SOURCE_CHANGE | HIGH |
| F003 | DATA_PROVENANCE_DEFECT | `capability_resolver.py:363-380` | Router files (`backend/src/routers/*.py`) not mapped to backend capability contracts | MEDIUM |
| F005 | TEST_DEFECT | `test_large_changeset.py:72` / `symbol_resolver.py` | O(n²) AST walk times out on 15k-line files | MEDIUM |
| F006 | CONFIGURATION_INTEGRITY_DEFECT | `verification.yaml` consumer gap | Framework does not detect config threshold divergence at plan or doctor time | MEDIUM |

## Remediation Plan

### F001 — Per-file obligation provenance
**Required behavior:** Every derived obligation MUST identify the actual source(s) responsible for it.
- Modify `ControlPlaneFacade._plan_to_obligations` to map each task to its originating file(s).
- Use the planner's task capability mapping and the blast-radius provenance to attribute obligations to specific changed files.
- For multi-file obligations, include all causal source paths; primary source must be deterministic.
- Add `source_paths[]` and `primary_source_path` to obligation provenance (reuse existing structures).

### F002 — Frontend source classification
**Required behavior:** Canonical change detector / capability resolver must classify supported frontend source files as legitimate source changes.
- Add `frontend/app/**/*.ts`, `frontend/app/**/*.tsx`, `frontend/components/**/*.ts`, `frontend/components/**/*.tsx`, `frontend/lib/**/*.ts`, `frontend/lib/**/*.tsx`, `frontend/hooks/**/*.ts`, `frontend/hooks/**/*.tsx` to SOURCE_CHANGE classification in `capability_resolver.py`.
- Ensure frontend capability discovery and symbol resolution are used.
- Frontend-only capability → frontend obligation; frontend hook mapped to backend → cross-layer obligation.

### F003 — Router-to-capability authority reconciliation
**Required behavior:** Resolver must consume the existing canonical architecture/cross-layer truth.
- For engine-owned backend router: router → endpoint → capability → engine → verification obligation.
- For platform router: platform router → platform endpoint → platform capability / boundary → platform verification obligation.
- Do not assign engine ownership to `platform.py`.
- Use `cross_layer_graph.py` and contract registry as authoritative source.
- If graph cannot resolve a router → explicit `ROUTER_UNMAPPED` state.

### F005 — Large-file performance boundary
**Action:** Run existing large-file scenario. Determine if:
1. Supported maximum source size exists, or
2. Algorithmic defect exists.
- If O(n²) AST behavior is objectively unacceptable for supported repository file → fix symbol extraction algorithm using existing resolver architecture.
- If hard boundary is genuinely intentional → document and enforce explicitly through diagnostics.
- Result must be one of: FIXED, PROVEN_SUPPORTED_BOUNDARY, PROVEN_EXTERNAL_BOUNDARY.

### F006 — Configuration divergence detection
**Required behavior:** Implement smallest possible integrity check to detect configuration threshold divergence.
- Doctor/integrity surface must identify when executable verification configuration and policy thresholds disagree.
- States: CONSISTENT, DIVERGED, UNKNOWN.
- Do not hard-code current threshold values; use existing canonical configuration authority (`config_loader.py`).
- Add negative tests demonstrating intentional temporary divergence is detected.
- Restore configuration after test.

## Required Tests (to be created/extended)

### F001 Tests
- F001-A: Two changed backend files producing different obligations retain separate provenance.
- F001-B: Three changed files producing a shared cross-layer obligation retain all causal source paths.
- F001-C: Reordering `changed_files` does NOT change obligation provenance.
- F001-D: Single-file behavior remains unchanged.
- F001-E: No obligation references a source path that did not participate in its derivation.
- F001-F: Identity continuity remains deterministic.

### F002 Tests
- F002-A: `frontend/app/...tsx` change → frontend capability.
- F002-B: `frontend/components/...tsx` change → frontend capability.
- F002-C: frontend hook change → frontend capability.
- F002-D: frontend-only capability → frontend obligation.
- F002-E: frontend hook mapped to backend → cross-layer obligation.
- F002-F: Platform Console frontend change → platform capability / platform-boundary obligation.
- F002-G: Unsupported/non-source frontend asset remains correctly classified as non-source.

### F003 Tests
- F003-A: Engine-owned router → expected capability.
- F003-B: Router endpoint → correct capability.
- F003-C: Router → engine relationship preserved.
- F003-D: Platform router → platform boundary, zero engine ownership.
- F003-E: Unknown router → explicit unmapped diagnosis.
- F003-F: Router change cannot silently collapse to generic `api-contracts` when canonical capability relationship exists.

### F006 Tests
- Configuration divergence detection with intentional threshold change (e.g., `coverage_threshold: 999`).
- Negative test: framework detects DIVERGED state.
- Restore configuration after test.

### F005 Tests
- Large file performance test with 15k-line file.
- Measure actual timings; record disposition.

## Canonical Pipeline Invariants (to prove after remediation)

I1–I10 as specified in the objective.

## Mandatory Real-World Scenarios (Re-run C64-R scenarios after remediation)

1. backend engine source change
2. backend router change
3. frontend hook change
4. frontend component change
5. frontend app route/page change
6. Platform Console frontend change
7. frontend/backend cross-layer change
8. platform boundary change
9. unmapped file
10. controlled verification failure
11. controlled timeout
12. SIGINT interruption
13. authority fault
14. evidence fault
15. configuration fault
16. artifact freshness fault
17. multi-file heterogeneous change
18. reordered equivalent multi-file change
19. large-file change
20. real repository change

All must execute through `python -m runtime.verify check` or canonical `run` path.

## Negative Testing

For each repaired transition, deliberately inject invalid inputs:
- frontend path with no resolver result
- router absent from architecture graph
- obligation without source provenance
- duplicate source paths
- missing capability
- missing obligation
- missing task
- missing evidence
- stale artifact
- mismatched run identity
- configuration threshold divergence

Framework must fail diagnostically rather than silently continue.

## Identity Continuity

Prove the full identity chain from commit → run_id → change_id → source_path → symbol_id → capability_id → architecture_id → obligation_id → task_id → execution_id → evidence_id → outcome → diagnosis.

For multi-file changes, prove source provenance preserved independently for each causal path.

## No Second Truth System

C64-R2 instrumentation must remain diagnostic only. No second planner, executor, evidence store, history store, capability graph, router registry, frontend dependency graph.

## Regression Requirements

Before final certification, existing certified regressions (C58, O-5-R2, C60, C61, C62, C63) must remain valid.
Run relevant framework tests plus frontend capability discovery, cross-layer graph, endpoint normalization, architecture provider, obligation planner, execution orchestrator, observability, framework integrity, platform API, Platform Console, C64-R forensic scenarios.

## Static Validation

Validate modified source with repository's canonical tooling. New errors introduced by C64-R2 are blockers; pre-existing errors must remain traceable.

## Performance Validation

Measure: plan generation, symbol extraction, capability resolution, cross-layer resolution, obligation derivation, complete `verify check`, large-file behavior, multi-file behavior. Record actual timings.

## Final Residual Ledger

Produce final ledger with every C64-R finding dispositioned as: FIXED, INTENTIONALLY_RETAINED, PROVEN_NON_DEFECT, PROVEN_SUPPORTED_BOUNDARY, EXTERNAL_BOUNDARY, FALSE_POSITIVE, OBSOLETE_AND_REMOVED, BLOCKED. DEFERRED prohibited.

## Mandatory Certification Gates (G1–G23)

All 23 gates must be true for certification.

## Final Certification Question

Answer with execution evidence: "If a developer makes a legitimate arbitrary change... will the canonical ClariFin_OS verification framework deterministically discover the change... without silently dropping the change or substituting an unrelated verification task?"

## Required Final Artifacts

Create in `runtime/generated/m9-c64-r2-runtime-pipeline-attribution-reconciliation/`:
- progress.md (this file)
- baseline.json
- remediation-ledger.json
- canonical-call-chain.json
- scenario-matrix.json
- transition-contracts.json
- identity-continuity.json
- obligation-reconciliation.json
- execution-reconciliation.json
- evidence-reconciliation.json
- outcome-reconciliation.json
- diagnosis-reconciliation.json
- console-reconciliation.json
- configuration-integrity.json
- performance-results.json
- negative-contract-testing.json
- residual-findings.json
- final-certification.md

Preserve original C64-R directory unchanged.

## Execution Discipline

Do not: start another broad audit, redesign verification framework, add another planner/executor/graph, optimize mutation/coverage scores, perform repository-wide Ruff/mypy cleanup, modify financial-domain behavior, modify database, modify C50 architecture, redesign Platform Console, remove legacy components merely because they exist.

Fix proven defects, prove through real canonical pipeline, re-run complete forensic validation.

## Current Status

**Phase 0 — Baseline & Setup:** COMPLETED
**Phase 1 — F001 Implementation:** PENDING
**Phase 2 — F002 Implementation:** PENDING
**Phase 3 — F003 Implementation:** PENDING
**Phase 4 — F005 Disposition:** PENDING
**Phase 5 — F006 Implementation:** PENDING
**Phase 6 — Test Implementation:** PENDING
**Phase 7 — Canonical Pipeline Validation:** PENDING
**Phase 8 — Artifact Generation & Certification:** PENDING

---

*Next update after F001 implementation.*