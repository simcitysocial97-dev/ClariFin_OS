# M9-C49 — Verification Execution Orchestration & End-to-End Pipeline Enforcement

**Phase:** C49 — Verification Execution Orchestration & End-to-End Pipeline Enforcement  
**Date:** 2026-08-31  
**Status:** CERTIFIED  
**Baseline:** M9-C48 Capability Operationalization & Verification Control Plane (certified)

---

## 1. Objective Achieved

C48 answered "what should I run?" C49 answers "run it, observe it, understand the result, determine what happens next, and stop when defensible evidence is sufficient."

The end-to-end chain is now executable end-to-end:

> **Repository Change → Capability Resolver → Blast Radius → Evidence Invalidation/Reuse → Control-Plane Plan → Execution Orchestrator → Verification Capabilities → Measurement Truth → Diagnostic / Survivor Intelligence → Strengthening when justified → Targeted Revalidation → Certification / Escalation**

No second planner, registry, evidence store, cache, capability system, or measurement system was introduced. The orchestrator consumes the C48 control plane and drives the existing C42/C47/C45 verifiers.

---

## 2. Implementation Summary

### New Canonical Modules (2 files)

| Module | Purpose |
|--------|---------|
| `runtime/foundation/verification/execution_orchestrator.py` | M9-C49 core: ExecutionPlan contract, ExecutionOrchestrator, structured TaskExecutionRecord, ExecutionReport, efficiency metrics, final decision logic, diagnostic + authorization boundary |
| `runtime/foundation/verification/shared_impact.py` | Deterministic AST-based shared-module dependency index (closes the C48 "endpoint/capability resolution incomplete" gap for shared infrastructure changes) |

### Extended Existing Modules (1 file)

| Module | Extension |
|--------|-----------|
| `runtime/foundation/verification/capability_resolver.py` | Added PLANNER_CAPABILITY_ALIASES (planner vocabulary → registry vocabulary), integrated shared-impact index, added `capability_sources` and `unmapped_blast_capabilities` to CapabilityResolution for machine-readable shared-impact provenance |

### Extended CLI (1 file)

| File | Extension |
|------|-----------|
| `runtime/verify.py` | Added 4 new CLI commands: `execution-plan`, `execute`, `execution-status`, `execution-report` |

### New Tests (1 file, 16 tests)

| File | Tests |
|------|-------|
| `runtime/tests/test_m9_c49.py` | 16 tests covering scenarios A–M + determinism + stop-on-sufficiency + plan validation |

---

## 3. Architecture & Design Contract

### Execution Plan Contract (`ExecutionPlan`)

Every plan has:

* `plan_id` (content-derived fingerprint, never timestamp)
* `source_plan_id` (C48 control-plane plan_id it consumes)
* `repository_fingerprint` (repo SHA + working-tree hash + config hash + toolchain hash + composite)
* `changed_files`, `affected_capabilities`, `affected_components`
* `invalidated_evidence`, `reusable_evidence` (from C48 resolution)
* `tasks` — ordered list of `ExecutionTaskSpec`
* `revalidation_sources` — every measurement record that was stale/missing/non-certifiable
* `reusable_measurements` — every persistent record reused without re-execution
* `escalation_conditions`, `measurement_requirements`, `certification_requirements`
* `plan_fingerprint` — sha256 over the above (excludes `generated_at`)
* `generated_at` — display only

### Execution Task Contract (`ExecutionTaskSpec`)

* `task_id`, `source_task_id` (C48 task ID + capability)
* `capabilities` (tuple; one execution can serve multiple capabilities)
* `verification_kind` (unit/contract/property/coverage/mutation/integration/golden/e2e + `revalidation` origin)
* `command`, `profile`, `scope`
* `is_mandatory`, `is_escalation`, `origin` (`control_plane` or `revalidation`)
* `prerequisites`, `depends_on`
* `expected_evidence`, `measurement_required`, `escalation_conditions`
* `authorization_required` (only mutation / revalidation mutation)
* `timeout_seconds`, `failure_policy` ("diagnose_then_stop")
* `evidence_reused`, `evidence_invalidated`
* `mutation_target` (when kind == mutation)

### Determinism

Two calls with the same repository state + same control-plane input produce:
* identical `plan_fingerprint`
* identical `plan_id`
* identical task ordering (sorted by `mandatory` then `primary_capability` then `command`)
* identical dedup decisions (one command = one task, even if multiple capabilities require it)

`generated_at` is excluded from every fingerprint.

### Repository Fingerprint

Captures: `git rev-parse HEAD`, working-tree hash of `backend/src/`, backend+root `pyproject.toml` hashes, toolchain versions (Python, pytest, mutmut). Composite sha256. If the live fingerprint no longer matches the plan's fingerprint, `VALIDATION_BLOCKED` and no execution.

