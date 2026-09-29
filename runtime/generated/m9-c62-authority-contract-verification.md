# M9-C62 Phase C — Authority Contract Verification

**Execution Record** — Authoritative Audit Phase  
**Started:** 2026-09-18T03:35:00Z  
**Branch:** `m9c9-merge-authorization-resolution`  
**Base Commit:** `2fca4854` (M9-C61: Converge cross-layer contract normalization)

---

## 1. Planning Hierarchy Verification

### Expected Hierarchy (from C62 spec):
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

#### ControlPlanePlanner → EvidenceAwarePlanner
**Location:** `runtime/foundation/verification/control_plane.py:148-158`
```python
def __init__(self, ..., evidence_planner: EvidenceAwarePlanner | None = None, ...):
    self._evidence_planner = evidence_planner or default_planner()
```

**Usage:** `control_plane.py:182` - `evidence_plan = self._evidence_planner.plan(changed_files)`

**Classification:** **ACTIVE_CANONICAL** - Top-level planner composes subordinate planner

#### ControlPlanePlanner → VerificationPlanner
**Location:** `runtime/foundation/verification/control_plane.py:148-160`
```python
def __init__(self, ..., base_planner: VerificationPlanner | None = None, ...):
    self._base_planner = base_planner or VerificationPlanner()
```

**Usage:** VerificationPlanner used internally for capability→workflow mapping

**Classification:** **ACTIVE_CANONICAL** - Top-level planner composes subordinate planner

#### ControlPlanePlanner → CrossLayerImpactPlanner
**Location:** `control_plane.py:217-261`
```python
blast_engine = BlastRadiusEngine()
e2e_impact = blast_engine.compute_e2e_impact(changed_path_objects)
```
CrossLayerImpactPlanner is used via BlastRadiusEngine for E2E impact analysis.

**Classification:** **ACTIVE_CANONICAL** - Top-level planner consumes blast-radius enrichment

#### VerificationOrchestrator → CrossLayerImpactPlanner
**Location:** `runtime/foundation/verification/orchestrator.py:815-832`
```python
def analyze_cross_layer(self) -> Any:
    from runtime.foundation.verification.planner.planner import CrossLayerImpactPlanner
    planner = CrossLayerImpactPlanner(map_path=self._map_path)
    self._cross_layer_report = planner.analyze_cross_layer_impact(self._changed_files)
```

**Classification:** **ACTIVE_CANONICAL** (Program 7B) - Independent top-level consumer

#### VerificationOrchestrator → VerificationPlanner
**Location:** `runtime/foundation/verification/orchestrator.py:755-756`
```python
self._planner = VerificationPlanner()
```

**Usage:** `orchestrator.py:883-884` - `self._plan = self._planner.plan(context)`

**Classification:** **ACTIVE_CANONICAL** (Program 7B) - Independent top-level consumer

---

## 2. Execution Authority Verification

### Expected Authority:
```
ExecutionOrchestrator (C49) — canonical for verify check/run
VerificationOrchestrator (7B) — canonical for legacy profiles/ci
MutationOrchestrator — specialized for mutation
```

### Actual Implementation (VERIFIED):

#### ExecutionOrchestrator (C49) Authority
**Entry Points:**
- `ControlPlaneFacade.check()` → `ExecutionOrchestrator.build_execution_plan()` → `execute()`
- `ControlPlaneFacade.run()` → `ExecutionOrchestrator.build_execution_plan()` → `execute()`

**Location:** `control_plane_facade.py:176, 184, 202-207, 305, 316-321`

**Plan Source:** Consumes C48 ControlPlanePlan exclusively

**Classification:** **ACTIVE_CANONICAL** - Primary execution authority for canonical commands

#### VerificationOrchestrator (Program 7B) Authority
**Entry Points:**
- `ControlPlaneFacade.ci()` → `VerificationOrchestrator.run()`
- Legacy profile aliases → `_run_profile_alias()` → direct subprocess execution

**Location:** `orchestrator.py:1185-1192, control_plane_facade.py:1011-1143`

