# RUNTIME FRAMEWORK DEEP-DIVE AUDIT
Date: 2026-09-08
Branch: m9c9-merge-authorization-resolution
Repository: /home/vasantha/AI-Projects/ClariFin_OS
Total runtime LOC: 162,932 lines across 503 Python files

---

## SECTION 1: STRUCTURE & INVENTORY

### Top-level directories under runtime/:
- `runtime/foundation/` — core framework (verification, architecture, audit, integrity, intelligence, knowledge, repository, workspace)
- `runtime/platform/` — AI platform (ai/, api/, cache.py, diagnostics/)
- `runtime/system/` — system services (command/, context/, evidence/, financial/, graph/, intelligence/, observability/, timeline/)
- `runtime/generated/` — evidence artifacts (massive: ~400+ JSON files, audit reports, snapshots)
- `runtime/tests/` — 107 test files
- `runtime/verify.py` — thin compatibility shim (351 lines)
- `runtime/VERSION` — v1.0.0, STABLE
- `runtime/program16_analysis.py` — 66,362 lines (single largest file, likely auto-generated)
- `runtime/analyze_*.py` — 10 analysis scripts (analyze_architecture, analyze_artifacts, analyze_engine_normalization, analyze_engine_topology, analyze_execution, analyze_gap, analyze_knowledge, analyze_ownership, ARCHITECTURE-mutation.md)

### 30 Largest Python Files:
1. 2,662 runtime/foundation/verification/workflow_convergence.py
2. 2,280 runtime/foundation/verification/executor_pipeline.py
3. 2,108 runtime/foundation/verification/execution_orchestrator.py
4. 1,749 runtime/program16_analysis.py
5. 1,510 runtime/foundation/verification/ci_evidence.py
6. 1,388 runtime/foundation/verification/convergence_pipeline.py
7. 1,302 runtime/foundation/verification/planner/planner.py
8. 1,295 runtime/foundation/verification/api_contracts/c30_certification.py
9. 1,263 runtime/tests/test_m9_c50_stop_gate9_failure_modes.py
10. 1,262 runtime/tests/audit_final_freeze.py
11. 1,230 runtime/foundation/verification/registry/registry.py
12. 1,215 runtime/foundation/verification/control_plane_facade.py
13. 1,199 runtime/foundation/verification/orchestrator.py
14. 1,178 runtime/tests/test_m9_c54.py
15. 1,145 runtime/foundation/verification/capability_catalog_data.py
16. 1,143 runtime/foundation/verification/blast_radius.py
17. 1,085 runtime/system/evidence/aggregator.py
18. 1,084 runtime/foundation/verification/mutation_runner.py
19. 1,072 runtime/tests/test_m9_c55.py
20. 1,065 runtime/tests/test_orchestrator.py
21. 1,042 runtime/foundation/audit/artifact_ownership.py
22. 1,035 runtime/tests/test_platform_api_phase1.py
23. 1,032 runtime/foundation/verification/forensic_cli.py
24. 1,008 runtime/tests/test_m9c57_verification_self_contract.py
25. 1,003 runtime/foundation/verification/capability_contract.py
26. 989 runtime/foundation/verification/cli_capability_matrix.py
27. 982 runtime/foundation/integrity/rules.py
28. 968 runtime/foundation/verification/diagnostic_agent.py
29. 938 runtime/foundation/verification/evidence_reuse.py
30. 905 runtime/foundation/architecture/provider.py

### Directory LOC Summary:
- runtime/foundation/verification/ — ~120K lines (the dominant subsystem)
- runtime/foundation/audit/ — ~20K lines
- runtime/foundation/repository/ — ~15K lines
- runtime/foundation/intelligence/ — ~12K lines
- runtime/foundation/architecture/ — ~10K lines
- runtime/foundation/integrity/ — ~9K lines
- runtime/foundation/knowledge/ — ~8K lines
- runtime/foundation/workspace/ — ~6K lines
- runtime/platform/ai/ — ~12K lines
- runtime/platform/api/ — ~10K lines
- runtime/system/ — ~8K lines
- runtime/tests/ — ~25K lines
- runtime/generated/ — evidence artifacts (not source code)

---

## SECTION 2: ENTRY POINTS & ORCHESTRATION

### 2.1 verify.py — Thin Compatibility Shim (351 lines)
- Path: `runtime/verify.py`
- All operator/AI commands flow through `runtime/foundation/verification/control_plane_facade.main()` (canonical_main)
- Canonical execution contract: `python -m runtime.verify <command>` from repo root
- Direct script execution (`python runtime/verify.py`) is FORBIDDEN — it shadows stdlib `platform` with `runtime/platform`
- Legacy commands (~97 tokens) routed through canonical control plane with deprecation warnings
- Outcome vocabulary (closed): passed | failed | blocked | interrupted | completed | unknown
- Maps orchestrator FinalDecision → status: certified→passed, diagnostic→failed, not_certifiable→failed, infrastructure_blocked→blocked, timeout_blocked→blocked, validation_blocked→blocked, awaiting_authorization→blocked, interrupted→interrupted
- Records verification events via EngineeringEventStore + LocalMetricsRepository (RunRecord)

### 2.2 Canonical CLI Surface (9 top-level commands)
Defined in `runtime/foundation/verification/canonical_control_plane.py`:
1. `verify check` — primary verification entrypoint
2. `verify plan` — plan-only mode (no execution)
3. `verify run` — execute an explicit plan
4. `verify diagnose` — failure/survivor diagnostic
5. `verify strengthen` — test-strengthening control plane
6. `verify inspect` — read-only inspection (capabilities/evidence/plan/mutation/workflows/health)
7. `verify certify` — certification (evidence-gated)
8. `verify ci` — CI orchestration/reconciliation
9. `verify doctor` — framework health/integrity

### 2.3 Legacy CLI Commands (from cli/cli.py)
- `verify plan --file --capability --endpoint --scope --output --table`
- `verify scope <scope>`
- `verify capability <capability>`
- `verify repository`
- `verify affected --file --capability --endpoint --scope`
- `verify graph`
- `verify affected-graph`
- `verify help`
- `verify version`