---

## 4. Stopping Rules (Section 6)

The orchestrator applies these deterministic rules during execution:

| Condition | Action | Decision |
|-----------|--------|----------|
| All mandatory tasks PASS or REUSED, no escalation needed | Skip escalation tasks with state `SKIPPED` | proceed to certification gate |
| Mandatory task FAILED | Diagnostic path, declared next action | `DIAGNOSTIC` |
| `TIMEOUT` (exit 124) | Never convert to PASS | `TIMEOUT_BLOCKED` |
| `INFRASTRUCTURE` (FileNotFoundError, ModuleNotFoundError, exit 127) | Never convert to PASS | `INFRASTRUCTURE_BLOCKED` |
| `AUTHORIZATION_REQUIRED` (mutation revalidation without explicit `--authorize`) | No production changes attempted | `AWAITING_AUTHORIZATION` |
| `SCOPE` or fingerprint mismatch mid-run | Abort, no further tasks | `VALIDATION_BLOCKED` |
| Stale measurement record (repo SHA mismatch) | Inject revalidation task (mandatory if `required_for_certification`) | proceeds |
| Missing authoritative certifiable measurement | Inject revalidation task (mandatory if `required_for_certification`) | proceeds |

### Certification Gate

When all mandatory tasks pass, the orchestrator checks every certification requirement:

* mutation score ≥ threshold
* record's `repository_sha` == current repo SHA
* record is `AUTHORITATIVE_COMPLETE` per C47 measurement truth

If all satisfied → `CERTIFIED`. Otherwise → `NOT_CERTIFIABLE` with a machine-readable list of gaps.

---

## 5. Mutation Subordinate to Orchestration

Mutation is *one* capability among many, never auto-executed:

* Targeted mutation runs only as a `revalidation` task (origin=`revalidation`).
* Full mutation campaigns require explicit `--authorize all` or `--authorize <task_id>`.
* Mutation revalidation tasks are always `authorization_required=True`.
* The orchestrator routes mutation tasks through the native mutmut runner (subprocess + scope enforcement) and produces a C47 `MeasurementTruthRecord` for the result.
* Without authorization, the orchestrator never invokes `execute_mutation`; it records `AUTHORIZATION_REQUIRED` and stops at the boundary.

---

## 6. Evidence Reuse

For every measurement-kind task (mutation, coverage), the orchestrator checks the persistent record *before* executing:

* Record exists, `certification_gate(record) == True`, `record.repository_sha == current SHA` → mark `REUSED`, reference the record in the task's `measurement_truth` field, no execution.
* Record exists but stale (SHA mismatch) → inject revalidation task with reason "evidence stale".
* No record or not certifiable → inject revalidation task with reason "no authoritative certifiable measurement record found".

---

## 7. Observability

Every execution produces a structured `TaskExecutionRecord` containing:

```
record_id, plan_id, task_id, primary_capability, capabilities,
command, scope, is_mandatory, is_escalation, verification_kind,
started_at, completed_at, duration_seconds, exit_code, completion_state,
stdout_path, stderr_path, artifacts, measurement_truth, diagnostic, next_action,
reason, prerequisites_satisfied
```

Reports are persisted to `runtime/generated/m9-c49/reports/<report_id>.json` and `runtime/generated/m9-c49/latest-report.json`. Logs are persisted to `runtime/generated/m9-c49/logs/<plan_id>/<task_id>-stdout.log` and `<task_id>-stderr.log`.

The CLI exposes:
* `verify.py execution-plan <files...>` — build + persist a plan
* `verify.py execute <files...> [--plan <path>] [--authorize all] [--dry-run]` — execute
* `verify.py execution-status [--plan <id> | --latest]` — summary
* `verify.py execution-report [--plan <id> | --latest] [--json]` — full report

---

## 8. Shared-Impact Resolution (C48 Gap Fix)

The C48 audit flagged: "Endpoint/capability resolution incomplete in CrossLayerImpactPlanner." C49 adds:

* `runtime/foundation/verification/shared_impact.py` — deterministic AST import analysis over `backend/src/`. Builds a file→backend-module import map, then a capability→module membership map, then a transitive DAG closure. The result: for any changed repo-relative path, the exact set of capabilities that depend on it.
* `PLANNER_CAPABILITY_ALIASES` in `capability_resolver.py` — deterministic vocabulary bridge from frontend-knowledge capability IDs (`useLoansCapability`) to verification-registry capability IDs (`loan-engine`).

Scenario K (shared service change to `backend/src/services/loan_service.py`) now produces:

```
direct: ['api-contracts']
transitive: ['loan-engine']
sources: {'loan-engine': ['blast:useLoansCapability -> loan-engine']}
```

The chain is machine-readable: a future LLM Guardian can trace exactly why each capability was selected.

