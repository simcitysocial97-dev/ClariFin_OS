# M9-C47 Audit Gaps and Priorities

**Repository SHA:** 35a31f50a0352e407b0936f50a7d7fe80206c16a
**Generated:** 2026-09-03T18:00:00Z

## P0 — Certification / Correctness Blockers

### GAP-001: MutationOrchestrator Not Wired into verify.py
**Problem:** Two parallel mutation execution paths exist. The verify.py mutation command uses mutation_runner.py:execute_mutation() (M9-C42.5), while the more sophisticated MutationOrchestrator in mutation_execution/orchestrator.py (M9-C44) with parallel execution, sharding, and campaign management is NOT wired in.
**Evidence:** runtime/verify.py:1333-1336 calls run_mutation_cli() from mutation_runner.py. MutationOrchestrator exists but is not called.
**Root Cause:** M9-C44 was developed but never integrated with the verify.py path.
**Affected Architecture:** Mutation execution, certification.
**Affected Capabilities:** mutation-run, mutation-analysis.
**Risk:** HIGH - the M9-C44 features (parallel execution, sharding, workspace management) are not being used.
**Dependencies:** None.
**Required Remediation:** Either wire MutationOrchestrator into verify.py or remove the unused implementation.
**Validation Required:** verify.py mutation should use MutationOrchestrator.
**Acceptance Gate:** mutation --smoke and mutation (full) should use the wired path.

### GAP-002: Progress Document Trust (Case 10)
**Problem:** EXECUTION_PROGRESS.md is human-maintained. There is no automated check that prevents marking a milestone complete without objective evidence. The C47 spec requires machine-verifiable milestone tracking.
**Evidence:** EXECUTION_PROGRESS.md has no automated validation.
**Root Cause:** Progress documents are not part of the verification framework.
**Affected Architecture:** Progress control, certification.
**Risk:** HIGH - an agent can claim completion without objective evidence.
**Dependencies:** None.
**Required Remediation:** Add machine-verifiable milestone tracking with status, scope, command, exit code, artifact, artifact hash, evidence ID, acceptance test, expected result, observed result, review/gate.
**Validation Required:** Automated check that prevents marking complete without evidence.
**Acceptance Gate:** Milestone completion requires objective evidence (exit code, artifact hash, etc.).

### GAP-003: Two MutationResult Dataclasses with Different Vocabularies
**Problem:** mutation_contract.py:MutationResult (6 buckets) and mutation_execution/domain_model.py:MutationResult (10 states) have different vocabularies and are not directly compatible.
**Evidence:** Both files define MutationResult with different fields.
**Root Cause:** Two parallel mutation architectures (M9-C42.5 and M9-C44).
**Affected Architecture:** Mutation result classification.
**Risk:** MEDIUM - the two paths produce different result shapes.
**Dependencies:** GAP-001.
**Required Remediation:** Unify the two MutationResult types.
**Validation Required:** Both paths should produce compatible results.
**Acceptance Gate:** Single MutationResult type used by both paths.

## P1 — Architecture / Repository-Wide Capability Blockers

### GAP-004: Symbol-Level Planning Not Implemented
**Problem:** The planner works at the file level, not the symbol level. The ultimate end state requires symbol-level planning.
**Evidence:** planner.py:382-388 TODO comment: "TODO Program 7: implement graph-based capability resolution. For now, skip endpoint-based capability resolution."
**Root Cause:** Symbol-level planning was deferred.
**Affected Architecture:** Verification planner, blast radius.
**Risk:** MEDIUM - symbol-level changes may not trigger the right verification scope.
**Dependencies:** None.
**Required Remediation:** Implement symbol-level planning using AST analysis.
**Validation Required:** Symbol-level changes should trigger the right verification scope.
**Acceptance Gate:** Symbol-level planning is functional.

### GAP-005: Graph-Based Capability Resolution TODO
**Problem:** Endpoint-based capability resolution is TODO in the planner.
**Evidence:** planner.py:382-388: "TODO Program 7: implement graph-based capability resolution."
**Root Cause:** Graph-based resolution was deferred.
**Affected Architecture:** Verification planner.
**Risk:** MEDIUM - endpoint changes may not trigger the right verification scope.
**Dependencies:** None.
**Required Remediation:** Implement graph-based capability resolution.
**Validation Required:** Endpoint changes should trigger the right verification scope.
**Acceptance Gate:** Graph-based resolution is functional.

