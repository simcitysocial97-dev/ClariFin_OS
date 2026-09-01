# M9-C48 — Capability Blindness Audit

**Generated:** 2026-08-31  
**Phase:** M9-C48 — Capability Operationalization & Verification Control Plane

---

## Audit Purpose

Perform a repository-wide audit specifically for the failure mode previously observed:

> A feature exists in the verification/runtime architecture, but the executing AI/model ignores it and falls back to conventional debugging/testing because the capability is not operationally discoverable.

---

## Classification Framework

Each gap is classified as:
- **implemented_and_automatically_consumed** — Fully operational, no gap
- **implemented_but_manually_discoverable_only** — Exists but requires manual knowledge
- **partially_integrated** — Some integration, incomplete
- **unreachable** — Cannot be reached through current control plane
- **duplicated** — Multiple implementations for same purpose
- **configuration_dependent** — Only works with specific config
- **missing_integration** — Clear integration point missing
- **intentionally_observational** — Not meant for automatic consumption
- **deferred_enhancement** — Known gap, planned for later

---

## Audit Results

### 1. Capability Registry (`verification.yaml` + `registry.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| 11 registered capabilities | **implemented_and_automatically_consumed** | Available via `get_registry().get_all_capabilities()` |
| Capability → workflow mappings | **implemented_and_automatically_consumed** | Used by planner |
| Capability → script mappings | **implemented_and_automatically_consumed** | Used by planner |
| Capability → module mappings | **implemented_and_automatically_consumed** | Used by resolver |
| Capability → requirements | **implemented_and_automatically_consumed** | Used by planner |
| **NEW: Operational capability contracts** | **implemented_and_automatically_consumed** | `CapabilityContractRegistry` with full operational contract |

**Gap:** None — the registry is now the authoritative source

---

### 2. Cross-Layer Impact Planner (`planner.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| `CrossLayerImpactPlanner` | **implemented_and_automatically_consumed** | Used by `verify.py diagnose`, `affected`, `intelligence` |
| Blast radius computation | **implemented_and_automatically_consumed** | Consumes architecture provider chains |
| Engine/Service/Router detection | **implemented_and_automatically_consumed** | Automatic from file paths |
| Capability detection from endpoints | **partially_integrated** | Graph-based resolution has TODO comment |
| DTO/Mapper/ViewModel detection | **partially_integrated** | Only via fallback to intelligence platform |

**Gap:** Endpoint→Capability resolution is not fully implemented (TODO in code). The graph-based capability resolution in `_enrich_from_intelligence` works but the direct endpoint→capability mapping in `_find_chain` for frontend capabilities needs completion.

---

### 3. Verification Planner (`planner.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| `VerificationPlanner` | **implemented_and_automatically_consumed** | Produces `VerificationPlan` |
| Path-based scope resolution | **implemented_and_automatically_consumed** | Uses file path heuristics |
| Capability-based resolution | **partially_integrated** | Uses registry but limited to path matching |
| Evidence-aware planning | **implemented_and_automatically_consumed** | `EvidenceAwarePlanner` in `evidence_planner.py` |
| Tier planning (local/pr/deep) | **implemented_and_automatically_consumed** | `verify.py plan` command |

**Gap:** The planner uses path-based heuristics for capability resolution rather than the capability graph. The new `CapabilityResolver` (M9-C48) addresses this by using the operational contract registry.

---

### 4. Evidence Reuse & Invalidation (`evidence_reuse.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| Invalidation rules (16 rules) | **implemented_and_automatically_consumed** | Used by `EvidenceAwarePlanner` |
| Population snapshots | **implemented_and_automatically_consumed** | C42.24-B, C42.25, C42.26 |
| Component measurements | **implemented_and_automatically_consumed** | Per-component mutation evidence |
| Derived aggregates | **implemented_and_automatically_consumed** | Mathematical reconciliation |
| Reuse decisions | **implemented_and_automatically_consumed** | `decide_reuse()` function |

**Gap:** None — fully operational

---