---

## 9. Acceptance Scenario Results (16/16 PASS)

| # | Scenario | Test | Result |
|---|----------|------|--------|
| A | Isolated backend change | `ScenarioAIsolatedBackendChange` | PASS |
| B | Cross-capability change | `ScenarioBCrossCapabilityChange` | PASS |
| C | Unaffected capability reuse | `ScenarioCUnaffectedCapabilityReuse` | PASS |
| D | Stale evidence | `ScenarioDStaleEvidence` | PASS |
| E | Targeted test failure | `ScenarioETargetedTestFailure` | PASS |
| F | Mutation survivor | `ScenarioFMutationSurvivor` | PASS |
| G | Coverage regression | `ScenarioGCoverageRegression` | PASS |
| H | Infrastructure failure | `ScenarioHInfrastructureFailure` | PASS |
| I | Timeout | `ScenarioITimeout` | PASS |
| J | Authorization boundary | `ScenarioJAuthorizationBoundary` | PASS |
| K | Shared infrastructure change | `ScenarioKSharedInfrastructure` | PASS |
| L | Workflow failure → capability | `ScenarioLWorkflowFailureMappedToCapability` | PASS |
| M | Successful complete flow | `ScenarioMSuccessfulCompleteFlow` | PASS |
| — | Determinism | `DeterminismTests` | PASS |
| — | Stop-on-sufficiency | `StopOnSufficiencyTests` | PASS |
| — | Plan validation | `PlanValidationTests` | PASS |

---

## 10. Regression Validation

| Suite | Tests | Result |
|-------|-------|--------|
| `test_m9_c42_27` | 38 | PASS |
| `test_m9_c42_28` | 24 | PASS |
| `test_m9_c42_29/30/31` | 82 | PASS |
| `test_measurement_truth` | 23 | PASS |
| `test_survivor_intel` | 12 | PASS |
| `test_affected` | 4 | PASS |
| `test_cross_layer_planner` | 25 | PASS |
| `test_snapshots` | 11 | PASS |
| **Total pre-existing** | **219** | **PASS** |

No pre-existing tests were modified. No production code was deleted. No parallel architecture was introduced.

---

## 11. Efficiency Measurements (Section 16)

Sample run for `backend/src/engines/loan_engine/amortization.py`:

```
Total available tasks (command inventory): 75
Tasks selected by control plane: 8
Tasks executed: 7
Tasks reused: 0
Tasks skipped (stop-on-sufficiency): 0
Tasks awaiting authorization: 1 (mutation revalidation)
Blind total commands: 11
Unnecessary execution avoided: 4
Execution time: ~17s
```

vs blind full verification: the orchestrator selected 8 out of 75 (10.6%), avoiding 89.4% of available tasks. The 4 "unnecessary_avoided" figure measures the dedup benefit (one execution serves multiple capabilities).

---

## 12. Known Boundaries (Authoritative)

* Full mutation campaigns for P0 engines remain an explicit escalation. C49 does not auto-execute them.
* Coverage measurement revalidation for non-required-for-certification mappings is non-mandatory.
* Frontend knowledge capability IDs that have no verification-registry mapping (e.g., `useAccountsCapability`) are recorded in `unmapped_blast_capabilities` and excluded from the plan. This is an explicit boundary, not a silent drop.
* `verify.py env-check` is the canonical pre-flight; the orchestrator runs it implicitly via `verify_prerequisites`.

---

## 13. C49 Durable Evidence

* `runtime/generated/m9-c49/EXECUTION_PROGRESS.md` — this file
* `runtime/generated/m9-c49/certification.json` — machine-readable certification
* `runtime/generated/m9-c49/plans/<plan_id>.json` — persisted ExecutionPlans
* `runtime/generated/m9-c49/reports/<report_id>.json` — persisted ExecutionReports
* `runtime/generated/m9-c49/latest-report.json` — most recent report
* `runtime/generated/m9-c49/logs/<plan_id>/<task_id>-{stdout,stderr}.log` — per-task logs
* `runtime/generated/m9-c49/measurements/measurement-truth-<cap>-<kind>.json` — measurement truth records produced by revalidation tasks

---

## 14. Post-C49 Readiness

The verification framework is now an **autonomous deterministic verification execution system** with:

* automatic capability resolution (C48)
* automatic plan generation (C48)
* automatic execution with stop rules and authorization boundaries (C49)
* automatic measurement truth production (C47)
* automatic diagnostic + strengthening (C48)
* automatic certification decision (C47 + C49)

A future LLM Guardian can consume the `ExecutionReport` JSON to understand:
* what was decided
* what was executed
* what passed, what failed
* what evidence was reused
* what was escalated
* what requires human authorization

without needing to know which internal command or capability to invoke.
