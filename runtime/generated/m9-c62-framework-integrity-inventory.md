# M9-C62 Phase B — Framework Integrity Inventory

**Execution Record** — Authoritative Audit Phase  
**Started:** 2026-09-18T03:29:23Z  
**Branch:** `m9c9-merge-authorization-resolution`  
**Base Commit:** `2fca4854` (M9-C61: Converge cross-layer contract normalization)

---

## 1. Planning Authority Inventory

| Component | File | Status | Layer | Invocation Path | Dependencies | Callers | CLI Exposure |
|-----------|------|--------|-------|-----------------|--------------|---------|--------------|
| **ControlPlanePlanner** | `runtime/foundation/verification/control_plane.py` | **ACTIVE_CANONICAL** | TOP-LEVEL | `ControlPlanePlanner.plan()` | EvidenceAwarePlanner, VerificationPlanner, CapabilityContractRegistry, VerificationGraph | ControlPlaneFacade.check(), ControlPlaneFacade.plan() | `verify check`, `verify plan` |
| **EvidenceAwarePlanner** | `runtime/foundation/verification/evidence_planner.py` | **ACTIVE_SPECIALIZED** | SUBORDINATE | `EvidenceAwarePlanner.plan()` | VerificationGraph, PopulationSnapshot, ComponentMeasurement | ControlPlanePlanner (internal) | Not directly exposed |
| **VerificationPlanner** | `runtime/foundation/verification/planner/planner.py:73` | **ACTIVE_SPECIALIZED** | SUBORDINATE | `VerificationPlanner.plan()` | VerificationRegistry, RepositoryGraphService | ControlPlanePlanner (internal), VerificationOrchestrator | `verify plan` (via planner CLI) |
| **CrossLayerImpactPlanner** | `runtime/foundation/verification/planner/planner.py:881` | **ACTIVE_SPECIALIZED** | SUBORDINATE | `CrossLayerImpactPlanner.analyze_cross_layer_impact()` | Chain map (architecture provider), cross-layer-graph.json | VerificationOrchestrator, ControlPlanePlanner (via resolution) | Not directly exposed |

**Key Finding:** The architecture is **LAYERED**, not competing. ControlPlanePlanner is the canonical top-level planner that composes EvidenceAwarePlanner and VerificationPlanner. CrossLayerImpactPlanner provides blast-radius enrichment to VerificationOrchestrator.

---

## 2. Execution Authority Inventory

| Component | File | Status | Actual Imports/Callers | Notes |
|-----------|------|--------|------------------------|-------|
| **ExecutionOrchestrator** (C49) | `runtime/foundation/verification/execution_orchestrator.py` | **ACTIVE_CANONICAL** | ControlPlaneFacade.check(), ControlPlaneFacade.run() | Consumes C48 ControlPlanePlan, drives to FinalDecision |
| **ExecutionOrchestrator** (decomposed) | `runtime/foundation/verification/orchestration/orchestrator.py` | **HISTORICAL/DECOMPOSED** | NOT imported by facade | Decomposed version, models moved to orchestration/models.py |
| **VerificationOrchestrator** (Program 7B) | `runtime/foundation/verification/orchestrator.py` | **ACTIVE_CANONICAL** (Program 7B) | VerificationOrchestrator.run(), capability_catalog, bypass_enforcement | Consumes CrossLayerImpactPlanner + VerificationPlanner, produces VerificationReport |
| **MutationOrchestrator** | `runtime/foundation/verification/mutation_execution/orchestrator.py` | **ACTIVE_SUPPORTING** | ExecutionOrchestrator (for mutation tasks) | Specialized mutation execution |
| **Executor Pipeline** | `runtime/foundation/verification/executor_pipeline.py` | **ACTIVE_SUPPORTING** | ExecutionOrchestrator (via adapters) | M28.28+ adapter layer for evidence capture |

**Key Finding:** Two active orchestrators exist for different purposes:
1. **ExecutionOrchestrator** (C49) — canonical C48 plan consumer, drives to certification decision
2. **VerificationOrchestrator** (Program 7B) — git-aware changed-file detection + cross-layer impact + VerificationPlanner → VerificationReport