### 2.4 CI Workflow Integration
13 workflow files in `.github/workflows/`:
- `verification-runtime.yml` — triggers on push/PR for runtime/**, backend/src/engines/**, routers/**, mappers/**; runs `python -m runtime.verify runtime`
- `backend-verify.yml` — runs `python -m runtime.verify backend`
- `frontend-verify.yml` — runs `python -m runtime.verify frontend`
- `api-contracts.yml` — runs `python -m runtime.verify api-contracts`
- `mutation.yml` — runs `python -m runtime.verify mutation --smoke` then `python -m runtime.verify mutation` (80% gate)
- `golden.yml`, `playwright.yml`, `quality.yml`, `security-codeql.yml`, `dependency-update.yml`, `release.yml`, `verification-reconcile.yml`, `m9-forensic-diagnostic-lab.yml`

All workflows use `.github/actions/bootstrap-runtime` and `.github/actions/setup-node-runtime`, then `python -m runtime.verify <command>`, then upload artifacts, then `python -m runtime.verify status >> $GITHUB_STEP_SUMMARY`.

### 2.5 Module Dependency Graph (internal imports only)
- `verify.py` → `control_plane_facade.main()`
- `control_plane_facade.py` → `canonical_control_plane`, `certification`, `control_plane`, `evidence_planner`, `execution_orchestrator`, `measurement_truth_integration`, `obligation`, `intelligence`
- `orchestrator.py` → `executor`, `failure_report`, `models`, `planner`, `profiles`, `registry`
- `planner/planner.py` → `repository.graph.graph_service`, `models`, `registry`
- `executor_pipeline.py` → `env`, `evidence_planner`, `evidence_reuse`, `mutation_contract`, `mutation_runner`, `executor`, `failure_report`, `models`, `registry`
- `execution_orchestrator.py` → `capability_contract`, `capability_resolver`, `control_plane`, `evidence_planner`, `evidence_reuse`, `graph_model`, `measurement_truth`, `planner`, `obligation`, `registry`, `strengthening`, `command_inventory`, `change_surface`, `shared_impact`, `blast_radius`
- `blast_radius.py` → `capability_contract`, `capability_resolver`, `change_surface`, `command_inventory`, `evidence_reuse`, `shared_impact`
- `mutation_runner.py` → `env`, `measurement_truth`, `mutation_contract`, `survivor_catalog`, `survivor_intel`
- `diagnostic_agent.py` → `evidence_planner`, `evidence_reuse`, `executor_pipeline`, `measurement_truth`, `reconciliation`
- `tier.py` → `intelligence.platform.blast`, `intelligence.platform.change`, `intelligence.platform.optimizer`, `orchestrator`
- `profiles.py` → `models`
- `cache.py` → standalone (no internal deps)
- `registry/registry.py` → `models`, `yaml`
- `control_plane.py` → `capability_contract`, `capability_resolver`, `evidence_planner`, `evidence_reuse`, `graph_model`, `measurement_truth`, `planner`
- `certification.py` → `route_authority`
- `obligation.py` → standalone (pure dataclasses)
- `capability_contract.py` → `measurement_truth`, `models`
- `canonical_control_plane.py` → standalone (CLI tree definition)
- `env.py` → standalone (environment resolution)

---

## SECTION 3: EVIDENCE & ARTIFACTS

### 3.1 Evidence/Artifact Directories
- `runtime/generated/` — primary evidence root (massive: ~400+ JSON files)
- `runtime/generated/m9-c49/` — execution logs, plans, reports
- `runtime/generated/m9-c50/` — stabilization, operational runs, convergence
- `runtime/generated/m9-c51/` through `m9-c57/` — milestone evidence
- `runtime/generated/evidence/` — API contracts, backend, frontend evidence
- `runtime/generated/execution/` — execution results
- `runtime/generated/ai-runs/`, `ai-memory/`, `ai-context-packs/`
- `runtime/generated/repository/` — index.json, migration DAG
- `runtime/generated/platform/` — snapshot.json
- `backend/tests/generated/mutation/` — mutation testing evidence

### 3.2 Evidence Dataclass Definitions (15+ classes)
**Foundation layer:**
- `VerificationEvidence` (models/model.py:179) — step_id, target_id, type, content, timestamp, status, metadata
- `ExecutionEvidence` (reconciliation.py:437) — canonical execution evidence
- `CIEvidenceRecord` (ci_evidence.py:85) — CI evidence record
- `SurvivorEvidence` (strengthening.py:69) — mutation survivor evidence
- `Evidence` (milestone_state.py:202) — milestone evidence
- `EvidenceRef` (obligation.py:131) — reference to evidence
- `EvidenceIntegrityReport` (evidence_integrity.py:52) — integrity report
- `EvidenceDisposition` (blast_radius.py:103) — enum for evidence disposition
- `EvidenceInvalidation` (blast_radius.py:174) — invalidation record
- `EvidenceClassification` (measurement_truth.py:70) — AUTHORITATIVE | DERIVED
- `ContractEvidence` (api_schema_governance.py:46) — contract evidence
- `EvidenceAwarePlan` (evidence_planner.py:119) — evidence-aware plan
- `EvidenceContractEntry` (workflow_convergence.py:674) — workflow evidence contract

**System layer:**
- `CoverageEvidence` (system/evidence/models/evidence.py:12, system/evidence/api.py:18)
- `MutationEvidence` (system/evidence/models/evidence.py:30, system/evidence/api.py:50)
- `TestResultEvidence` (system/evidence/models/evidence.py:51)
- `ContractEvidence` (system/evidence/models/evidence.py:70)
- `VerificationEvidence` (system/evidence/models/evidence.py:87)
- `EvidenceCollectionResult` (system/evidence/models/evidence.py:140)
- `EvidenceArtifact` (system/evidence/collectors/base.py:14)
- `EvidenceSummary` (system/evidence/aggregator.py:93)

**Platform API contracts:**
- `EvidenceListItem`, `EvidenceListData`, `EvidenceListEnvelope`, `EvidenceDetailData`, `EvidenceDetailEnvelope`, `EvidenceCompareData`, `EvidenceCompareEnvelope` (platform/api/contracts/evidence.py)

### 3.3 Evidence Schema Versioning
- `DIAGNOSTIC_REPORT_SCHEMA = "m9-diagnostic-report/v1"` (diagnostic_agent.py:47)
- `CONVERGENCE_SCHEMA = "m9-c56-convergence/v1"` (convergence_pipeline.py:35)
- `CertificationReport.schema = "m9-c52-certification/v1"` (certification.py:38)
- `MutationResult` — no explicit schema version field; uses run_id + repository_sha + tree_sha for identity
- Version policy in runtime/VERSION: v1.0.x = bug fixes only; v1.1 = backwards-compatible additions; v2.0 = breaking changes

### 3.4 Artifact Writing Locations
- `runtime/foundation/verification/executor_pipeline.py` — writes ExecutionEvidence records
- `runtime/foundation/verification/mutation_runner.py` — writes mutation-summary.json, measurement-truth records, survivor catalogs, survivor intel
- `runtime/foundation/verification/certification.py` — writes certification reports
- `runtime/foundation/verification/evidence_reuse.py` — writes population snapshots, component measurements
- `runtime/foundation/verification/cache.py` — writes verification-cache.json
- `runtime/system/evidence/collectors/` — CoverageCollector, MutationCollector, TestResultCollector, ContractCollector, PropertyTestCollector
- `runtime/system/evidence/ingestion/pipeline.py` — EvidenceIngestionPipeline
- `runtime/system/evidence/aggregator.py` — EvidenceAggregator, EvidenceSummary

---

## SECTION 4: VERIFICATION PIPELINE

### 4.1 Tier System (tier.py — 493 lines)
Three verification tiers:
- **Tier 1 (LOCAL)**: developer working-tree delta (staged + unstaged + untracked). NEVER diffs against origin/main/merge-base.
- **Tier 2 (PR)**: actual PR base/diff (GITHUB_BASE_REF or explicit override)
- **Tier 3 (DEEP)**: explicit full-system execution. Not change-scoped; mutation, golden, E2E and performance selected regardless of diff.

Critical invariant: every unit in UNIT_CATALOG appears as either `selected` or `excluded` with machine-readable reason. 10 canonical units:
unit-targeted, backend-unit, backend-integration, contracts-schemathesis, frontend-unit, frontend-typecheck-build, playwright-e2e, runtime-self-test, mutation-run, golden-regression

### 4.2 Verification Profiles (profiles.py — 587 lines)
Immutable profiles that expand into deterministic tasks. Profile aliases:
- `verify quick` — ruff, black, mypy, unit tests
- `verify backend` — backend verification suite
- `verify frontend` — frontend verification suite
- `verify contracts` — schemathesis contract tests
- `verify graph` — repository graph verification
- `verify full` — complete verification suite
- `verify runtime` — engineering runtime self-verification
- `verify golden` — golden regression tests
- `verify playwright` — playwright E2E tests

Configuration authority split (O-2):
- `profiles.py` OWNS the task-list execution surface (alias profiles)
- `verification.yaml` OWNS the planner/registry surface (capability-driven execution)
- Reconciliation tested by `test_m9c57_verification_self_contract.py`

### 4.3 Verification YAML Config (verification.yaml — 373 lines, 13KB)
12 canonical workflows defined:
quick, backend, frontend, contracts, property, mutation, integration, migration, repository, full, runtime, golden

Configuration:
- backend coverage_threshold: 40, mutation_threshold: 60
- frontend enabled: true
- infrastructure: python 3.12, node 24, cache_strategy: dependency-hash

### 4.4 Verification Registry (registry/registry.py — 1,230 lines)
Loads verification.yaml. Key dataclasses:
- `VerificationWorkflow` — id, name, description, category, scope, command, script, capabilities, scopes, dependencies
- `VerificationScript` — id, name, path, description, category, scope, capabilities
- `VerificationCapability` — id, name, description, category, scopes, requirements, workflows, scripts, modules
- `VerificationRequirement` — id, category, severity, description, scope, module, capability, workflow, script, evidence_required, depends_on, tags, metadata

Key constants: `UNMAPPED = "UNMAPPED"` — sentinel for units with no mapping decision. Explicit enumerated table join between intelligence pipeline units and orchestrator pipeline workflows. Many-to-one mapping permitted.

### 4.5 Test Selection & Execution Pipeline
**Planning flow:**
1. `ChangeDetector` (intelligence) → detects changed files
2. `CapabilityResolver` (capability_resolver.py) → classifies changes (TEST_CHANGE, CONFIG_CHANGE, INFRASTRUCTURE_CHANGE, DOCUMENTATION_CHANGE, SOURCE_CHANGE, UNKNOWN)
3. `BlastRadius` (blast_radius.py) → computes impact (DIRECTLY_AFFECTED, TRANSITIVELY_AFFECTED, SHARED_INFRASTRUCTURE_AFFECTED, etc.)
4. `ControlPlanePlanner` (control_plane.py) → produces ControlPlanePlan
5. `EvidenceAwarePlanner` (evidence_planner.py) → produces EvidenceAwarePlan with reuse decisions
6. `ExecutionOrchestrator` (execution_orchestrator.py) → executes tasks, produces ExecutionReport

**Execution flow:**
- `executor.py` (319 lines) — subprocess execution with retry, timeout, process-group cancellation, streaming output
- `executor_pipeline.py` (2,280 lines) — executable verification plan, task adapters, mutation executor, evidence capture, reconciliation, scope enforcement, failure classification
- `execution_orchestrator.py` (2,108 lines) — turns C48 plan into executable pipeline, stopping rules, fingerprint validation

**CompletionState vocabulary (closed):** PASS, FAILED, TIMEOUT, INFRASTRUCTURE, EVIDENCE, SCOPE, CONFIGURATION, CERTIFICATION, AUTHORIZATION_REQUIRED, REUSED, SKIPPED

**Stopping rules:**
- Mandatory tasks all PASS/REUSED → skip escalation, declare final decision
- Any mandatory FAILED → run diagnostic; do not auto-execute escalation
- TIMEOUT/INFRASTRUCTURE/SCOPE/CONFIGURATION/CERTIFICATION failures never convert to PASS
- AUTHORIZATION_REQUIRED tasks stop at human-authorization boundary

### 4.6 Subprocess Execution (execution_orchestrator.py:1341-1419)
- Uses `subprocess.run(command, shell=True, cwd=REPO_ROOT, env=child_process_env(), capture_output=True, text=True, timeout=spec.timeout_seconds)`
- Exit code 0 → PASS
- Exit code 124 → TIMEOUT
- Exit code 127 or infra signals (FileNotFoundError, ModuleNotFoundError, etc.) → INFRASTRUCTURE
- Otherwise → FAILED
- stdout/stderr written to `runtime/generated/m9-c49/logs/{plan_id}/{task_id}-stdout.log`


---

## SECTION 5: MUTATION & QUALITY

### 5.1 Mutation Testing Architecture
**Core modules:**
- `mutation_runner.py` (1,084 lines) — canonical mutation runner, single source of truth
- `mutation_contract.py` (720 lines) — mutation result schema, arithmetic reconciliation, three-gate classification
- `mutation_execution/` subpackage — domain_model.py, mutmut_adapter.py, orchestrator.py, evidence.py, workspace.py, health.py, verify_result.py, forensics.py, cache.py, backend_interface.py, config_fingerprint.py, isolation_report.py, adapter_report.py, reliability_report.py, cache_report.py, workspace_report.py, backend_contract_report.py, domain_model_report.py, final_certification.py

**Invocation (identical locally and in CI):**
- `python -m runtime.verify mutation` — authoritative full campaign
- `python -m runtime.verify mutation --smoke` — bounded infra health check
- `python -m runtime.verify mutation --target balance_engine` — incremental
- `python -m runtime.verify mutation --restore` — restore mutated source only

**Three-Gate Classification (mutation_contract.py:398 classify_gates):**
- Gate A (Execution): PASS | INFRASTRUCTURE_FAILURE — did the pipeline run?
- Gate B (Evidence): PASS | FAIL — is evidence complete?
- Gate C (Quality): True | False — does score meet 80% threshold?

**Exit code mapping (mutation_runner.py:1074-1084):**
- Gate A or B failed → exit 1 (NOT EVALUABLE, never a score)
- Full mode + Gate C True → exit 0
- Full mode + Gate C False → exit 2 (below threshold)
- Smoke/target → exit 0 if A & B pass (quality NOT gated)

**CI integration (mutation.yml:136-226):**
- mutation_execution_status, mutation_evaluated, mutation_score, mutation_killed, mutation_survived, mutation_threshold, mutation_exit_code, mutation_reason
- If mutation_evaluated=true && exit_code=0 → "Mutation score meets threshold"
- If mutation_evaluated=true && exit_code=2 → "Mutation score below threshold"
- If mutation_evaluated=false → "MUTATION NOT EVALUATED — infrastructure/evidence failure, NOT a 0% quality result"

### 5.2 Mutation Exit Code → Status Mapping (mutation_contract.py:210-222)
```
0    -> survived
1    -> killed
3    -> killed
-24  -> killed
5    -> no_tests
33   -> no_tests
34   -> skipped
35   -> suspicious
36   -> timeout
2    -> interrupted
None -> not_checked
default -> suspicious
```

### 5.3 Measurement Truth (measurement_truth.py — 602 lines)
**MeasurementCompletionStatus vocabulary:**
- AUTHORITATIVE_COMPLETE — only state consumable by certification
- PARTIAL, TIMEOUT, INFRASTRUCTURE_FAILURE, EVIDENCE_FAILURE, INVALID_SCOPE, DERIVED_ONLY, UNKNOWN — non-certifiable

**EvidenceClassification:** AUTHORITATIVE | DERIVED
**MeasurementKind:** COVERAGE | MUTATION (must remain separate)

### 5.4 Coverage & Quality Metrics
- `coverage_measurement.py` (7,939 lines) — coverage measurement
- `coverage_truth.py` (7,029 lines) — coverage truth contract
- `test_quality.py` (7,739 lines) — test quality metrics
- `gap_classification.py` (16,427 lines) — gap classification
- `test_generator.py` (22,458 lines) — test generation
- `generation_engine.py` (25,358 lines) — generation engine
- `generation_eligibility.py` (12,241 lines) — generation eligibility
- `test_strengthening_pipeline.py` (17,298 lines) — test strengthening
- `strengthening.py` (23,332 lines) — strengthening logic
- `strengthening_integration.py` (7,389 lines) — strengthening integration

### 5.5 Threshold Enforcement
- Backend coverage threshold: 40% (verification.yaml)
- Backend mutation threshold: 60% (verification.yaml)
- Full campaign mutation threshold: 80% (hardcoded in mutation_contract.py)
- `VerificationSummary.__post_init__` enforces arithmetic: passed + failed + skipped == total_tasks

### 5.6 Convergence Pipeline (convergence_pipeline.py — 1,388 lines)
Autonomous convergence pipeline (M9-C56):
1. DISCOVERS: loads mutation survivors, coverage gaps, capability attributions
2. CLASSIFIES: C42 classifier + C45 intel
3. GENERATES: produces concrete SAFE test code
4. APPLIES: writes tests to filesystem (additive only)
5. VALIDATES: runs focused tests + targeted mutation
6. REPORTS: convergence ledger with killed survivors, new tests, improved scores


---

## SECTION 6: DIAGNOSIS & CLASSIFICATION

### 6.1 Failure Classification System
**FailureClassification enum (models/model.py:56-73):**
- TEST_FAILURE — test assertion failure
- COMMAND_FAILURE — command exited non-zero
- IMPORT_FAILURE — import/module error
- TIMEOUT — command timed out
- ENVIRONMENT_FAILURE — environment issue
- PLANNING_FAILURE — planning error
- RECONCILIATION_FAILURE — evidence reconciliation failed
- ARTIFACT_FAILURE — artifact production failed
- UNKNOWN_FAILURE — unattributable (raw diagnostic preserved)

**FailureReport dataclass (failure_report.py:88-100):**
- classification, unit_id, command, exit_code, failure_summary, test_failure_count, root_failure, diagnostic, evidence_path

### 6.2 Exit Code Handling (execution_orchestrator.py:1341-1436)
- Exit code 0 → CompletionState.PASS
- Exit code 124 (TimeoutExpired) → CompletionState.TIMEOUT
- FileNotFoundError → CompletionState.INFRASTRUCTURE
- Exit code 127 or infra signals → CompletionState.INFRASTRUCTURE
- Otherwise → CompletionState.FAILED

### 6.3 Infrastructure vs Application Failure Distinction
Infra signals checked: FileNotFoundError, No such file or directory, ModuleNotFoundError, command not found, Permission denied, No such command

### 6.4 Diagnostic & Forensic Agent (diagnostic_agent.py — 968 lines)
Consumes only canonical framework outputs:
- ForensicExecutionRecord (C42.28)
- Correlation (C42.27)
- EvidenceAwarePlan (C42.27)
- ReconciledVerificationState (C42.28)

Nine canonical questions: What changed? What is affected? What evidence remains valid? What must actually run? What was actually executed? What happened? What was NOT tested? What remains uncertain? Is the repository state certifiable?

Verdict vocabulary (closed): CERTIFIABLE | NOT_CERTIFIABLE | CERTIFICATION_BLOCKED | INSUFFICIENT_EVIDENCE

Uncertainty taxonomy: nondeterministic_mutation, equivalent_mutant, insufficient_test_surface, stale_evidence, incomplete_ci_evidence, unmapped_capability, ambiguous_behavior

Causal chain stages (11): change, affected_graph_nodes, invalidations, reused_evidence, selected_tasks, executed_tasks, execution_results, new_evidence, derived_evidence, failures, uncertainties

### 6.5 Failure Report Generation (failure_report.py — 194 lines)
- `_pytest_failed_test_ids(output)` — extracts failing pytest node ids from "short test summary info" section
- `_count_pytest_failures(summary_text)` — extracts integer count of failed tests
- `_pytest_summary_line(output)` — returns first concise pytest summary line
- `is_pytest_command(command)` — checks if command contains "pytest"
- `is_import_failure(output)` — regex for ModuleNotFoundError, ImportError, SyntaxError, etc.

### 6.6 Change Classification (capability_resolver.py:75-112)
- ChangeClassification enum: TEST_CHANGE, CONFIG_CHANGE, INFRASTRUCTURE_CHANGE, DOCUMENTATION_CHANGE, SOURCE_CHANGE, UNKNOWN
- ClassifiedChange dataclass with classification field
- `_classify_change(file_path)` — classifies based on file path patterns

### 6.7 Reconciliation Classification (reconciliation.py:151-173)
- ReconciliationClassification — reconciles evidence from multiple sources


---

## SECTION 7: AI PLATFORM

### 7.1 AI Platform File Inventory
- `runtime/platform/ai/orchestrator.py` (265 lines) — AIOrchestrator, run lifecycle management
- `runtime/platform/ai/agents.py` (347 lines) — Agent base class + DiagnosticAssistantAgent + others
- `runtime/platform/ai/tools/__init__.py` (18K) — ToolRegistry, TOOL_REGISTRY_INSTANCE
- `runtime/platform/ai/tools/handlers.py` (9.2K) — Level 0-1 tool handlers
- `runtime/platform/ai/providers/base.py` (5.2K) — ModelProvider Protocol, BaseProvider ABC
- `runtime/platform/ai/providers/router.py` (9.3K) — ModelRouter
- `runtime/platform/ai/providers/local.py` (15K) — LocalOllamaProvider, LocalLargeProvider, OpenRouterProvider, DeterministicFallbackProvider
- `runtime/platform/ai/config.py` (8.5K) — AIConfig, load_config, get_ai_config
- `runtime/platform/ai/intent.py` (5.6K) — intent classification
- `runtime/platform/ai/policy.py` (4.7K) — AI policy enforcement
- `runtime/platform/ai/planner.py` (5.3K) — AI planning
- `runtime/platform/ai/runs.py` (2.9K) — run tracking
- `runtime/platform/ai/memory.py` (3.1K) — AI memory
- `runtime/platform/ai/context/builder.py` (15K) — ContextBuilder, build_context_pack
- `runtime/platform/ai/context/cache.py` (2.5K) — context cache
- `runtime/platform/ai/context/trimmer.py` (2.3K) — context trimmer
- `runtime/platform/ai/context/serializer.py` (2.0K) — context serializer
- `runtime/platform/ai/context/ranker.py` (2.7K) — context ranker
- `runtime/platform/ai/context/provenance.py` (3.4K) — context provenance

### 7.2 AI Orchestrator (orchestrator.py)
- `AIOrchestrator` — central coordinator for AI run lifecycle
- `start_run(symptom, mode, capability_id)` — creates run in PENDING state
- `get_run(run_id)`, `list_runs(limit, status)` — run retrieval
- `execute_step(run_id, tool_name, ...)` — step execution
- Runs persisted to `runtime/generated/ai-runs/{run_id}.json`
- Audit trail maintained per run
- Does NOT connect to any LLM directly

### 7.3 Agent Framework (agents.py)
- `Agent` base class — name, description, authority_level, enabled
- `can_execute(run_mode, run_authorization_level)` — checks authority
- `DiagnosticAssistantAgent` (Phase 17) — authority level 1, enabled by default
  - Pipeline: USER SYMPTOM → DETERMINISTIC ENGINE → CHANGE INTELLIGENCE → HISTORY → EVIDENCE → CONTEXT PACK → LOCAL MODEL → STRUCTURED INTERPRETATION
  - Distinguishes FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION
  - Never overwrites deterministic evidence

### 7.4 Tool Registry (tools/__init__.py)
- `ToolRegistry` — get, list_tools, invoke, get_tool_schema
- `register_builtin_tools(registry)` — registers Level 0 (observe/read-only) and Level 1 (governed write) handlers
- `TOOL_REGISTRY_INSTANCE` — singleton
- Tool path: Tool Registry → Policy Engine → Platform API Service → C50 Authority
- No direct AI → executor / DB / shell / filesystem mutation

### 7.5 Tool Handlers (handlers.py)
**Level 0 (observe — read-only):**
- `inspect_health` → health.build_health_snapshot()
- `inspect_capability` → capabilities.build_capability_detail()
- `inspect_architecture` → architecture.build_architecture_authorities()
- `inspect_errors` → errors_service.build_errors_current/recent/recurring()
- `inspect_history` → history.build_history_runs()
- `inspect_evidence` → evidence.build_evidence_detail()
- `inspect_file` → read-only file read
- `inspect_capabilities` → capabilities.build_capability_list()

**Level 1 (governed write):**
- `run_verification_capability` → verification_write.build_run_result()
- `run_capability_group` → verification_write.build_run_result() for each

### 7.6 LLM Provider Integration
- `ModelProvider` Protocol (base.py:110) — provider interface
- `BaseProvider` ABC (base.py:138) — base implementation
- `ProviderKind` enum — provider types
- `ProviderHealth` — health tracking
- `ModelRouter` (router.py:55) — register, get_provider, list_providers, route
- `LocalOllamaProvider` — local Ollama integration
- `LocalLargeProvider` — local large model
- `OpenRouterProvider` — OpenRouter API integration
- `DeterministicFallbackProvider` — deterministic fallback when no LLM available

### 7.7 AI Configuration (config.py)
- `AIConfig` — provider configs, model settings
- `load_config()`, `get_ai_config()`, `reload_ai_config()`, `set_ai_config()`
- `get_provider_config(name)` — per-provider configuration

### 7.8 Context Pack Builder (context/builder.py)
- `ContextBuilder` — builds deterministic, reproducible context packs
- `build_context_pack(symptom, capability_id, run_id, intent_type)` — convenience function
- Context pack kind: "platform.context_pack"
- Components: change intelligence, history, evidence, diagnostics, repository context


---

## SECTION 8: CHANGE DETECTION

### 8.1 Git Integration (orchestrator.py:76-150)
- `_find_repo_root()` — walks up from __file__ to find backend/pyproject.toml marker
- `_default_branch()` — tries origin/main, origin/develop, main, develop
- `_merge_base_with_default()` — computes merge-base of HEAD and default branch
  - Fetches default branch first to avoid stale refs (F26: fetch failures fail closed)
  - Offline mode via VERIFICATION_OFFLINE=1 env var
- `_collect_changed_files()` — collects changed files via git diff
- `_is_git_available()` — checks git availability
- `_filter_changed_files()` — filters out runtime/generated/, node_modules/, .pytest_cache/, __pycache__, .pyc files

### 8.2 Change Intelligence (foundation/intelligence/platform/)
- `change.py` — `analyze_changes()` function
- `blast.py` — `compute_blast_radius()`, `impacted_engines()`, `all_impacted()`
- `optimizer.py` — `optimize_verification()`, `VerificationPlanIntel`
- `resolver.py` — capability resolution
- `attribution.py` — change attribution
- `risk.py` — risk assessment
- `cost.py` — cost analysis
- `state.py` — state management
- `repair.py` — repair logic
- `optimizer.py` — optimization
- `cli_format.py` — CLI formatting
- `pipeline.py` — pipeline orchestration
- `changeset.py` — changeset management
- `memory.py` — intelligence memory
- `ci.py` — CI integration
- `api.py` — API integration
- `migration.py` — migration intelligence
- `certification.py` — certification intelligence

### 8.3 Repository Intelligence (foundation/repository/)
- `scanner/` — base.py, backend_scanner.py, frontend_scanner.py, api_scanner.py, test_scanner.py, workflow_scanner.py, script_scanner.py, docs_scanner.py, metadata_scanner.py, migration_scanner.py
- `graph/` — graph_service.py, schema.py
- `builder/` — builder.py, index.py
- `query/` — query.py
- `analysis/` — impact.py, metrics.py
- `validation/` — validator.py
- `__main__.py` — module entry point

### 8.4 Repository Graph Service (graph_service.py)
- `RepositoryGraphService` — consumed by VerificationPlanner
- Builds dependency graph from scanner outputs
- Provides graph queries for planning

### 8.5 File-to-Module Mapping
- `capability_resolver.py` — `_classify_change(file_path)` classifies by path patterns
- `change_surface.py` — `discover_change_surfaces()`, `ChangeSurfaceAnalysis`, `SurfaceKind`
- `shared_impact.py` — `SharedDependencyIndex`, `get_shared_dependency_index()`
- `capability_graph_resolver.py` — resolves capabilities from change surfaces
- `capability_graph.py` — verification graph model

### 8.6 PR Boundary Detection
- Tier 1 (LOCAL): working-tree delta only — never diffs against origin/main
- Tier 2 (PR): GITHUB_BASE_REF or explicit override
- `_merge_base_with_default()` — merge-base computation with fetch
- `_resolve_repository_identity()` — commit_sha + branch from git at record time


---

## SECTION 9: EVIDENCE PROVENANCE

### 9.1 Evidence Reuse System (evidence_reuse.py — 938 lines)
**Four reuse primitives:**
- `PopulationSnapshot` — frozen set of components under verification
- `ComponentMeasurement` — one component's measurement record
- `DerivedAggregate` — result computed from authoritative component measurements
- `EvidenceReuse` — decision that existing measurement remains valid
- `MeasurementInvalidation` — conditions under which evidence must be re-measured

**ReuseDisposition vocabulary:**
- REUSE — evidence remains valid
- INVALIDATE_COMPONENT — evidence for specific component is dead
- INVALIDATE_CAPABILITY — evidence for entire capability is dead
- INVALIDATE_TASK — single task's evidence is dead
- INVALIDATE_EVIDENCE_ONLY — only this specific evidence is dead
- DOES_NOT_INVALIDATE — evidence remains valid

**Invalidation rules:** enumerated explicitly, never guessed. Classifier is a pure function (unit testable).

### 9.2 Cache/Reuse Logic (cache.py — 223 lines)
**VerificationCache:**
- Keys: (commit, changed_files, profile)
- `replay()` — authoritative entry point
- Returns ReplayResult with exit_code derived from stored overall_status
- **Critical invariant:** exit_code can never be 0 when stored status is "fail"
- Cached PASS → exit 0; Cached FAIL → exit != 0; Missing/corrupt → re-execute or fail safely

**Content-aware invalidation (R-CACHE-1):**
- Old key was (commit, changed_files, fingerprint) where changed_files was filename list
- New key hashes working-tree CONTENTS of every changed file
- Any content change on disk forces fresh run

**CachedVerdict dataclass:** overall_status, passed, failed, skipped, unit_statuses

### 9.3 Evidence Integrity (evidence_integrity.py)
- `EvidenceIntegrityReport` — integrity report for evidence artifacts
- Validates evidence completeness and consistency

### 9.4 Evidence Persistence
- Path generation: `runtime/generated/m9-c49/logs/{plan_id}/{task_id}-stdout.log`
- Serialization: json.dumps with indent=2, default=str
- Retention: workflow-defined (14-90 days depending on artifact type)
- Cleanup: no explicit cleanup policy found in code; retention managed by GitHub Actions

### 9.5 Stale Evidence Detection
- `MeasurementInvalidation` — explicit conditions for staleness
- `EvidenceReuse.decide_reuse()` — deterministic reuse decision
- `PopulationSnapshot.fingerprint()` — content-derived fingerprint for staleness check
- Fingerprint mismatch → do not reuse (cache.py)

### 9.6 Historical Evidence Comparison
- `c42_24_b_measurements()` — 12 components with scored/killed counts
- `c42_25_measurements()` — 2 intelligence components
- `c42_26_population()` — 14-component population snapshot
- `c42_26_derived_aggregate()` — derived aggregate from measurements

### 9.7 Milestone State Tracking (milestone_state.py — 2,319 lines)
- `Evidence` class — milestone evidence tracking
- Tracks progress across M9-C42 through M9-C57 milestones


---

## SECTION 10: METRICS & COVERAGE

### 10.1 Coverage Modules
- `coverage_measurement.py` (7,939 lines) — coverage measurement implementation
- `coverage_truth.py` (7,029 lines) — coverage truth contract
- `measurement_truth.py` (602 lines) — measurement truth contract (shared by coverage + mutation)
- `measurement_truth_integration.py` — integrates measurement truth into execution
- `measurement_truth_cli.py` (3,838 lines) — CLI for measurement truth

### 10.2 Threshold Enforcement
- Backend coverage threshold: 40% (verification.yaml)
- Backend mutation threshold: 60% (verification.yaml)
- Full campaign mutation threshold: 80% (hardcoded in mutation_contract.py:88)
- `MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE` — only state consumable by certification
- `_NON_CERTIFIABLE` set: PARTIAL, TIMEOUT, INFRASTRUCTURE_FAILURE, EVIDENCE_FAILURE, INVALID_SCOPE, DERIVED_ONLY
- `VerificationSummary.__post_init__` — arithmetic invariant: passed + failed + skipped == total_tasks

### 10.3 Quality Metrics Modules
- `test_quality.py` (7,739 lines) — test quality metrics
- `test_false_certification_audit.py` (9,913 lines) — false certification audit
- `test_cache_invalidation.py` (12,428 lines) — cache invalidation testing
- `test_command_consolidation.py` (8,152 lines) — command consolidation
- `candidate_validation.py` (20,320 lines) — candidate validation
- `pipeline_enforcement.py` (12,489 lines) — pipeline enforcement

### 10.4 Coverage Evidence Collection
- `runtime/system/evidence/collectors/coverage.py` — CoverageCollector, CoverageEvidence
- `runtime/system/evidence/collectors/mutation.py` — MutationCollector
- `runtime/system/evidence/collectors/test_results.py` — TestResultCollector
- `runtime/system/evidence/collectors/contract_tests.py` — ContractTestsCollector
- `runtime/system/evidence/collectors/property_tests.py` — PropertyTestsCollector
- `runtime/system/evidence/collectors/base.py` — EvidenceCollector ABC, EvidenceArtifact

### 10.5 Evidence Aggregation
- `runtime/system/evidence/aggregator.py` (1,085 lines) — EvidenceAggregator, EvidenceSummary
- `runtime/system/evidence/ingestion/pipeline.py` — EvidenceIngestionPipeline
- `runtime/system/evidence/api.py` — evidence API (CoverageEvidence, MutationEvidence, VerificationEvidence)

### 10.6 Observability
- `runtime/system/observability/` — analytics.py, cost_analysis.py, dashboard.py, dependency_growth.py, event_store.py, execution_context.py, flaky_tests.py, health_report.py, outcome.py, repository.py
- Event store: EngineeringEventStore, create_event
- RunRecord: run_id, timestamp, environment, runner, verification_depth, intent, trigger, commit_sha, branch, profile, status, passed, failed, skipped, duration_seconds, evidence_count, cache_hit, metadata


---

## SECTION 11: RUNTIME EXECUTION SAMPLES

### 11.1 Runtime Help
```
python -m runtime.verify --help
python verify.py --help
```
Canonical CLI tree:
- verify check — plan + execute required verification
- verify plan — plan-only mode
- verify run — execute explicit plan
- verify diagnose — failure/survivor diagnostic
- verify strengthen — test-strengthening
- verify inspect — read-only (capabilities/evidence/plan/mutation/workflows/health)
- verify certify — certification (evidence-gated)
- verify ci — CI orchestration/reconciliation
- verify doctor — framework health/integrity

### 11.2 Runtime Diagnostics
- `python -m runtime.verify doctor` — framework health/integrity check
- `python -m runtime.verify env-check` — canonical environment check (machine-readable fingerprint)
- `python -m runtime.verify status` — verification status summary
- `python -m runtime.verify metrics` — metrics
- `python -m runtime.verify history` — history
- `python -m runtime.verify deps` — dependencies
- `python -m runtime.verify verify-status` — verification status
- `python -m runtime.verify integrity` — integrity check
- `python -m runtime.verify mutation --smoke` — bounded mutation smoke test

### 11.3 Environment Contract (env.py)
- `child_process_env()` — canonical child-process environment
  - Prepends venv/bin and interpreter bin to PATH
  - Sets PYTHONUNBUFFERED=1, TZ=UTC, LC_ALL=C.UTF-8, LANG=C.UTF-8
- `EnvironmentReport` — python, pytest, mutmut tools with versions and sources
- `FORBIDDEN_VENV_DIRS` — backend/venv, backend/.venv must NEVER exist
- `PINNED_MUTMUT = "3.7.0"`, `MIN_PYTHON = (3, 12)`

### 11.4 Runtime Version
- Engineering Platform v1.0.0
- Release Date: 2026-08-05
- Status: STABLE
- SemVer: v1.0.x = bug fixes; v1.1 = backwards-compatible additions; v2.0 = breaking changes

### 11.5 Runtime Self-Documentation
Key module docstrings:
- `verify.py`: "ClariFin OS — Autonomous Verification Runtime (Program 7B). M9-C49: Control Plane Consolidation. M9-C57: Canonical Runtime & Reproducible Environment Convergence. This is the THIN COMPATIBILITY SHIM for the verification runtime."
- `orchestrator.py`: "Verification Orchestrator — Program 7B. Deterministic verification runtime that automatically plans, executes, and reports verification based on changed files."
- `planner/planner.py`: "Verification Planner — Phase 4 + Program 7A Cross-Layer Intelligence. Produces deterministic verification plans from changed files, capabilities, endpoints, and requested scope. No execution logic. Pure planning."
- `executor_pipeline.py`: "M9-C42.28 — Executable Verification Plan + Targeted Executor + Evidence Capture + Reconciliation + Scope Enforcement + Failure Classification."
- `execution_orchestrator.py`: "M9-C49 — Verification Execution Orchestration. Turns the C48 control-plane plan into an executable, observable, deterministic verification pipeline."
- `diagnostic_agent.py`: "M9-C42.30 — Diagnostic & Forensic Agent Foundation. Consumes only canonical framework outputs. First version is diagnostic: it observes evidence and reaches conclusions; it never modifies production code."
- `blast_radius.py`: "M9-C50 — Canonical Blast-Radius Contract. The single canonical deterministic contract representing change impact. Answers 15 questions required by the C50 spec."
- `control_plane_facade.py`: "M9-C49 — Canonical Control Plane Facade. This module is the SINGLE public command surface for the ClariFin_OS verification runtime."
- `convergence_pipeline.py`: "M9-C56 — Autonomous Convergence Pipeline. Makes the entire ClariFin_OS verification infrastructure automatically invocable."
- `mutation_runner.py`: "M9-C42.5 — Canonical mutation runner (single source of truth). Replaces the fragile bash pipeline with one deterministic, testable Python runner."
- `tier.py`: "VEA-5 M2 — Tier-aware verification planning. A verification unit is never silently absent from a plan."
- `profiles.py`: "Verification Profiles — Program 7B. Immutable verification profiles that expand into deterministic tasks."


---

## SECTION 12: TESTING & CONFIGURATION

### 12.1 Runtime Test Inventory
- 107 test files in `runtime/tests/`
- All 107 test files reference runtime/verify (comprehensive coverage)
- Test categories: m9_c42_27 through m9_c57, platform_api_phase1-15, vea5_*, measurement_truth, mutation_infra, mutation_inventory, orchestrator, integrity_*, knowledge_*, repair, risk, workspace, snapshots, status, verify_status, etc.

### 12.2 Key Test Files
- `test_m9c57_verification_self_contract.py` — O2-D reconciliation test (profiles ↔ verification.yaml)
- `test_m9c57_outcome_semantic_contract.py` — O-2 outcome vocabulary contract
- `test_m9c57_observability_convergence.py` — observability convergence
- `test_m9_c50_stop_gate2_obligation_reconciliation.py` through `stop_gate9_failure_modes.py` — stop gates
- `test_m9_c50_self_verification.py` — runtime self-verification
- `test_m9_c50_final_governance.py` — final governance
- `test_m9_c50_operational_lineage.py` — operational lineage
- `test_m9_c50_executor_adapters.py` — executor adapters
- `test_m9_c50_ci_convergence.py` — CI convergence
- `test_m9_c49_canonical_cli.py` — canonical CLI
- `test_m9_c48_*` — C48 milestone tests (aggregator_obsolete, api_schema_governance, capability_authority, capability_graph, cli_governance, coverage_truth, frontend_arithmetic, function_audit, milestone_state, mutation_unified, test_quality, test_strengthening)
- `test_vea5_*` — VEA-5 tests (m5_ci_integration, m6_evidence_contract, m8_merge_enforcement, m8r_cache_observability, m8r_cli_reconcile, m9_security_codeql, plan_reconciliation, tier_plan, verification_cache)
- `test_platform_api_phase1.py` through `test_platform_api_phase15_21.py` — platform API tests

### 12.3 Environment Variables
- `VERIFICATION_OFFLINE=1` — skip git fetch, use local refs only
- `PYTHONUNBUFFERED=1` — unbuffered Python output (set by child_process_env)
- `TZ=UTC`, `LC_ALL=C.UTF-8`, `LANG=C.UTF-8` — deterministic locale (set by child_process_env)

### 12.4 Dependencies (pyproject.toml)
**Runtime/verification CLI:**
- click==8.4.2

**Backend runtime:**
- fastapi==0.141.1, pydantic==2.13.5, python-multipart==0.0.32, pdfplumber==0.11.10, camelot-py[cv]==2.0.0, ghostscript==0.8.1, pandas==3.0.5, python-dateutil==2.9.0, cachetools==7.1.8, httpx==0.28.1, jsonschema==4.26.0, pyyaml==6.0.3, uvicorn==0.52.4

**Verification tooling (optional):**
- pytest==9.1.1, pytest-asyncio==1.4.0, pytest-cov==7.1.0, pytest-xdist==3.8.0, pytest-timeout==2.4.0, hypothesis==6.167.1, coverage==7.16.0, ruff==0.16.6, black==26.5.1, mypy==2.3.1, mutmut==3.7.0

**Contract testing (optional):**
- schemathesis==4.25.2

**Script entry points:**
- `verify = "runtime.foundation.verification.cli.cli:cli"`

### 12.5 Pytest Configuration
- pythonpath = ["backend/src", "backend/tests"]
- norecursedirs: .*, backend/mutants, backend/tests/mutation_infra/mutants, backend/tests/invariants/_m4_exit_probe/**, backend/tests/probes, .git, __pycache__, .venv, venv, node_modules, frontend/node_modules
- Markers: capability, contract, property, invariant, golden, meta, slow, mutation, integration, unit, performance

### 12.6 Linting/Formatting
- Ruff: line-length=88, target-version=py312, select E/W/F/I/B/C4/UP/SIM
- Black: line-length=88, target-version=py312
- Mypy: python_version=3.12, mypy_path=backend/src, exclude backend/, runtime/generated/

### 12.7 Runtime Logging
- No dedicated logging module found
- `logging.getLogger(__name__)` used in orchestrator.py, verify.py, handlers.py, agents.py
- Print statements: significant count across runtime (console output for CLI)
- Rich/colorama/termcolor: not found in runtime code (click used for CLI formatting)


---

## SECTION 13: INTEGRATION POINTS

### 13.1 Backend Integration
- `runtime/foundation/verification/env.py` — resolves backend/src on sys.path
- `pyproject.toml` — mypy_path = ["backend/src"], pythonpath = ["backend/src", "backend/tests"]
- `runtime/foundation/repository/scanner/backend_scanner.py` — scans backend source
- `runtime/foundation/intelligence/platform/` — blast, change, optimizer, attribution, risk, cost, certification
- `runtime/foundation/architecture/` — provider.py, cross_layer.py, models.py, sources.py, chains.py, discovery.py, migration_reports.py, ids.py
- Backend engines referenced: loan_engine, credit_card_engine, account_engine, reconciliation_engine, behaviour_engine, balance_engine, ledger_audit_engine, cashflow_engine, financial_events, core_domain_money, common_calculations, recommendation_engine

### 13.2 Frontend Integration
- `runtime/foundation/repository/scanner/frontend_scanner.py` — scans frontend source
- `runtime/foundation/verification/frontend_financial_arithmetic_lint.py` — frontend financial arithmetic lint
- `runtime/system/context/` — TypeScript context management (ContextHistory, ContextNavigation, ContextSelection, ContextRestorer, ContextSerializer, ContextValidator, ContextManager, ContextRegistry, ContextRuntime, ContextSession, ContextWorkspace)
- Frontend verification: `python -m runtime.verify frontend`

### 13.3 Database Integration
- No direct database references found in runtime code
- Migration verification exists as a workflow category (verification.yaml:133-141)
- `runtime/foundation/repository/scanner/migration_scanner.py` — migration scanner

### 13.4 CI Integration
- All 13 workflows delegate to `python -m runtime.verify <command>`
- `.github/actions/bootstrap-runtime` — sets up Python environment
- `.github/actions/setup-node-runtime` — sets up Node.js
- `.github/actions/upload-runtime` — uploads artifacts
- Workflow triggers: push (branches: "**"), pull_request (main, develop), schedule, workflow_dispatch
- Artifacts uploaded: cross-layer-map, knowledge-index, verification-cache, engineering-history, verification-report, execution/, mutation-report, coverage-evidence, runtime-performance

### 13.5 Cross-Layer Integration
- `runtime/foundation/architecture/cross_layer.py` — cross-layer analysis
- `runtime/foundation/audit/cross_layer.py` — audit cross-layer
- `runtime/foundation/verification/api_contracts/` — inventory.py, gate.py, taxonomy.py, mutations.py, normalize.py, c30_certification.py, fixture.py
- `runtime/platform/api/contracts/` — architecture.py, application.py, capabilities.py, change.py, context.py, diagnostics.py, errors.py, events.py, evidence.py, executions.py, health.py, history.py, tasks.py, verification.py, ai.py, _primitives.py
- `runtime/platform/api/services/` — application.py, architecture.py, capabilities.py, change.py, evidence.py, executions.py, health.py, history.py, tasks.py, tasks_write.py, verification.py, verification_write.py, events.py, errors.py, _helpers.py, _comparison.py


---

## SECTION 14: OBSERVABILITY

### 14.1 Logging Infrastructure
- No dedicated logging module found in runtime/
- `logging.getLogger(__name__)` used in: orchestrator.py, verify.py, handlers.py, agents.py
- Print statements used extensively for CLI console output (click.echo)
- No rich/colorama/termcolor usage found (click provides CLI formatting)

### 14.2 Observability Modules
- `runtime/system/observability/`:
  - `analytics.py` — analytics engine
  - `cost_analysis.py` — cost analysis
  - `dashboard.py` — dashboard generation
  - `dependency_growth.py` — dependency growth tracking
  - `event_store.py` — EngineeringEventStore, create_event
  - `execution_context.py` — create_context
  - `flaky_tests.py` — flaky test detection
  - `health_report.py` — health reporting
  - `outcome.py` — outcome tracking
  - `repository.py` — LocalMetricsRepository, RunRecord

### 14.3 Event Store
- `EngineeringEventStore` — appends events to JSONL file
- `create_event(event_type, context, payload, metadata)` — creates structured event
- Events: verification_record, VerificationCompleted, and others
- Context: environment, runner, verification_depth, intent, trigger, commit_sha, branch

### 14.4 RunRecord
Fields: run_id, timestamp, environment, runner, verification_depth, intent, trigger, commit_sha, branch, profile, status, passed, failed, skipped, duration_seconds, evidence_count, cache_hit, metadata

### 14.5 Audit Modules
- `runtime/foundation/audit/`:
  - `observability.py` — observability tracking
  - `repair_order.py` — repair ordering
  - `workspace.py` — workspace audit
  - `cross_layer.py` — cross-layer audit
  - `models.py` — audit models
  - `normalize.py` — normalization
  - `certification.py` — certification audit
  - `knowledge.py` — knowledge audit
  - `github_runtime.py` — GitHub runtime audit
  - `github_actions.py` — GitHub Actions audit
  - `runtime_cli.py` — runtime CLI audit
  - `evidence.py` — evidence audit
  - `reporter.py` — report generation
  - `cluster.py` — clustering
  - `artifact_ownership.py` — artifact ownership
  - `planner.py` — planner audit
  - `dependency_graph.py` — dependency graph audit
  - `remediation.py` — remediation
  - `performance.py` — performance audit
  - `failure_injection.py` — failure injection
  - `integrity.py` — integrity audit
  - `repository.py` — repository audit
  - `runner.py` — runner audit
  - `executor.py` — executor audit
  - `pipeline.py` — pipeline audit


---

## SECTION 15: DOCUMENTATION

### 15.1 Module and Function Docstrings
Key module docstrings (from code inspection):
- `verify.py`: Thin compatibility shim. All operator/AI commands flow through canonical control plane. Legacy commands routed with deprecation warnings.
- `orchestrator.py`: Deterministic verification runtime that automatically plans, executes, and reports verification based on changed files. The orchestrator never performs dependency analysis itself.
- `planner/planner.py`: Produces deterministic verification plans from changed files, capabilities, endpoints, and requested scope. No execution logic. Pure planning.
- `executor.py`: Execution pipeline for verification commands. Supports Python, npm, pytest, vitest, playwright, schemathesis, shell commands. Retry logic, cancellation, parallel execution, streaming output, process-group ownership.
- `executor_pipeline.py`: Runtime bridge between evidence-aware planner and execution infrastructure. Contains executable verification plan, task adapters, targeted mutation executor, evidence capture, reconciliation, scope enforcement, failure classification.
- `execution_orchestrator.py`: Turns C48 control-plane plan into executable, observable, deterministic pipeline. Consumes C48 plan; never independently re-discovers verifications.
- `diagnostic_agent.py`: Diagnostic & Forensic Agent Foundation. Consumes only canonical framework outputs. Never modifies production code. Nine canonical questions. Closed verdict vocabulary.
- `blast_radius.py`: Canonical Blast-Radius Contract. Single canonical deterministic contract representing change impact. Answers 15 questions. Every impact decision has machine-readable provenance.
- `control_plane_facade.py`: SINGLE public command surface. Every operator/AI invocation maps to exactly one canonical operation. 9 top-level commands.
- `control_plane.py`: Strengthens existing planner so capability information actually controls execution. Prefers reusable evidence → targeted verification → component-specific → capability-specific → property/invariant/contract → targeted mutation → escalation.
- `mutation_runner.py`: Canonical mutation runner. Replaces fragile bash pipeline. Executes intended tests against generated mutants. Produces trustworthy killed/survived/no-tests/timeout/not-checked. Behaves identically locally and in CI.
- `mutation_contract.py`: Canonical mutation result schema. Arithmetic reconciliation invariant. Three-gate classification (Execution / Evidence / Quality). Pure logic only.
- `measurement_truth.py`: ONE authoritative, observable, durable and reproducible measurement path. Coverage and mutation are explicitly SEPARATE measurements. Partial/timeout/corrupt/derived can NEVER be labelled AUTHORITATIVE_COMPLETE.
- `evidence_planner.py`: Evidence-aware planner. Produces deterministic plan answering what is affected, what evidence exists, which is reusable, which is invalidated, which tasks must be re-executed, what remains uncertain.
- `evidence_reuse.py`: Previously generated evidence can be deterministically reused when validity conditions remain satisfied. Four reuse primitives. Invalidation rules enumerated explicitly.
- `cache.py`: Verification cache integrity. Cached successful → PASS. Cached failed → FAIL. Missing/corrupt → re-execute or fail safely. Fingerprint mismatch → do not reuse.
- `certification.py`: Programmatic certification engine. Verifies all gates G1-G30. Verdict: CERTIFIED | NOT_CERTIFIED | CERTIFICATION_BLOCKED | INSUFFICIENT_EVIDENCE.
- `convergence_pipeline.py`: Autonomous convergence pipeline. DISCOVERS → CLASSIFIES → GENERATES → APPLIES → VALIDATES → REPORTS. Makes entire runtime infrastructure automatically invocable.
- `canonical_control_plane.py`: SINGLE authoritative operator-facing command tree. Every public command maps to one canonical control-plane operation.
- `obligation.py`: Control plane reasons in terms of obligations, not files or commands. Change → Capability → Requirement → Verification Obligation → Task → Evidence → Disposition. Pure: no I/O.
- `capability_contract.py`: Extends VerificationCapability architecture so every registered capability can answer machine-readably 24 questions. Additive — no second capability registry.
- `profiles.py`: Immutable verification profiles that expand into deterministic tasks. Each profile maps to specific set of verification commands. No duplicated commands.
- `tier.py`: Tier-aware verification planning. A verification unit is never silently absent from a plan. Three tiers: LOCAL, PR, DEEP.
- `env.py`: Canonical environment resolver. Single place that resolves mutmut/pytest/python binaries, pins and validates contracts, detects stray virtualenvs, emits machine-readable fingerprint.

### 15.2 TODOs/FIXMEs/HACKs in Runtime
Only 2 found:
1. `runtime/foundation/verification/capability_graph_resolver.py:14` — "planner (planner.py:382-388 TODO closure)"
2. `runtime/foundation/verification/planner/planner.py:383` — "# TODO Program 7: implement graph-based capability resolution"

### 15.3 Known Limitations
- `program16_analysis.py` (66K lines) — likely auto-generated analysis dump, not actively maintained
- Multiple `analyze_*.py` scripts at runtime root — analysis tools, not part of core framework
- `runtime/system/evidence/aggregator_obsolete_disposition.py` — explicitly marked obsolete
- `runtime/system/context/` — TypeScript implementation (separate from Python runtime)
- `runtime/system/financial/`, `runtime/system/graph/`, `runtime/system/timeline/`, `runtime/system/command/` — README.md only, no Python implementation
- Mutation testing full campaign takes ~27 minutes (documented constraint)
- Mutation threshold: 80% for full campaign, 60% for backend (different thresholds for different scopes)
- Backend coverage threshold: 40% (relatively low)
- `runtime/generated/` excluded from ruff/black/mypy linting (intentional — generated artifacts)


---

SECTION 16 TEST
SECTION 16 START

---

## SECTION 16: CONCEPTUAL ANSWERS

### Q1: What is the runtime's conceptual model?
The runtime is a **deterministic verification orchestrator with autonomous convergence capabilities**. It is NOT just a test runner — it is a multi-layered system that:

1. **Detects changes** via git intelligence (Tier 1 LOCAL / Tier 2 PR / Tier 3 DEEP)
2. **Maps changes to capabilities** via capability resolver + blast radius analysis
3. **Plans verification** via evidence-aware planner (reuse decisions, invalidation rules)
4. **Executes verification** via subprocess orchestration with failure classification
5. **Collects evidence** with measurement truth (authoritative vs derived)
6. **Certifies** via 30-gate certification engine
7. **Diagnoses failures** via forensic diagnostic agent
8. **Strengthens tests** via autonomous convergence pipeline (generates tests, applies, validates)
9. **Provides AI platform** with tool registry, context packs, and governed agents

Key defining modules:
- `control_plane_facade.py` — single public command surface
- `execution_orchestrator.py` — turns plans into executable pipeline
- `convergence_pipeline.py` — autonomous test strengthening
- `diagnostic_agent.py` — forensic diagnosis
- `blast_radius.py` — canonical impact contract

### Q2: What is the data flow?
**Input:** git diff / file paths / CLI args / changed capabilities / changed endpoints
**Processing chain:**
```
Change Detection (git diff)
  → Change Classification (capability_resolver._classify_change)
  → Blast Radius Computation (blast_radius.py — 15 questions)
  → Capability Resolution (capability_resolver)
  → Control Plane Planning (control_plane.py — prefers reusable → targeted → component → capability → property → mutation → escalation)
  → Evidence-Aware Planning (evidence_planner.py — reuse decisions, invalidation)
  → Task Compilation (executor_pipeline.py — executable tasks with commands, timeouts, fingerprints)
  → Execution (execution_orchestrator.py — subprocess with failure classification)
  → Evidence Capture (ExecutionEvidence records)
  → Reconciliation (reconciliation.py — labelled aggregates)
  → Certification (certification.py — 30 gates G1-G30)
  → Diagnostic (diagnostic_agent.py — 9 questions, closed verdicts)
  → Convergence (convergence_pipeline.py — generate → apply → validate → report)
```
**Output:** JSON evidence artifacts, verification reports (MD), CI status (exit codes), certification verdicts, diagnostic reports, convergence ledgers

### Q3: What are the core abstractions?
**Base classes/protocols:**
- `VerificationProfile` (profiles.py) — immutable profile → deterministic tasks
- `VerificationPlanner` (planner/planner.py) — pure planning
- `Executor` (executor.py) — subprocess execution with retry/timeout/cancellation
- `ExecutionOrchestrator` (execution_orchestrator.py) — plan → execution bridge
- `Agent` (agents.py) — AI agent base class
- `ToolRegistry` (tools/__init__.py) — tool registration and invocation
- `ModelProvider` Protocol (providers/base.py) — LLM provider interface
- `EvidenceCollector` ABC (system/evidence/collectors/base.py) — evidence collection

**Composition pattern:**
- Facade → ControlPlanePlanner → ExecutionOrchestrator → Executor
- Facade → CapabilityResolver → BlastRadius → ControlPlanePlanner
- Facade → EvidenceAwarePlanner → EvidenceReuse → ComponentMeasurement
- Facade → CertificationEngine (30 gates)
- Facade → DiagnosticAgent (consumes ForensicExecutionRecord)
- Facade → ConvergencePipeline (DISCOVER → CLASSIFY → GENERATE → APPLY → VALIDATE → REPORT)

### Q4: What is the extension mechanism?
**Adding a new verification gate:**
1. Add to `verification.yaml` workflows section (command, scope, capabilities)
2. Add to `UNIT_CATALOG` in `tier.py` (id, category, estimated_seconds)
3. Add to `profiles.py` if it's a profile alias
4. Add certification gate in `certification.py` (G1-G30)
5. Add test in `runtime/tests/`

**Adding a new evidence type:**
1. Add `@dataclass` in `system/evidence/models/evidence.py` or `foundation/verification/models/model.py`
2. Add collector in `system/evidence/collectors/`
3. Add to `EvidenceAggregator` in `system/evidence/aggregator.py`
4. Add API contract in `platform/api/contracts/evidence.py`
5. Add service in `platform/api/services/evidence.py`

**Adding a new tier:**
1. Add to `VerificationTier` enum in `tier.py`
2. Define selection logic in tier planner
3. Update UNIT_CATALOG completeness invariant

Q5-Q8 start

### Q5: How does CI invoke the runtime?
**Exact command-line invocations from workflows:**
- `python -m runtime.verify backend` (backend-verify.yml:57)
- `python -m runtime.verify frontend` (frontend-verify.yml:61)
- `python -m runtime.verify api-contracts` (api-contracts.yml:65)
- `python -m runtime.verify runtime` (verification-runtime.yml:60)
- `python -m runtime.verify mutation --smoke` (mutation.yml:59)
- `python -m runtime.verify mutation` (mutation.yml:81)
- `python -m runtime.verify env-check` (mutation.yml:56, 78)
- `python -m runtime.verify status >> $GITHUB_STEP_SUMMARY` (all workflows)

**Parameter passing:** CLI args only (no env vars for command selection). Workflow inputs (target-path, engine-name) passed via `python -m runtime.verify mutation --target <path> --engine <name>` when dispatched.

**Success/failure communication:** Exit codes:
- 0 = pass
- 1 = infrastructure failure / not evaluable
- 2 = quality gate failure (below threshold)
- Workflow step `if: always()` runs classification and sets outputs, then final step checks exit code

### Q6: How does runtime discover what changed?
**Git integration code (orchestrator.py:76-150):**
- `_find_repo_root()` — walks up from __file__ to find backend/pyproject.toml
- `_default_branch()` — tries origin/main, origin/develop, main, develop
- `_merge_base_with_default()` — fetches default branch, computes merge-base, fails closed on fetch failure
- `_collect_changed_files()` — git diff against merge-base
- `_is_git_available()` — checks git presence
- `_filter_changed_files()` — filters generated/cache/binary artifacts

**File-to-module mapping:**
- `capability_resolver._classify_change(file_path)` — TEST_CHANGE, CONFIG_CHANGE, INFRASTRUCTURE_CHANGE, DOCUMENTATION_CHANGE, SOURCE_CHANGE, UNKNOWN
- `change_surface.discover_change_surfaces()` — maps files to change surfaces
- `repository/graph/graph_service.py` — builds dependency graph from scanner outputs
- `repository/scanner/` — backend_scanner, frontend_scanner, api_scanner, test_scanner, workflow_scanner, etc.

**PR boundary detection:**
- Tier 1 (LOCAL): working-tree delta only — never diffs against origin/main
- Tier 2 (PR): GITHUB_BASE_REF or explicit override
- `_resolve_repository_identity()` — commit_sha + branch from git at record time

### Q7: How does runtime select tests?
**Test discovery:**
- `repository/scanner/test_scanner.py` — discovers test files
- `registry/registry.py` — loads verification.yaml, maps units to workflows
- `planner/planner.py` — VerificationPlanner.plan() produces VerificationPlan

**Test filtering/selection:**
- `control_plane.py` — prefers: reusable evidence → targeted → component-specific → capability-specific → property/invariant/contract → targeted mutation → escalation
- `evidence_planner.py` — TaskDisposition: selected_fresh, selected_revalidation, selected_aggregate, excluded_unaffected, excluded_already_certified, excluded_reusable_evidence, excluded_outside_population, excluded_deferred, excluded_not_applicable, blocked_by_drift
- `executor_pipeline.py` — task adapters for kind families: unit, property, invariant, contract, coverage, mutation, golden, capability. Tasks that cannot be safely executed are marked `not_executable_yet`.

**Tier-based test obligation:**
- Tier 1 (LOCAL): working-tree delta only
- Tier 2 (PR): actual PR base/diff
- Tier 3 (DEEP): full-system, mutation/golden/E2E/performance regardless of diff
- UNIT_CATALOG completeness invariant: every unit appears as selected or excluded with reason

### Q8: How does runtime execute tests?
**Subprocess invocation (execution_orchestrator.py:1341-1436):**
```python
proc = subprocess.run(
    command, shell=True, cwd=REPO_ROOT,
    env=child_process_env(), capture_output=True, text=True,
    timeout=spec.timeout_seconds,
)
```

**Timeout/retry logic:**
- `executor.py` — `_max_retries = 3`, `_retry_delay = 1`
- `subprocess.TimeoutExpired` → exit_code=124, CompletionState.TIMEOUT
- Process-group ownership: `os.killpg(pgid, SIGTERM)` → sleep(0.5) → `os.killpg(pgid, SIGKILL)`
- `Executor._kill_process_group()` — kills entire process group on timeout/cancellation

**Output capture and parsing:**
- stdout/stderr written to `runtime/generated/m9-c49/logs/{plan_id}/{task_id}-stdout.log`
- `failure_report.py` — parses pytest short summary, extracts failing node IDs
- Exit code classification: 0→PASS, 124→TIMEOUT, 127/infra signals→INFRASTRUCTURE, else→FAILED


### Q9: What evidence schemas exist?
**Evidence dataclasses with "Evidence" in name:**
1. `VerificationEvidence` (models/model.py:179) — step_id, target_id, type, content, timestamp, status
2. `ExecutionEvidence` (reconciliation.py:437) — canonical execution evidence
3. `CIEvidenceRecord` (ci_evidence.py:85) — CI evidence record
4. `SurvivorEvidence` (strengthening.py:69) — mutation survivor evidence
5. `Evidence` (milestone_state.py:202) — milestone evidence
6. `EvidenceRef` (obligation.py:131) — reference to evidence
7. `EvidenceIntegrityReport` (evidence_integrity.py:52) — integrity report
8. `ContractEvidence` (api_schema_governance.py:46) — contract evidence
9. `EvidenceAwarePlan` (evidence_planner.py:119) — evidence-aware plan
10. `EvidenceContractEntry` (workflow_convergence.py:674) — workflow evidence contract
11. `CoverageEvidence` (system/evidence/models/evidence.py:12) — coverage evidence
12. `MutationEvidence` (system/evidence/models/evidence.py:30) — mutation evidence
13. `TestResultEvidence` (system/evidence/models/evidence.py:51) — test result evidence
14. `EvidenceCollectionResult` (system/evidence/models/evidence.py:140) — collection result
15. `EvidenceArtifact` (system/evidence/collectors/base.py:14) — evidence artifact
16. `EvidenceSummary` (system/evidence/aggregator.py:93) — evidence summary
17. `GapEvidence` (gap_classification.py) — gap evidence

**Versioning strategy:**
- Schema strings: "m9-diagnostic-report/v1", "m9-c56-convergence/v1", "m9-c52-certification/v1"
- Version policy (runtime/VERSION): v1.0.x = bug fixes; v1.1 = backwards-compatible additions; v2.0 = breaking changes
- MutationResult uses run_id + repository_sha + tree_sha for identity (not explicit version)

**Backward compatibility:**
- `EvidenceClassification` enum: AUTHORITATIVE | DERIVED (immutable)
- `MeasurementCompletionStatus` — non-certifiable states are bounded, machine-readable
- Legacy status values ("pass"/"fail") normalized to canonical ("passed"/"failed") via `_normalize_status()`
- Legacy commands routed through canonical control plane with deprecation warnings

### Q10: How is evidence persisted?
**File path generation:**
- Execution logs: `runtime/generated/m9-c49/logs/{plan_id}/{task_id}-stdout.log`
- Mutation summary: `backend/tests/generated/mutation/mutation-summary.json`
- Measurement truth: persisted by mutation_runner alongside summary
- Verification cache: `runtime/generated/verification-cache.json`
- AI runs: `runtime/generated/ai-runs/{run_id}.json`
- Survivor intel: `backend/tests/generated/mutation/mutation-survivor-intel.json`

**Serialization:**
- `json.dumps(data, indent=2, default=str) + "\n"` (cache.py)
- `json.dump(plan_to_dict(plan), f, indent=2, default=str)` (cli.py)
- Dataclasses use `asdict()` for serialization

**Retention/cleanup:**
- No explicit cleanup policy in code
- Retention managed by GitHub Actions upload-runtime action (retention-days: 14-90 depending on artifact)

### Q11: How is evidence reused?
**Cache lookup (cache.py:45-100):**
- Keys: (commit, changed_files, profile) — with content-hash of changed files
- `replay()` — authoritative entry point
- Returns ReplayResult: reusable, overall_status, exit_code, reason
- **Invariant:** exit_code can never be 0 when stored status is "fail"

**Staleness detection:**
- `_compute_tree_digest(changed_files)` — hashes working-tree contents of every changed file
- Fingerprint mismatch → do not reuse
- `PopulationSnapshot.fingerprint()` — content-derived fingerprint
- `MeasurementInvalidation` — explicit conditions: INVALIDATES_COMPONENT, INVALIDATES_CAPABILITY, INVALIDATES_TASK, INVALIDATES_EVIDENCE_ONLY, DOES_NOT_INVALIDATE

**Cache invalidation triggers:**
- Content change on disk (R-CACHE-1 fix)
- Fingerprint mismatch
- Missing/corrupt evidence → re-execute or fail safely
- `decide_reuse()` in evidence_reuse.py — deterministic reuse decision


Q12-Q14

### Q12: How does runtime classify failures?
**Exit code → failure type mapping (execution_orchestrator.py:1395-1436):**
- Exit code 0 → CompletionState.PASS
- Exit code 124 (TimeoutExpired) → CompletionState.TIMEOUT
- FileNotFoundError → CompletionState.INFRASTRUCTURE
- Exit code 127 or infra signals → CompletionState.INFRASTRUCTURE
- Otherwise → CompletionState.FAILED

**Infra signals:** FileNotFoundError, No such file or directory, ModuleNotFoundError, command not found, Permission denied, No such command

**Timeout detection:**
- `subprocess.run(..., timeout=spec.timeout_seconds)`
- `subprocess.TimeoutExpired` → exit_code=124, CompletionState.TIMEOUT

**Infrastructure vs application failure distinction:**
- Infrastructure: command not found, module not found, permission denied, exit 127
- Application: test assertion failure, command exited non-zero (not infra)
- Unknown: cannot establish cause → UNKNOWN_FAILURE, raw diagnostic preserved

**FailureClassification enum (models/model.py:56-73):**
TEST_FAILURE, COMMAND_FAILURE, IMPORT_FAILURE, TIMEOUT, ENVIRONMENT_FAILURE, PLANNING_FAILURE, RECONCILIATION_FAILURE, ARTIFACT_FAILURE, UNKNOWN_FAILURE

### Q13: How does runtime explain failures?
**Failure report generation (failure_report.py):**
- `FailureReport` dataclass: classification, unit_id, command, exit_code, failure_summary, test_failure_count, root_failure, diagnostic, evidence_path
- `_pytest_failed_test_ids(output)` — extracts failing pytest node IDs from "short test summary info" section
- `_count_pytest_failures(summary_text)` — extracts integer count of failed tests
- `_pytest_summary_line(output)` — returns first concise pytest summary line
- `is_import_failure(output)` — regex for ModuleNotFoundError, ImportError, SyntaxError

**Context collection:**
- stdout/stderr captured to log files
- stdout_path, stderr_path in ExecutionResult
- Diagnostic excerpt bounded (not full output)

**Root cause attribution:**
- pytest failures → TEST_FAILURE with root_failure node ID
- Import errors → IMPORT_FAILURE
- Command failures → COMMAND_FAILURE
- Timeout → TIMEOUT
- Unattributable → UNKNOWN_FAILURE with raw diagnostic preserved

### Q14: Can runtime detect regressions?
**Historical evidence comparison:**
- `c42_24_b_measurements()` — 12 components with scored/killed counts from C42.24-B
- `c42_25_measurements()` — 2 intelligence components from C42.25
- `c42_26_population()` — 14-component population snapshot
- `c42_26_derived_aggregate()` — derived aggregate from measurements

**Trend analysis:**
- `DerivedAggregate` — computed from authoritative component measurements
- `ComponentMeasurement.summary` — scored, killed, mutation_score_pct per component
- Population-level comparison via fingerprints

**Regression alert mechanism:**
- Stale evidence detection → INVALIDATED disposition → re-execution required
- `MeasurementInvalidation` — explicit conditions for when evidence must be re-measured
- `decide_reuse()` — deterministic decision on whether evidence remains valid
- Fingerprint mismatch → do not reuse → fresh execution

Q15

### Q15: How is mutation testing integrated?
**Mutant generation invocation (mutation_runner.py):**
- `python -m runtime.verify mutation` — authoritative full campaign
- `python -m runtime.verify mutation --smoke` — bounded infra health check
- `python -m runtime.verify mutation --target <engine>` — incremental
- `python -m runtime.verify mutation --restore` — restore mutated source only
- Uses mutmut 3.7.0 (pinned), executes via `execute_mutation()` in mutation_runner.py

**Three-gate classification (mutation_contract.py:398 classify_gates):**
- Gate A (Execution): PASS | INFRASTRUCTURE_FAILURE — did the pipeline run?
- Gate B (Evidence): PASS | FAIL — is evidence complete?
- Gate C (Quality): True | False — does score meet 80% threshold?

**Survivor catalog persistence (mutation_runner.py:1028-1072):**
- `run_catalog_cli(BACKEND_DIR / "mutants", BACKEND_DIR, out_path=catalog_path)` — survivor breakdown
- `build_survivor_intel(...)` + `write_survivor_intel(...)` — durable survivor intelligence
- Persisted to `backend/tests/generated/mutation/mutation-survivors.json` and `mutation-survivor-intel.json`

### Q16: How are mutation results used?
**Threshold enforcement (mutation_runner.py:1074-1084):**
- Gate A or B failed → exit 1 (NOT EVALUABLE, never a score)
- Full mode + Gate C True → exit 0
- Full mode + Gate C False → exit 2 (below threshold)
- Smoke/target → exit 0 if A & B pass (quality NOT gated)

**CI gate integration (mutation.yml:136-226):**
- mutation_evaluated=true && exit_code=0 → "Mutation score meets threshold"
- mutation_evaluated=true && exit_code=2 → "Mutation score below threshold"
- mutation_evaluated=false → "MUTATION NOT EVALUATED — infrastructure/evidence failure, NOT a 0% quality result"

**Developer feedback mechanism:**
- Survivor intel: what mutated → covering tests → classification → capability → fingerprint → recommendation
- Convergence pipeline: generates test code to kill survivors, applies, validates
- Diagnostic agent: explains failures with closed verdict vocabulary

### Q17: What AI/LLM integration exists?
**Agent/orchestrator interfaces (agents.py, orchestrator.py):**
- `AIOrchestrator` — run lifecycle management (start_run, get_run, list_runs, execute_step)
- `Agent` base class — name, description, authority_level, enabled, can_execute(), execute()
- `DiagnosticAssistantAgent` — authority level 1, enabled by default
  - Pipeline: SYMPTOM → ENGINE → CHANGE INTELLIGENCE → HISTORY → EVIDENCE → CONTEXT PACK → MODEL → INTERPRETATION
  - Distinguishes FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION

**Prompt construction (context/builder.py):**
- `ContextBuilder` — builds deterministic, reproducible context packs
- `build_context_pack(symptom, capability_id, run_id, intent_type)` — convenience function
- Context pack components: change intelligence, history, evidence, diagnostics, repository context
- Context pack kind: "platform.context_pack"

**Tool/action registry (tools/__init__.py, handlers.py):**
- `ToolRegistry` — get, list_tools, invoke, get_tool_schema
- `register_builtin_tools()` — registers Level 0 (observe) and Level 1 (governed write) handlers
- Level 0 handlers: inspect_health, inspect_capability, inspect_architecture, inspect_errors, inspect_history, inspect_evidence, inspect_file, inspect_capabilities
- Level 1 handlers: run_verification_capability, run_capability_group
- Tool path: Tool Registry → Policy Engine → Platform API Service → C50 Authority
- No direct AI → executor / DB / shell / filesystem mutation

**LLM providers (providers/):**
- `ModelProvider` Protocol — provider interface
- `BaseProvider` ABC — base implementation
- `ModelRouter` — register, get_provider, list_providers, route
- `LocalOllamaProvider`, `LocalLargeProvider`, `OpenRouterProvider`, `DeterministicFallbackProvider`
- `AIConfig` — provider configs, model settings

### Q18: How would AI consume runtime outputs?
**Structured data formats:**
- Context packs: "platform.context_pack" kind with change intelligence, history, evidence, diagnostics
- Diagnostic reports: "m9-diagnostic-report/v1" schema with 9 questions + closed verdicts
- Certification reports: "m9-c52-certification/v1" with 30 gates
- Convergence results: "m9-c56-convergence/v1" with generated tests, survivors killed
- Mutation results: MutationResult with killed/survived/no_tests/timeout/suspicious/not_checked
- Evidence: EvidenceListItem, EvidenceDetailEnvelope (Pydantic models in platform/api/contracts/evidence.py)

**API/interface for AI to invoke runtime:**
- `ToolRegistry.invoke(tool_name, arguments)` — governed tool invocation
- Platform API services (platform/api/services/) — capabilities, change, evidence, executions, health, history, architecture, tasks, verification
- Tool handlers route through Platform API Service → C50 Authority

**Feedback loop:**
- AI suggestion → ContextPack → DiagnosticAssistant → structured interpretation
- Convergence pipeline: DISCOVER → CLASSIFY → GENERATE → APPLY → VALIDATE → REPORT
- AI never modifies production code (diagnostic_agent.py: "it never modifies production code")
- AI never overwrites deterministic evidence (agents.py: "model is not authoritative")

Q19

### Q19

### Q19: How does runtime validate itself?
**Self-tests (tests of the runtime):**
- 107 test files in `runtime/tests/` — all reference runtime/verify
- `test_m9c57_verification_self_contract.py` — O2-D reconciliation (profiles ↔ verification.yaml)
- `test_m9c57_outcome_semantic_contract.py` — O-2 outcome vocabulary contract
- `test_m9c57_observability_convergence.py` — observability convergence
- `test_m9_c50_self_verification.py` — runtime self-verification
- `test_m9_c50_stop_gate2_obligation_reconciliation.py` through `stop_gate9_failure_modes.py`
- `test_m9_c50_final_governance.py` — final governance
- `test_vea5_*` — VEA-5 tests

**Invariant checks:**
- `VerificationSummary.__post_init__` — arithmetic: passed + failed + skipped == total_tasks
- `MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE` — only state consumable by certification
- `_NON_CERTIFIABLE` set — 7 non-certifiable states
- Cache integrity: exit_code can never be 0 when stored status is "fail"
- UNIT_CATALOG completeness invariant: every unit appears as selected or excluded

**Bootstrap problem solution:**
- `python -m runtime.verify env-check` — canonical environment check
- `python -m runtime.verify doctor` — framework health/integrity
- `python -m runtime.verify mutation --smoke` — bounded mutation infra smoke
- Runtime tests itself via `python -m runtime.verify runtime` (verification-runtime.yml)
- Canonical execution model: `python -m runtime.verify <command>` from repo root through .venv

### Q20: What are the known limitations?
**TODOs/FIXMEs/HACKs (only 2 found):**
1. `runtime/foundation/verification/capability_graph_resolver.py:14` — "planner (planner.py:382-388 TODO closure)"
2. `runtime/foundation/verification/planner/planner.py:383` — "# TODO Program 7: implement graph-based capability resolution"

**Incomplete features:**
- `runtime/system/financial/`, `runtime/system/graph/`, `runtime/system/timeline/`, `runtime/system/command/` — README.md only, no Python implementation
- `runtime/system/evidence/aggregator_obsolete_disposition.py` — explicitly marked obsolete
- `runtime/system/context/` — TypeScript implementation (separate from Python runtime)
- `runtime/program16_analysis.py` (66K lines) — likely auto-generated analysis dump
- Multiple `analyze_*.py` scripts at runtime root — analysis tools, not core framework

**Documented assumptions/constraints:**
- Mutation full campaign takes ~27 minutes (documented constraint: mutation.only_when_threshold_confident)
- No repository-wide mutation rerun unless formal campaign gate requires it (c42_37_hard_constraints)
- No duplicate frameworks (m9_c57_no_duplicate_frameworks)
- Normal operation must not require PYTHONPATH or sys.path manipulation (m9_c57_normal_op_no_pythonpath)
- Pre-existing errors must be fixed rather than deferred (pre_existing_error_backlog_policy)
- Only run full mutation when confident >80% threshold will be reached
- Long verification runs are not assumed to be hangs (correction: long_run_not_hang)
- Do not assume unused code is dead (correction: dead_code_removal_policy)

final sections

---

## SECTION 17: RUNTIME DEPENDENCY GRAPH

```
verify.py (thin shim)
  └── control_plane_facade.main() [SINGLE public command surface]
        ├── canonical_control_plane [CLI tree: 9 operations]
        ├── certification.main() [30 gates G1-G30]
        ├── control_plane [ControlPlanePlanner → ControlPlanePlan]
        ├── evidence_planner [EvidenceAwarePlanner → EvidenceAwarePlan]
        ├── execution_orchestrator [ExecutionOrchestrator → ExecutionReport]
        │     ├── capability_contract [CapabilityContractRegistry]
        │     ├── capability_resolver [CapabilityResolution]
        │     ├── change_surface [ChangeSurfaceAnalysis]
        │     ├── command_inventory [CommandInventory]
        │     ├── evidence_reuse [ComponentMeasurement, PopulationSnapshot]
        │     ├── graph_model [VerificationGraph]
        │     ├── measurement_truth [MeasurementKind]
        │     ├── obligation [ObligationSet, Disposition]
        │     ├── registry [VerificationRegistry]
        │     ├── shared_impact [SharedDependencyIndex]
        │     ├── strengthening [StrengtheningPipeline]
        │     └── executor_pipeline [ExecutableVerificationTask, EvidenceCapture]
        ├── intelligence [analyze, format_diagnostic]
        │     └── intelligence.platform [blast, change, optimizer, attribution, risk, cost]
        ├── measurement_truth_integration [MeasurementTruthIntegrator]
        └── obligation [Change, Capability, Requirement, VerificationObligation]

orchestrator.py [Verification Orchestrator]
  ├── executor [Executor: subprocess, retry, timeout, process-group]
  ├── failure_report [FailureReport, FailureClassification]
  ├── models [VerificationPlan, ExecutionResult, VerificationSummary]
  ├── planner [VerificationPlanner: pure planning]
  │     └── repository.graph.graph_service [RepositoryGraphService]
  ├── profiles [VerificationProfile: immutable task lists]
  └── registry [VerificationRegistry: loads verification.yaml]

planner/planner.py [VerificationPlanner]
  └── repository.graph.graph_service [RepositoryGraphService]

executor_pipeline.py [Executable Plan + Adapters + Evidence]
  ├── env [child_process_env, hash_file, resolve_environment]
  ├── evidence_planner [EvidenceAwarePlan, PlannedTask]
  ├── evidence_reuse [ComponentMeasurement, PopulationSnapshot, decide_reuse]
  ├── mutation_contract [ENGINE_SELECTION, classify_gates, compute_score]
  ├── mutation_runner [execute_mutation]
  ├── executor [Executor]
  ├── failure_report [build_failure_report]
  ├── models [ExecutionResult, FailureClassification]
  └── registry [VerificationRegistry]

mutation_runner.py [Canonical Mutation Runner]
  ├── env [PINNED_MUTMUT, REPO_ROOT, VENV_BIN, resolve_environment]
  ├── measurement_truth [EvidenceClassification, FailureClassification, MeasurementTruthRecord]
  ├── mutation_contract [ENGINE_SELECTION, MutationResult, classify_gates, compute_score]
  ├── survivor_catalog [run_catalog_cli]
  └── survivor_intel [build_survivor_intel, write_survivor_intel]

diagnostic_agent.py [Diagnostic & Forensic Agent]
  ├── evidence_planner [EvidenceAwarePlanner]
  ├── evidence_reuse [decide_reuse]
  ├── executor_pipeline [ForensicExecutionRecord]
  ├── measurement_truth [MeasurementTruthRecord]
  └── reconciliation [ReconciledVerificationState]

blast_radius.py [Canonical Blast-Radius Contract]
  ├── capability_contract [CapabilityContractRegistry]
  ├── capability_resolver [CapabilityResolution, resolve_capabilities]
  ├── change_surface [ChangeSurfaceAnalysis, discover_change_surfaces]
  ├── command_inventory [CommandInventory]
  ├── evidence_reuse [ComponentMeasurement, PopulationSnapshot]
  └── shared_impact [SharedDependencyIndex]

tier.py [Tier-Aware Planning]
  ├── intelligence.platform.blast [compute_blast_radius]
  ├── intelligence.platform.change [analyze_changes]
  ├── intelligence.platform.optimizer [optimize_verification, VerificationPlanIntel]
  └── orchestrator [_filter_changed_files]

convergence_pipeline.py [Autonomous Convergence]
  ├── survivor_intel [build_survivor_intel]
  ├── test_generator [generate_tests]
  └── mutation_runner [execute_mutation]

platform/ai/ [AI Platform]
  ├── orchestrator [AIOrchestrator: run lifecycle]
  ├── agents [Agent, DiagnosticAssistantAgent]
  ├── tools [ToolRegistry, register_builtin_tools]
  │     └── handlers [LEVEL_0_HANDLERS, LEVEL_1_HANDLERS]
  ├── providers [ModelRouter, BaseProvider, LocalOllamaProvider, OpenRouterProvider]
  ├── config [AIConfig, load_config]
  ├── context [ContextBuilder, build_context_pack]
  │     ├── builder [ContextBuilder]
  │     ├── cache [ContextCache]
  │     ├── trimmer [ContextTrimmer]
  │     ├── serializer [ContextSerializer]
  │     ├── ranker [ContextRanker]
  │     └── provenance [ContextProvenance]
  ├── intent [IntentClassifier]
  ├── policy [PolicyEngine]
  ├── planner [AIPlanner]
  ├── runs [RunTracker]
  └── memory [AIMemory]

platform/api/ [Platform API]
  ├── contracts [Pydantic models: Evidence, Capability, Architecture, etc.]
  └── services [build_* functions: capabilities, change, evidence, executions, etc.]

system/evidence/ [Evidence System]
  ├── collectors [EvidenceCollector ABC, CoverageCollector, MutationCollector, etc.]
  ├── ingestion [EvidenceIngestionPipeline]
  ├── models [CoverageEvidence, MutationEvidence, VerificationEvidence]
  ├── aggregator [EvidenceAggregator, EvidenceSummary]
  └── api [evidence API endpoints]

system/observability/ [Observability]
  ├── event_store [EngineeringEventStore, create_event]
  ├── execution_context [create_context]
  ├── repository [LocalMetricsRepository, RunRecord]
  ├── analytics [AnalyticsEngine]
  ├── cost_analysis [CostAnalysis]
  ├── dashboard [Dashboard]
  ├── health_report [HealthReport]
  ├── outcome [OutcomeTracker]
  └── flaky_tests [FlakyTestDetector]
section 18

---

## SECTION 18: CRITICAL GAPS OBSERVED

### 18.1 Architectural Complexity
- **162,932 lines** across 503 Python files — massive surface area
- **2,662-line** `workflow_convergence.py` — single file larger than most frameworks
- **2,280-line** `executor_pipeline.py` — God file pattern
- **2,108-line** `execution_orchestrator.py` — God file pattern
- **66,362-line** `program16_analysis.py` — auto-generated dump, not actively maintained
- Multiple `analyze_*.py` scripts at runtime root — analysis tools, not core framework

### 18.2 Redundancy & Duplication
- `runtime/system/evidence/` and `runtime/foundation/verification/` both have evidence models — potential duplication
- `runtime/foundation/verification/models/model.py` and `runtime/system/evidence/models/evidence.py` — overlapping evidence concepts
- `runtime/platform/api/contracts/` and `runtime/foundation/verification/api_contracts/` — overlapping contract concepts
- `runtime/foundation/audit/` and `runtime/foundation/verification/` — overlapping audit/verification concerns
- `runtime/foundation/repository/` and `runtime/foundation/intelligence/` — overlapping repository intelligence

### 18.3 Integration Gaps
- `runtime/system/financial/`, `runtime/system/graph/`, `runtime/system/timeline/`, `runtime/system/command/` — README.md only, no Python implementation
- `runtime/system/context/` — TypeScript implementation (separate from Python runtime, potential integration gap)
- `runtime/system/evidence/aggregator_obsolete_disposition.py` — explicitly marked obsolete but still present
- Only 2 TODOs found in 162K lines — suggests incomplete features are not documented as TODOs

### 18.4 Hardcoded Assmutations
- 80% mutation threshold hardcoded in `mutation_contract.py:88`
- Backend coverage threshold: 40% (relatively low, may be too permissive)
- Backend mutation threshold: 60% (different from full campaign 80%)
- `c42_24_b_measurements()` — hardcoded measurement data (12 components with specific scored/killed counts)
- `c42_25_measurements()` — hardcoded measurement data (2 components)
- `c42_26_population()` — hardcoded population snapshot

### 18.5 Bootstrap Problem
- Runtime must verify itself but has no special bootstrap mechanism
- `python -m runtime.verify runtime` runs runtime self-verification
- Canonical execution model prevents direct script execution (platform module shadowing)
- Environment resolution via `env.py` — single source of truth for toolchain

### 18.6 Evidence Provenance Gaps
- No explicit evidence cleanup/retention policy in code (managed by GitHub Actions)
- Some evidence schemas lack version fields (MutationResult uses run_id + sha, not explicit version)
- Legacy status values ("pass"/"fail") require normalization to canonical ("passed"/"failed")
- Evidence reuse decisions are deterministic but rely on hardcoded measurement data

### 18.7 AI Integration Gaps
- AI platform is separate from verification pipeline (not deeply integrated)
- `DiagnosticAssistantAgent` has authority_level=1 (enabled by default) but cannot modify production code
- `DeterministicFallbackProvider` — when no LLM available, falls back to deterministic
- Context packs are built but AI consumption is limited to diagnostic interpretation
- No feedback loop from AI suggestions back to verification pipeline (one-way: AI observes, doesn't act)

### 18.8 Performance Concerns
- Full mutation campaign: ~27 minutes (documented constraint)
- No parallel execution of independent verification tasks in the orchestrator
- Cache invalidation requires content-hash of all changed files (could be expensive for large PRs)
- No incremental verification beyond targeted mutation

### 18.9 Testing Gaps
- 107 test files — good coverage of runtime itself
- But tests are milestone-specific (m9_c42_27 through m9_c57) — may not cover all code paths
- `test_m9c57_verification_self_contract.py` — reconciliation test between profiles and verification.yaml
- No performance/load tests for the runtime itself
- No fuzz testing of evidence schemas

### 18.10 Security Considerations
- No authentication/authorization for verification execution (beyond authority levels in AI agents)
- No encryption of evidence artifacts
- No secrets management (env vars used directly)
- Tool handlers have Level 0 (read-only) and Level 1 (governed write) — no Level 2+ for destructive operations
- `allow_dirty` flag in mutation runner — could allow execution on dirty worktree

### 18.11 Observability Gaps
- No dedicated logging module (uses stdlib logging)
- No structured logging format (JSON logs)
- No distributed tracing
- Event store is local JSONL only (no external metrics backend)
- No alerting mechanism for regression detection