### GAP-006: Severity Filtering Not Implemented
**Problem:** The planner does not filter by VerificationRequirement.severity.
**Evidence:** VerificationRequirement has severity field but the planner does not use it for filtering.
**Root Cause:** Severity-based prioritization was deferred.
**Affected Architecture:** Verification planner.
**Risk:** LOW - all requirements are executed regardless of severity.
**Dependencies:** None.
**Required Remediation:** Implement severity-based filtering or prioritization.
**Validation Required:** Critical requirements should be prioritized.
**Acceptance Gate:** Severity-based filtering is functional.

### GAP-007: Two Capability Registries
**Problem:** VerificationRegistry in registry/registry.py and CapabilityContractRegistry in capability_contract.py are two separate registries.
**Evidence:** Both files exist with different purposes.
**Root Cause:** Two separate registries were created.
**Affected Architecture:** Capability registry.
**Risk:** MEDIUM - divergence between the two registries.
**Dependencies:** None.
**Required Remediation:** Unify the two capability registries.
**Validation Required:** Both registries should be consistent.
**Acceptance Gate:** Single capability registry.

### GAP-008: Mutation Engines Not Registered as Capabilities
**Problem:** ENGINE_SELECTION in mutation_contract.py contains 14 engines for mutation testing, but VerificationRegistry only has 10 default capabilities. The mutation engines are not registered as verification capabilities.
**Evidence:** ENGINE_SELECTION has 14 engines, VerificationRegistry has 10 default capabilities.
**Root Cause:** Mutation engines were added without being registered as capabilities.
**Affected Architecture:** Capability registry, mutation.
**Risk:** MEDIUM - mutation engines may not be discoverable through the capability graph.
**Dependencies:** GAP-007.
**Required Remediation:** Register mutation engines as capabilities.
**Validation Required:** All 14 engines should be discoverable.
**Acceptance Gate:** All mutation engines are registered as capabilities.

### GAP-009: Rename/Move Graph Invalidation
**Problem:** Git diff detects renames but graph invalidation is not explicitly implemented.
**Evidence:** Rename scenarios are partially verified in FAILURE_MODE_AUDIT.
**Root Cause:** Graph invalidation for renames was not implemented.
**Affected Architecture:** Blast radius, graph model.
**Risk:** MEDIUM - renamed files may not trigger the right verification scope.
**Dependencies:** None.
**Required Remediation:** Implement rename/move graph invalidation.
**Validation Required:** Renamed files should trigger the right verification scope.
**Acceptance Gate:** Rename graph invalidation is functional.

### GAP-010: Deletion Capability Removal
**Problem:** Deleted files are included in changed_files but capability removal is not explicitly handled.
**Evidence:** Deletion scenarios are partially verified in FAILURE_MODE_AUDIT.
**Root Cause:** Capability removal for deletions was not implemented.
**Affected Architecture:** Capability registry, blast radius.
**Risk:** MEDIUM - deleted capabilities may still be in the graph.
**Dependencies:** None.
**Required Remediation:** Implement deletion capability removal.
**Validation Required:** Deleted capabilities should be removed from the graph.
**Acceptance Gate:** Deletion capability removal is functional.

## P2 — Significant Verification Weaknesses

### GAP-011: Automatic Test Generation Not End-to-End
**Problem:** generation_engine.py, test_generator.py, and strengthening_pipeline.py exist but the end-to-end pipeline (survivor -> diagnosis -> generated test -> execution -> mutant re-execution -> validation -> regression check -> evidence) is NOT verified to operate.
**Evidence:** AUTO_TEST_GENERATION_AUDIT.json.
**Root Cause:** Test generation was partially implemented.
**Affected Architecture:** Test strengthening, mutation.
**Risk:** MEDIUM - the system cannot automatically generate and validate tests.
**Dependencies:** None.
**Required Remediation:** Complete the end-to-end test generation pipeline.
**Validation Required:** Generated tests should be executed and mutants re-executed.
**Acceptance Gate:** End-to-end test generation is functional.

### GAP-012: Frontend Financial Arithmetic Rule Not Enforced
**Problem:** The rule "Frontend must not perform financial arithmetic on monetary values" is documented but the enforcement mechanism (tests, static rules, runtime behavior) is not verified.
**Evidence:** CROSS_LAYER_AUDIT.json.
**Root Cause:** The rule was documented but not enforced.
**Affected Architecture:** Frontend verification.
**Risk:** MEDIUM - financial arithmetic bugs may not be caught.
**Dependencies:** None.
**Required Remediation:** Add static analysis rule or test to enforce the architectural constraint.
**Validation Required:** Frontend code should not perform financial arithmetic.
**Acceptance Gate:** Financial arithmetic rule is enforced.

