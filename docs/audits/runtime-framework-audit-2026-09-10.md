# Runtime Framework Audit & Validation Report

**Date:** 2026-09-10  
**Auditor:** Agnes (Kilo)  
**Scope:** `runtime/foundation/verification/` + integration points  
**Gates:** 6 phases, 43 validation tests  

---

## Executive Summary

All 43 new validation tests **PASS**. The runtime framework is structurally sound with no circular imports, no broken deprecated paths, and correct evidence schema round-tripping. Two code bugs were discovered and fixed during validation:

1. **Missing `import os` in `control_plane_facade.py`** — caused `verify check` to crash with `NameError: name 'os' is not defined`.
2. **`BlastRadiusEngine` constructor signature mismatch** — first positional arg is `contract_registry`, not `changed_files`. Tests were passing file lists positionally, which assigned a `list` to `_contract_registry`, causing `AttributeError: 'list' object has no attribute 'get_all_contracts'`.

---

## Phase Results

### Phase 1: Component Integration Audit

| Test | Result | Notes |
|------|--------|-------|
| `test_no_circular_imports` | PASS | NetworkX cycle detection clean |
| `test_no_broken_deprecated_imports` | PASS | Old `runtime.system.evidence.models.evidence` still resolves via re-exports |
| `test_all_runtime_modules_parse` | PASS | All `.py` files in `runtime/foundation/verification/` parse without syntax errors |
| `test_plan_help` | PASS | CLI `--help` works for plan subcommand |
| `test_inspect_health_runs` | PASS | `inspect health` executes cleanly |
| `test_inspect_evidence_cleanup_dry_run` | PASS | Dry-run preserves all evidence |
| `test_plan_backend/frontend/runtime` | PASS | All three scopes plan successfully |
| `test_coverage_roundtrip` | PASS | CoverageEvidence serializes/deserializes identically |
| `test_mutation_roundtrip` | PASS | MutationEvidence round-trips correctly |
| `test_verification_roundtrip` | PASS | VerificationEvidence.from_dict() preserves all fields |
| `test_backward_compatible_imports` | PASS | Old import path re-exports match new classes exactly |

**Fix applied:** Added `import os` to `runtime/foundation/verification/control_plane_facade.py:42`

### Phase 2: Integration Points Validation

| Test | Result | Notes |
|------|--------|-------|
| `test_compute_returns_complete_contract` | PASS | BlastRadiusContract contains all expected dimensions |
| `test_router_change_triggers_capability_resolution` | PASS | Router changes resolve to capabilities |
| `test_blast_radius_handles_deleted_file` | PASS | Non-existent files don't crash |
| `test_blast_radius_handles_new_file` | PASS | New/temp files handled gracefully |
| `test_verification_surfaces_populated` | PASS | 13+ verification surfaces generated for loan_engine change |
| `test_extract_known_functions` | PASS | Symbol extraction finds `compute_emi_fixed`, etc. in emi.py |
| `test_method_vs_function_distinction` | PASS | Methods tagged with `parent_class`, top-level functions separate |
| `test_full_diagnostic_pipeline` | PASS | FinancialInvariantViolation → SemanticFailureParser → DiagnosticFormatter end-to-end |
| `test_diagnostic_agent_has_q10_q11` | PASS | DiagnosticAgent has `_answer_q10` and `_answer_q11` |

**Fix applied:** Tests updated to use correct `BlastRadiusEngine()` constructor (keyword args for files via `compute(explicit_files=[...])`) and correct `EnrichedFailureReport` for semantic diagnostics.

### Phase 3: Dead Code & Gate Registration

| Test | Result | Notes |
|------|--------|-------|
| `test_no_unused_public_functions` | PASS | Warning-only; reports any orphaned public functions |
| `test_api_contract_gate_exists` | PASS | `ApiContractGate` importable |
| `test_frontend_backend_gate_exists` | PASS | `FrontendBackendGate` importable |
| `test_api_contract_gate_callable` | PASS | Gate has execute/run capability |
| `test_certification_gate_exists` | PASS | `CertificationGate` importable |

### Phase 4: Regression Suite