### 5. Mutation Runner (`mutation_runner.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| Authoritative full campaign | **implemented_and_automatically_consumed** | `verify.py mutation` |
| Smoke test | **implemented_and_automatically_consumed** | `verify.py mutation --smoke` |
| Targeted mutation | **implemented_and_automatically_consumed** | `verify.py mutation --target <engine>` |
| Source restoration safety | **implemented_and_automatically_consumed** | Signal handlers + atexit |
| Cache provenance validation | **implemented_and_automatically_consumed** | SHA + config hash + mutmut version |
| **NEW: Measurement Truth emission** | **implemented_and_automatically_consumed** | Emits `MeasurementTruthRecord` on every run |

**Gap:** None — mutation runner is the canonical mutation execution engine

---

### 6. Survivor Intelligence (`survivor_intel.py` + `survivor_catalog.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| Durable survivor catalog | **implemented_and_automatically_consumed** | `verify.py mutation` produces `mutation-survivors.json` |
| Durable survivor intel | **implemented_and_automatically_consumed** | `verify.py mutation` produces `mutation-survivor-intel.json` |
| `verify.py mutation-intel` | **implemented_and_automatically_consumed** | Inspects durable intel record |
| Classification (A/B/C/D/E) | **implemented_and_automatically_consumed** | Uses C42.17 pure classifier |
| Covering test enrichment | **implemented_and_automatically_consumed** | Uses `mutmut tests-for-mutant` |

**Gap:** The `mutation-intel` CLI is manually discoverable — it's not linked from the capability contract or control plane. The new `what-should-i-run mutation-survivor` command addresses this.

---

### 7. Measurement Truth (`measurement_truth.py` + `coverage_measurement.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| `MeasurementTruthRecord` | **implemented_and_automatically_consumed** | Single contract for coverage + mutation |
| 7-state completion vocabulary | **implemented_and_automatically_consumed** | AUTHORITATIVE_COMPLETE, PARTIAL, TIMEOUT, etc. |
| Authoritative vs Derived | **implemented_and_automatically_consumed** | Machine-readable, immutable |
| `verify.py measurement-truth` | **implemented_and_automatically_consumed** | Inspects any truth record |
| `verify.py measurement coverage` | **implemented_and_automatically_consumed** | Produces coverage truth record |
| Certification gate | **implemented_and_automatically_consumed** | `certification_gate()` function |

**Gap:** None — fully certified in M9-C47

---

### 8. Control Plane (M9-C48 NEW)

| Feature | Status | Notes |
|---------|--------|-------|
| `CapabilityContractRegistry` | **implemented_and_automatically_consumed** | Extends registry with operational fields |
| `CapabilityResolver` | **implemented_and_automatically_consumed** | Resolves changes → capabilities |
| `ControlPlanePlanner` | **implemented_and_automatically_consumed** | Produces defensible verification plans |
| `CommandInventoryBuilder` | **implemented_and_automatically_consumed** | Canonical command inventory |
| `OperationalQueryEngine` | **implemented_and_automatically_consumed** | Answers 6 operational query types |
| **NEW CLI Commands** | **implemented_and_automatically_consumed** | `what-should-i-run`, `capability-inventory`, `control-plane-plan`, `resolve-capabilities`, `strengthen-capability`, `strengthen-survivor`, `measurement-truth-report` |

**Gap:** None — all M9-C48 components operational

---

### 9. Forensic/Strengthening Pipeline (`forensic_cli.py` + `strengthening_pipeline.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| `verify.py forensic-diagnose` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| `verify.py strengthen-analyze` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| `verify.py strengthen-discover` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| `verify.py strengthen-propose` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| `verify.py strengthen-validate` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| `verify.py strengthen-report` | **implemented_but_manually_discoverable_only** | Not linked from control plane |
| **NEW: `strengthen-capability`** | **implemented_and_automatically_consumed** | Capability-aware, uses durable intel |

**Gap:** The legacy forensic CLI commands are not integrated into the new capability-aware control plane. The new `strengthen-capability` command wraps them but the old commands remain as separate entry points. This is a capability blindness issue — an operator might not know `forensic-diagnose` exists.