### GAP-013: Schema Mismatch Fix History Not Documented
**Problem:** The specific loan API response-shape mismatch (backend array vs frontend wrapped object) fix history is not documented.
**Evidence:** CROSS_LAYER_AUDIT.json.
**Root Cause:** Fix history was not documented in this audit.
**Affected Architecture:** Cross-layer verification.
**Risk:** LOW - the API contract integrity gate should catch this.
**Dependencies:** None.
**Required Remediation:** Document the fix history or verify the current state.
**Validation Required:** Current API responses should match frontend expectations.
**Acceptance Gate:** Schema mismatch is fixed or documented as known issue.

### GAP-014: CLI Surface Not Coherent
**Problem:** The CLI surface is extremely large (100+ commands in verify.py, 12 in cli/cli.py). Many commands have overlapping functionality.
**Evidence:** CLI_SURFACE_AUDIT.json.
**Root Cause:** Commands accumulated over time without consolidation.
**Affected Architecture:** CLI surface, operator UX.
**Risk:** LOW - functional but not user-friendly.
**Dependencies:** None.
**Required Remediation:** Consolidate overlapping commands and classify as CANONICAL/ALIAS/COMPATIBILITY/INTERNAL/LEGACY/DUPLICATE/UNREACHABLE.
**Validation Required:** CLI surface should be coherent.
**Acceptance Gate:** CLI surface is consolidated.

## P3 — Quality Improvements

### GAP-015: Dead/Latent Code in Evidence Aggregator
**Problem:** _find_chain_for_failure and _find_dependency_chain are marked OBSOLETE (E-4 defect) but are retained in the code.
**Evidence:** runtime/system/evidence/aggregator.py:53-89, 986-1051.
**Root Cause:** Dead code retained per VEA-3 §0.3 (no opportunistic deletion).
**Affected Architecture:** Evidence aggregation.
**Risk:** LOW - dead code is not called but increases maintenance burden.
**Dependencies:** None.
**Required Remediation:** Remove or clearly mark as deprecated.
**Validation Required:** Dead code should be removed or clearly deprecated.
**Acceptance Gate:** Dead code is removed.

### GAP-016: Coverage Not Freshly Measured
**Problem:** The C47 spec requires fresh coverage measurement without modifying tests. This audit did not re-measure coverage.
**Evidence:** COVERAGE_TRUTH_AUDIT.json.
**Root Cause:** Time constraints.
**Affected Architecture:** Coverage measurement.
**Risk:** LOW - the infrastructure supports fresh measurement.
**Dependencies:** None.
**Required Remediation:** Re-measure coverage in a follow-up audit.
**Validation Required:** Coverage numbers should be current.
**Acceptance Gate:** Coverage is freshly measured.

### GAP-017: Test Quality Not Sampled
**Problem:** The C47 spec requires sampling test quality to classify tests as execution-only/weak/behavioral/invariant/property/contract/integration/E2E/golden/mutation-sensitive/diagnostic/false-positive protection. This audit did not sample test quality.
**Evidence:** C47 spec requirement.
**Root Cause:** Time constraints.
**Affected Architecture:** Test quality.
**Risk:** LOW - the infrastructure supports classification.
**Dependencies:** None.
**Required Remediation:** Sample test quality in a follow-up audit.
**Validation Required:** Test quality is classified.
**Acceptance Gate:** Test quality is sampled.

## P4 — Optimization / Convenience

### GAP-018: Function Audit Not 100% Complete
**Problem:** The C47 spec requires 100% classification of all executable framework functions. This audit covered the canonical execution path but not all 122 framework files.
**Evidence:** FUNCTION_AUDIT.json.
**Root Cause:** Time constraints.
**Affected Architecture:** Framework audit.
**Risk:** LOW - the critical-path functions are classified.
**Dependencies:** None.
**Required Remediation:** Complete the function audit in a follow-up.
**Validation Required:** All functions are classified.
**Acceptance Gate:** 100% function classification.

## Summary

| Priority | Count | Highest Risk |
|----------|-------|--------------|
| P0 | 3 | GAP-001, GAP-002 |
| P1 | 7 | GAP-004, GAP-005 |
| P2 | 4 | GAP-011, GAP-012 |
| P3 | 3 | GAP-015 |
| P4 | 1 | GAP-018 |
