# M9-C62 Phase D — Automatic Authority-Drift Detection

**Execution Record** — Authoritative Audit Phase  
**Started:** 2026-09-18T03:39:42Z  
**Branch:** `m9c9-merge-authorization-resolution`  
**Base Commit:** `2fca4854` (M9-C61: Converge cross-layer contract normalization)

---

## 1. Detection Requirements (from C62 spec)

The detector must inspect actual repository relationships and identify:

| Condition | Expected Detection |
|-----------|-------------------|
| Wrong planner imported by canonical CLI | DETECTED |
| Wrong executor imported by canonical facade | DETECTED |
| Legacy orchestrator unexpectedly used by canonical command | DETECTED |
| Second evidence path introduced | DETECTED |
| Canonical registry bypassed | DETECTED |
| Deprecated command becomes direct execution path | DETECTED |

Detection must use:
- Imports
- Call relationships
- Command dispatch
- Registry metadata
- Known authority declarations

Output must identify:
- Detected component
- Expected authority
- Actual authority
- Classification
- Source evidence
- Severity

---

## 2. Implementation Plan

### 2.1 Detection Architecture

Create `runtime/foundation/verification/authority_drift_detector.py` with:

1. **PlannerDriftDetector** - Verify planner import/use in canonical paths
2. **ExecutorDriftDetector** - Verify executor import/use in canonical paths
3. **EvidencePathDriftDetector** - Verify evidence path integrity
4. **ConfigurationDriftDetector** - Verify config/registry parity
5. **CLIDriftDetector** - Verify CLI command dispatch integrity
6. **CIDriftDetector** - Verify CI workflow parity

### 2.2 Authority Declarations (Source of Truth)

```python
# Canonical authority declarations
CANONICAL_AUTHORITIES = {
    "planner": {
        "top_level": "runtime.foundation.verification.control_plane.ControlPlanePlanner",
        "subordinate": [
            "runtime.foundation.verification.evidence_planner.EvidenceAwarePlanner",
            "runtime.foundation.verification.planner.planner.VerificationPlanner",
            "runtime.foundation.verification.planner.planner.CrossLayerImpactPlanner",
        ],
    },
    "executor": {
        "canonical": "runtime.foundation.verification.execution_orchestrator.ExecutionOrchestrator",
        "program_7b": "runtime.foundation.verification.orchestrator.VerificationOrchestrator",
        "specialized": [
            "runtime.foundation.verification.mutation_execution.orchestrator.MutationOrchestrator",
        ],
        "historical": [
            "runtime.foundation.verification.orchestration.orchestrator.ExecutionOrchestrator",
        ],
    },
    "evidence": {
        "writer": "runtime.verify.record_execution_report",
        "stores": [
            "runtime.system.observability.event_store.EngineeringEventStore",
            "runtime.system.observability.repository.LocalMetricsRepository",
        ],
    },
    "cli": {
        "canonical_commands": [
            "check", "plan", "run", "diagnose", "strengthen", 
            "inspect", "certify", "ci", "doctor"
        ],
        "legacy_aliases": [
            "quick", "backend", "frontend", "api-contracts", 
            "runtime", "golden", "playwright"
        ],
        "mutation": "runtime.foundation.verification.mutation_runner.execute_mutation",
    },
}
```

### 2.3 Detection Logic

#### Planner Drift Detection
- Scan `control_plane_facade.py` for planner imports
- Verify only `ControlPlanePlanner` is instantiated directly
- Verify subordinate planners only instantiated via `ControlPlanePlanner.__init__`

#### Executor Drift Detection
- Scan `control_plane_facade.py` for executor imports
- Verify `ExecutionOrchestrator` used for `check`/`run`
- Verify `VerificationOrchestrator` used for `ci` only
- Flag any direct import of `orchestration.orchestrator`

#### Evidence Path Drift Detection
- Scan for calls to `EngineeringEventStore.append()` outside `record_execution_report`
- Scan for calls to `LocalMetricsRepository.append()` outside `record_execution_report`
- Verify single writer pattern

#### Configuration Drift Detection
- Verify `verification.yaml` keys match code expectations
- Verify capability registry has all capabilities referenced by planners
- Verify verification registry has all workflows referenced by profiles

#### CLI Drift Detection
- Scan `control_plane_facade.py` main() dispatch
- Verify all 9 canonical commands map to facade methods
- Verify legacy aliases route through `migration_map()`

---

## 3. Implementation

Creating the detector module...