**Plan Source:** Self-generates plan via VerificationPlanner + CrossLayerImpactPlanner

**Classification:** **ACTIVE_CANONICAL** (Program 7B) - Independent execution authority for CI/legacy profiles

#### MutationOrchestrator Authority
**Entry Points:**
- `ExecutionOrchestrator._execute_measurement_task()` → `MutationOrchestrator.run()`
- `verify mutation` CLI → `runtime.foundation.verification.mutation_runner.execute_mutation()`

**Location:** `execution_orchestrator.py:1334-1335, 1448-1580`

**Classification:** **ACTIVE_SUPPORTING** - Specialized executor for mutation tasks

---

## 3. Evidence Authority Verification

### Expected Chain:
```
ExecutionOrchestrator.execute() → TaskExecutionRecord → record_execution_report() → EngineeringEventStore + RunRecord → Analytics/History
```

### Actual Implementation (VERIFIED):

#### ExecutionOrchestrator Evidence Production
**Location:** `execution_orchestrator.py:1173-1176, 1294-1316`
- Produces `TaskExecutionRecord` for each task
- Produces `ExecutionReport` with all records
- Calls `record_execution_report()` in facade

#### ControlPlaneFacade Evidence Recording
**Location:** `control_plane_facade.py:226-228, 339-341`
```python
from runtime.verify import record_execution_report
record_execution_report("check", report, time.monotonic() - run_start)
```

#### VerificationOrchestrator Evidence Production
**Location:** `orchestrator.py:1002-1079`
- Produces `run-manifest.json` (VEA-2 Phase 2) joining plan → execution
- Aggregates evidence via `EvidenceAggregator`

#### Event Store / History Authority
**Single Writer Verified:**
- `EngineeringEventStore.append()` → `engineering-events.jsonl` (append-only)
- `LocalMetricsRepository.append()` → `engineering-history.json` (RunRecord persisted)
- Both written by `record_execution_report()` in `runtime/verify.py`

**Classification:** **CONVERGENT** - Single canonical evidence path ✅

---

## 4. Configuration Authority Verification

### verification.yaml Authority
**Location:** `runtime/foundation/verification/verification.yaml`
- Mutation thresholds, regression thresholds, profile configurations
- Read by `runtime/foundation/verification/env.py` for thresholds

### Profiles.py Authority
**Location:** `runtime/foundation/verification/profiles.py`
- Profile definitions for legacy aliases (quick, backend, frontend, etc.)
- Consumed by `_run_profile_alias()` in control_plane_facade.py

### Capability Contract Registry Authority
**Location:** `runtime/foundation/verification/capability_contract.py`
- Capability contracts with workflow_mappings
- Consumed by ControlPlanePlanner, ExecutionOrchestrator

### Verification Registry Authority
**Location:** `runtime/foundation/verification/registry.py`
- VerificationRequirement, workflows, scripts, capabilities
- Consumed by VerificationPlanner

### Migration Map Authority
**Location:** `runtime/foundation/verification/canonical_control_plane.py`
- Legacy command → canonical operation mapping
- Consumed by `main()` in control_plane_facade.py

---

## 5. CLI Authority Verification

### Canonical Commands (9) - All VERIFIED Complete:
| Command | Facade Method | Planner | Executor | Evidence | Outcome |
|---------|--------------|---------|----------|----------|---------|
| check | ControlPlaneFacade.check() | ControlPlanePlanner | ExecutionOrchestrator | TaskExecutionRecord | FinalDecision |
| plan | ControlPlaneFacade.plan() | ControlPlanePlanner | (dry-run) | Plan artifact | Plan JSON |
| run | ControlPlaneFacade.run() | (provided plan) | ExecutionOrchestrator | TaskExecutionRecord | FinalDecision |
| diagnose | ControlPlaneFacade.diagnose() | - | - | FailureReport | Diagnostic |
| strengthen | ControlPlaneFacade.strengthen() | TestGenerator | - | StrengtheningReport | - |
| inspect | ControlPlaneFacade.inspect() | - | - | Capability/Plan/Evidence | - |
| certify | ControlPlaneFacade.certify() | - | CertificationGate | MeasurementTruth | Certified/NotCertifiable |
| ci | ControlPlaneFacade.ci() | VerificationOrchestrator | VerificationOrchestrator | VerificationReport | VerificationSummary |
| doctor | ControlPlaneFacade.doctor() | - | EnvCheck | EnvCheckResult | Health |