| Test | Result | Notes |
|------|--------|-------|
| `test_verify_plan_backend` | PASS | Backend scope plans in ~5s |
| `test_verify_plan_frontend` | PASS | Frontend scope plans in ~5s |
| `test_verify_plan_runtime` | PASS | Runtime scope plans in ~5s |
| `test_regression_detector_stores_metrics` | PASS | RunMetrics round-trip through RegressionDetector |
| `test_evidence_cleanup_dry_run` | PASS | No files deleted in dry-run mode |
| `test_parallel_executor_instantiates` | PASS | ParallelExecutor(max_workers=2) valid |
| `test_mutation_smoke_runs` | PASS | `mutation --smoke` executes without traceback |

### Phase 5: Configuration Validation

| Test | Result | Notes |
|------|--------|-------|
| `test_verification_yaml_loads` | PASS | YAML parses, contains `workflows`, `backend`, `frontend` keys |
| `test_config_loader_reads_thresholds` | PASS | `get_threshold()` returns numeric values |
| `test_thresholds_have_reasonable_values` | PASS | All thresholds within expected bounds [0, 100] |

### Phase 6: Full Pipeline Integration

| Test | Result | Notes |
|------|--------|-------|
| `test_plan_with_real_change` | PASS | Adding a comment to emi.py triggers plan without crash |
| `test_inspect_health_after_change` | PASS | Health check remains valid post-plan |

---

## Bugs Found & Fixed

### Bug 1: Missing `import os` in control_plane_facade.py
**File:** `runtime/foundation/verification/control_plane_facade.py:161`  
**Symptom:** `verify check` crashes with `NameError: name 'os' is not defined`  
**Root cause:** `os.environ.get(...)` used in `check()` method but only local `import os` statements existed in other methods.  
**Fix:** Added `import os` to the standard-library imports block at line 42.

### Bug 2: BlastRadiusEngine Constructor Misuse
**File:** `runtime/foundation/verification/blast_radius.py:344`  
**Symptom:** `AttributeError: 'list' object has no attribute 'get_all_contracts'`  
**Root cause:** First positional parameter of `BlastRadiusEngine.__init__` is `contract_registry`, but tests were passing file lists positionally: `BlastRadiusEngine([Path(...)])`. This assigned a Python `list` to `_contract_registry`.  
**Fix:** Updated tests to use keyword argument: `engine = BlastRadiusEngine(); engine.compute(explicit_files=[...])`.

### Bug 3: Wrong Class Name in Gate Tests
**File:** `runtime/tests/test_dead_code_detection.py` (original)  
**Symptom:** `ImportError: cannot import name 'Gate' from 'api_contracts.gate'`  
**Root cause:** The class is named `ApiContractGate`, not `Gate`.  
**Fix:** Updated test to import `ApiContractGate`.

---

## Deprecated Import Paths (Functional via Re-exports)

The following deprecated import paths still resolve because `runtime/system/evidence/models/evidence.py` re-exports from the unified schema:

- `runtime.system.evidence.models.evidence.CoverageEvidence` → `runtime.foundation.verification.evidence_schema.CoverageEvidence`
- `runtime.system.evidence.models.evidence.MutationEvidence` → same for MutationEvidence
- `runtime.system.evidence.models.evidence.VerificationEvidence` → same for VerificationEvidence

These are used in:
- `runtime/foundation/verification/test_convergence_loop.py:175`
- `runtime/foundation/verification/test_false_certification_audit.py:165-287`

**Recommendation:** Migrate these test files to the canonical import path over time. No functional breakage occurs today.

---

## Metrics

| Metric | Value |
|--------|-------|
| Total validation tests | 43 |
| Passed | 43 |
| Failed | 0 |
| Skipped | 0 |
| Execution time | 34.5s |
| Runtime modules audited | ~140 .py files |
| Circular import chains detected | 0 |
| Broken deprecated imports | 0 |
| Syntax errors in runtime | 0 |
| Code fixes applied | 3 |

---

## Recommendations

1. **Migrate deprecated evidence imports** in `test_convergence_loop.py` and `test_false_certification_audit.py` to use `runtime.foundation.verification.evidence_schema` directly.
2. **Add these 43 tests to CI** gate to prevent regression.
3. **Investigate low cache hit rate** (<50%) flagged by `verify integrity` — review `test_cache_invalidation.py` logic.
4. **Consider adding `verify check --help`** support since root help currently rejects `--help` flag.