They serve different entry points: `verify check`/`verify run` → ExecutionOrchestrator; legacy profiles → VerificationOrchestrator.

---

## 3. Evidence Path Trace

| Stage | Implementation | Authority | Consumers |
|-------|---------------|-----------|-----------|
| verification execution | ExecutionOrchestrator.execute() | ExecutionOrchestrator | ControlPlaneFacade, CLI |
| ExecutionEvidence | `executor_pipeline.py:639` | Executor Pipeline | Reconciliation, Forensic Record |
| EvidenceCollector | `executor_pipeline.py` (implicit) | Executor Pipeline | - |
| events | `runtime/system/observability/event_store.py` | EngineeringEventStore | Analytics, History, Platform Console |
| RunRecord | `runtime/system/observability/repository.py` | LocalMetricsRepository | Analytics, History, Platform Console |
| analytics/history | `runtime/system/observability/analytics.py` | EngineeringAnalytics | Platform Console, CI |

**Evidence Path:** ExecutionOrchestrator → TaskExecutionRecord → record_execution_report() → EngineeringEventStore + RunRecord → Analytics/History

---

## 4. Configuration Inventory

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| **verification.yaml** | `runtime/foundation/verification/verification.yaml` | **ACTIVE_CANONICAL** | Thresholds, profiles, mutation config |
| **profiles.py** | `runtime/foundation/verification/profiles.py` | **ACTIVE_CANONICAL** | Profile definitions for legacy aliases |
| **capability registry** | `runtime/foundation/verification/capability_contract.py` | **ACTIVE_CANONICAL** | Capability contracts with workflow mappings |
| **verification registry** | `runtime/foundation/verification/registry.py` | **ACTIVE_CANONICAL** | Verification requirements, workflows, scripts |
| **migration map** | `runtime/foundation/verification/canonical_control_plane.py` | **ACTIVE_SUPPORTING** | Legacy command → canonical operation mapping |

---

## 5. CLI Authority Inventory

| CLI Command | Facade Method | Planner | Executor | Evidence Path | Outcome Path | Status |
|-------------|---------------|---------|----------|---------------|--------------|--------|
| **check** | ControlPlaneFacade.check() | ControlPlanePlanner | ExecutionOrchestrator | TaskExecutionRecord | FinalDecision | **COMPLETE** |
| **plan** | ControlPlaneFacade.plan() | ControlPlanePlanner | (dry-run) | Plan artifact | Plan JSON | **COMPLETE** |
| **run** | ControlPlaneFacade.run() | (uses provided plan) | ExecutionOrchestrator | TaskExecutionRecord | FinalDecision | **COMPLETE** |
| **diagnose** | ControlPlaneFacade.diagnose() | - | - | FailureReport | Diagnostic | **COMPLETE** |
| **strengthen** | ControlPlaneFacade.strengthen() | TestGenerator | - | StrengtheningReport | - | **COMPLETE** |
| **inspect** | ControlPlaneFacade.inspect() | - | - | Capability/Plan/Evidence data | - | **COMPLETE** |
| **certify** | ControlPlaneFacade.certify() | - | CertificationGate | MeasurementTruth | Certified/NotCertifiable | **COMPLETE** |
| **ci** | ControlPlaneFacade.ci() | VerificationOrchestrator | VerificationOrchestrator | VerificationReport | VerificationSummary | **COMPLETE** |
| **doctor** | ControlPlaneFacade.doctor() | - | EnvCheck | EnvCheckResult | Health | **COMPLETE** |

### Legacy Profile Aliases (Compatibility Routes)

| Command | Chain Status | Notes |
|---------|--------------|-------|
| `verify quick` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify backend` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify frontend` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify api-contracts` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify runtime` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify golden` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify playwright` | LEGACY SHIM | Delegates to `verify.py` legacy cmd_* via migration_map |
| `verify mutation` | CANONICAL | Direct to `runtime.foundation.verification.mutation_runner.execute_mutation` |

---

## 6. CI Workflow Audit