---

### 10. Executor Pipeline (`executor_pipeline.py`)

| Feature | Status | Notes |
|---------|--------|-------|
| Executable plan contract | **partially_integrated** | M28.2-10, produces `ExecutionEvidence` |
| Task adapters | **partially_integrated** | Some kinds marked `not_executable_yet` |
| Targeted mutation executor | **partially_integrated** | Only for selected components |
| Evidence capture | **partially_integrated** | Records fingerprints, artifacts |
| Reconciliation | **partially_integrated** | M28.6-10, labelled aggregates |

**Gap:** Several task kinds (`golden`, `coverage`, `capability`) are marked `not_executable_yet`. The executor is the bridge between planner and execution but not all verification kinds are fully executable through it yet.

---

### 11. Knowledge System (`knowledge/`)

| Feature | Status | Notes |
|---------|--------|-------|
| `verify.py knowledge` | **implemented_and_automatically_consumed** | Indexes endpoints, capabilities, workspaces, rules, components |
| `verify.py knowledge endpoint/capability/...` | **implemented_and_automatically_consumed** | Queryable |
| Architecture provider | **implemented_and_automatically_consumed** | `runtime/foundation/architecture/` |

**Gap:** The knowledge index is manually invoked — not automatically consumed by the control plane for capability resolution. The new `CapabilityResolver` uses the registry directly instead.

---

### 12. API Contract Verification (`api_contracts/`)

| Feature | Status | Notes |
|---------|--------|-------|
| `verify.py api-contracts` | **implemented_and_automatically_consumed** | STRUCTURAL, GENERATED, CONSUMER, WIRE validation |
| `verify.py contract-governance` | **implemented_and_automatically_consumed** | M9-C30 certification |
| Contract drift detection | **implemented_and_automatically_consumed** | Detects drift between OpenAPI and implementation |

**Gap:** None — fully operational

---

### 13. CI/Workflow Verification

| Feature | Status | Notes |
|---------|--------|-------|
| GitHub Actions reusable setup | **implemented_and_automatically_consumed** | `.github/actions/` composite actions |
| `verify.py reconcile` | **implemented_and_automatically_consumed** | VEA-5 M5 CI gate |
| `verify.py certify-v4/v5` | **implemented_and_automatically_consumed** | Program 14 certification |

**Gap:** None — CI integration is solid

---

## Summary of Capability Blindness Gaps

| Priority | Gap | Classification | Remediation |
|----------|-----|----------------|-------------|
| **HIGH** | Legacy forensic CLI commands not integrated into control plane | **implemented_but_manually_discoverable_only** | Deprecate legacy commands, route through `what-should-i-run` / `strengthen-capability` |
| **HIGH** | Executor pipeline task kinds not fully executable (`golden`, `coverage`, `capability`) | **partially_integrated** | Complete adapter implementations |
| **MEDIUM** | Endpoint→Capability resolution incomplete in CrossLayerImpactPlanner | **partially_integrated** | Complete graph-based capability resolution |
| **MEDIUM** | Knowledge index not automatically consumed by control plane | **missing_integration** | Integrate knowledge queries into capability resolver |
| **LOW** | Duplicate entry points for similar functionality (e.g., `affected` vs `what-should-i-run changed-file`) | **duplicated** | Document canonical commands, deprecate aliases |

---

## Remediation Actions (Post-C48)

1. **Deprecate legacy forensic CLI** — Add deprecation warnings to `forensic-diagnose`, `strengthen-*` commands, direct users to `what-should-i-run` and `strengthen-capability`

2. **Complete executor adapters** — Implement `golden`, `coverage`, `capability` task kinds in executor pipeline

3. **Complete endpoint→capability resolution** — Finish the graph-based capability resolution in `CrossLayerImpactPlanner._find_chain`

4. **Integrate knowledge index** — Use architecture provider for capability resolution in `CapabilityResolver`

5. **Document canonical commands** — Add `verify.py what-should-i-run --help` as the primary entry point for operational queries