### Legacy Profile Aliases (8) - All Routed Through Migration Map:
| Alias | Migration Target | Execution Path |
|-------|------------------|----------------|
| quick | CHECK (profile) | `_run_profile_alias("quick")` |
| backend | CHECK (profile) | `_run_profile_alias("backend")` |
| frontend | CHECK (profile) | `_run_profile_alias("frontend")` |
| api-contracts | CHECK (profile: contracts) | `_run_profile_alias("contracts")` |
| runtime | CHECK (profile) | `_run_profile_alias("runtime")` |
| golden | CHECK (profile) | `_run_profile_alias("golden")` |
| playwright | CHECK (profile) | `_run_profile_alias("playwright")` |
| mutation | Direct | `mutation_runner.execute_mutation()` |

---

## 6. Authority Contract Verification Summary

| Authority Chain | Expected | Actual | Status |
|-----------------|----------|--------|--------|
| ControlPlanePlanner → EvidenceAwarePlanner | Composed | Composed (injected or default) | ✅ VERIFIED |
| ControlPlanePlanner → VerificationPlanner | Composed | Composed (injected or default) | ✅ VERIFIED |
| ControlPlanePlanner → CrossLayerImpactPlanner | Consumed | Consumed via BlastRadiusEngine | ✅ VERIFIED |
| VerificationOrchestrator → CrossLayerImpactPlanner | Composed | Instantiated internally | ✅ VERIFIED |
| VerificationOrchestrator → VerificationPlanner | Composed | Instantiated internally | ✅ VERIFIED |
| ExecutionOrchestrator (C49) | Canonical for check/run | Used by facade.check/run | ✅ VERIFIED |
| VerificationOrchestrator (7B) | Canonical for ci/profiles | Used by facade.ci/profiles | ✅ VERIFIED |
| MutationOrchestrator | Specialized mutation | Used by ExecutionOrchestrator | ✅ VERIFIED |
| Evidence Path | Single canonical | record_execution_report() single writer | ✅ VERIFIED |
| Config Authority | verification.yaml, profiles.py, registries | All consumed by canonical components | ✅ VERIFIED |
| CLI Canonical (9) | Complete chains | All 9 commands have complete chains | ✅ VERIFIED |
| Legacy Aliases (8) | Compatibility routes | All routed via migration_map | ✅ VERIFIED |

---

## 7. Mechanical Discoverability Assessment

The objective requires making authority relationships **mechanically discoverable**. Current state:

✅ **Planner hierarchy** - Documented in code (instantiation in `__init__`)
✅ **Execution authority** - Documented in facade method dispatch
✅ **Evidence path** - Single writer pattern in `record_execution_report()`
✅ **CLI commands** - Enumerated in `CanonicalOperation` enum
✅ **Legacy aliases** - Enumerated in `migration_map()` and `PROFILE_ALIASES` set
⚠️ **Cross-layer planner dual-consumer** - Both ControlPlanePlanner AND VerificationOrchestrator independently instantiate CrossLayerImpactPlanner (documented but not mechanically enforced)
⚠️ **Orchestrator dual-authority** - Two canonical orchestrators for different entry points (documented in C59)

---

## 8. Phase C Completion Status

✅ Planning hierarchy verified mechanically  
✅ Execution authority verified mechanically  
✅ Evidence authority verified mechanically  
✅ Configuration authority verified mechanically  
✅ CLI authority verified mechanically  
✅ Legacy alias routing verified mechanically  
⚠️ Mechanical discoverability partially complete (dual-consumer patterns documented but not enforced)

**Next:** Phase D — Automatic Authority-Drift Detection