| Workflow | Trigger | Verification Command | Entry Point | Canonical? | Direct Tool Invocation? | continue-on-error? | Exit Code Propagation? |
|----------|---------|---------------------|-------------|------------|------------------------|-------------------|------------------------|
| quality.yml | push/PR | `python -m runtime.verify quick` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| backend-verify.yml | push/PR (backend/**) | `python -m runtime.verify backend` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| verification-runtime.yml | push/PR (runtime/**) | `python -m runtime.verify runtime` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| mutation.yml | schedule/dispatch | `python -m runtime.verify mutation --smoke` then `mutation` | Canonical | YES | NO | NO | YES |
| golden.yml | push/PR | `python -m runtime.verify golden` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| playwright.yml | push/PR | `python -m runtime.verify playwright` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| api-contracts.yml | push/PR | `python -m runtime.verify api-contracts` | Legacy profile alias | YES (via migration_map) | NO | NO | YES |
| verification-reconcile.yml | PR | `python -m runtime.verify reconcile` | Canonical (custom) | YES | NO | NO | YES |
| security-codeql.yml | push/PR | CodeQL analysis | External tool | INTENTIONAL_EXTERNAL_TOOL | YES (CodeQL) | NO | YES |
| dependency-update.yml | schedule | dependabot | External tool | INTENTIONAL_EXTERNAL_TOOL | YES | NO | YES |
| release.yml | tag | release automation | External tool | INTENTIONAL_EXTERNAL_TOOL | YES | NO | YES |

**Key Finding:** All CI workflows delegate to the canonical `python -m runtime.verify` entry point. Legacy profile aliases are routed through the canonical migration map with no semantic loss. Exit codes propagate correctly. Evidence and history are recorded via `runtime.verify status`.

---

## 7. Classification Summary

| Classification | Components | Count |
|----------------|------------|-------|
| **ACTIVE_CANONICAL** | ControlPlanePlanner, ExecutionOrchestrator (C49), VerificationOrchestrator (7B), MutationOrchestrator, ControlPlaneFacade, verification.yaml, profiles.py, capability registry, verification registry, canonical CLI commands (9) | ~15 |
| **ACTIVE_SPECIALIZED** | EvidenceAwarePlanner, VerificationPlanner, CrossLayerImpactPlanner, Executor Pipeline | 4 |
| **COMPATIBILITY** | Legacy profile aliases (8), migration_map, canonical_control_plane.py (as shim) | ~10 |
| **HISTORICAL** | Orchestration/orchestrator.py (decomposed), milestone directories | ~2 |
| **DEAD** | None identified | 0 |
| **AMBIGUOUS** | None identified | 0 |

---

## 8. Authority Relationship Verification

### Expected Planning Hierarchy (from C62 spec):
```
ControlPlanePlanner
    │
    ├── EvidenceAwarePlanner
    │
    ├── VerificationPlanner
    │
    └── CrossLayerImpactPlanner
```

### Actual Implementation (VERIFIED):
- **ControlPlanePlanner** instantiates EvidenceAwarePlanner and VerificationPlanner internally (control_plane.py:148-160)
- **ControlPlanePlanner** consumes CrossLayerImpactPlanner via blast radius in `_determine_escalation_conditions` and E2E impact analysis
- **VerificationOrchestrator** independently instantiates CrossLayerImpactPlanner and VerificationPlanner
- All subordinate planners are **layered responsibilities**, not competing top-level planners ✅

### Expected Execution Authority:
```
ExecutionOrchestrator (C49) — canonical for verify check/run
VerificationOrchestrator (7B) — canonical for legacy profiles/ci
MutationOrchestrator — specialized for mutation
```

### Actual Implementation (VERIFIED):
- **ExecutionOrchestrator** is used by ControlPlaneFacade.check() and ControlPlaneFacade.run() ✅
- **VerificationOrchestrator** is used by ControlPlaneFacade.ci() and legacy profile routes ✅
- **MutationOrchestrator** is called by ExecutionOrchestrator for mutation tasks ✅
- Specialized/historical paths explicitly documented ✅

---

## 9. Phase B Completion Status

✅ Planning authority inventory complete  
✅ Execution authority inventory complete  
✅ Evidence path trace complete  
✅ Configuration inventory complete  
✅ CLI authority inventory complete  
✅ CI workflow audit complete  
✅ Classification summary complete  
✅ Authority relationship verification complete

**Next:** Phase C — Authority Contract Verification