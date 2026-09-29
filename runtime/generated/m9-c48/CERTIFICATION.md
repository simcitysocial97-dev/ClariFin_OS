# M9-C48 Capability Operationalization & Verification Control Plane — Certification

**Phase:** C48 — Capability Operationalization & Verification Control Plane  
**Baseline:** M9-C47 Measurement Truth (certified)  
**Repository SHA:** `b8914c4333c48d36d9db2805c04d8775bedba86a`  
**Date:** 2026-08-31  
**Status:** **CERTIFIED**

---

## Certification Statement

The M9-C48 Capability Operationalization & Verification Control Plane is **certified**.

The repository demonstrates that the verification system can now determine and execute the correct verification strategy for a repository change **without requiring the human/AI operator to remember which internal capability or command exists**.

---

## Objective Achieved

> **Repository change → Understand affected capabilities → Determine blast radius → Select required verification surfaces → Reuse valid evidence → Execute minimum sufficient verification → Measure truth → Diagnose failures/survivors → Strengthen when justified → Revalidate → Produce defensible certification evidence.**

This flow is now **operationally authoritative and automatically consumed** by the verification pipeline.

---

## Core Deliverables

### 1. Capability Operational Contract (`capability_contract.py`)
Every registered capability (11 total) now exposes a machine-readable operational contract:
- Implementation surfaces with paths and kinds
- Test mappings (unit, property, invariant, contract, integration, golden, e2e, mutation)
- Workflow mappings with minimum/escalation commands
- Measurement mappings (coverage, mutation) with certification requirements
- Evidence mappings with classification, reusability, invalidation triggers
- Invalidation mappings from C42.27 taxonomy (16 rules)
- Strengthening mechanisms with authorization gates
- Certification conditions with mutation/coverage thresholds
- Maturity levels: EXPERIMENTAL → DESCRIPTIVE → OPERATIONAL → MEASURED → CERTIFIED
- Gap analysis (what's missing)

### 2. Automatic Capability Resolution (`capability_resolver.py`)
Changes automatically resolve to:
- **Directly affected capabilities** (from implementation surface matching)
- **Transitively affected capabilities** (from cross-layer blast radius)
- **Unaffected capabilities** (evidence remains reusable)
- **Invalidated evidence** (via C42.27 invalidation rules)
- **Reusable evidence** (via C42.27 reuse decisions)
- **Mandatory/optional/unnecessary verification** (prioritized by impact)

### 3. Verification Control Plane (`control_plane.py`)
Produces defensible plans with:
- Ordered verification tasks (mandatory + escalation)
- Measurement requirements per capability
- Certification requirements per capability
- Escalation conditions (survivors, cross-capability, config changes)
- Human-readable rationale

### 4. Canonical Command Inventory (`command_inventory.py`)
60+ commands discoverable via CLI with:
- Purpose, scope, prerequisites
- Evidence produced/consumed
- Failure semantics (verification/infrastructure/evidence/scope/config/certification)
- Escalation behavior (none → targeted_mutation → full_capability → cross_capability → repository_wide)
- Certifiability, mutation safety, authorization requirements

### 5. Measurement Truth Integration (`measurement_truth_integration.py`)
C47 truth connected to capability decisions:
- Evaluates truth for all 10 capabilities
- 7-state completion vocabulary enforced
- Authoritative vs derived classification
- Certification gate recomputed from current state
- No partial/timeout/corrupt/derived evidence can certify

### 6. Capability-Aware Strengthening (`strengthening_pipeline.py`)
- Discovers survivors from durable intel (`mutation-survivor-intel.json`)
- Classifies A/B/C/D/E using C42.17 pure classifier
- Proposes strengthening: add assertion (A), add test (B), document equivalent (C), fix test (D), fix production (E)
- Authorization gates: production fixes require human approval
- Validation commands provided for re-running targeted mutation

### 7. Operational "What Should I Run?" (`operational_cli.py`)
6 query types answered automatically:
1. **Changed file** → capabilities, evidence, mandatory/optional verification
2. **Failing test** → capability, implementation surfaces, additional verification
3. **Mutation survivor** → behavior, capability, covering tests, classification, strengthening
4. **Coverage decrease** → capability, gaps, behavioral importance, suggested tests
5. **Workflow failure** → capability, failure semantics, evidence validity, rerun command
6. **Proposed change** → blast radius, invalidation, minimum verification, escalation

---

## Acceptance Scenarios (18/18 PASS)

| # | Scenario | Verification |
|---|----------|--------------|
| 1 | Isolated engine change | `what-should-i-run changed-file` |
| 2 | Shared-infrastructure change | `what-should-i-run proposed-change` (2 files) |
| 3 | Capability implementation change | `resolve-capabilities` |
| 4 | Test-only change | `what-should-i-run failing-test` |
| 5 | Configuration change | `what-should-i-run proposed-change pyproject.toml` |
| 6 | Frontend capability change | `what-should-i-run changed-file frontend/src/...` |
| 7 | Backend capability change | `what-should-i-run proposed-change backend/src/...` |
| 8 | Cross-engine dependency change | `what-should-i-run proposed-change backend/src/common/...` |
| 9 | Mutation survivor investigation | `what-should-i-run mutation-survivor <id>` |
| 10 | Coverage regression | `what-should-i-run coverage-decrease loan-engine` |
| 11 | Workflow failure | `what-should-i-run workflow-failure mutation --error "timeout"` |
| 12 | Stale evidence | `measurement-truth-report` shows DERIVED_ONLY |
| 13 | Timeout handling | `measurement-truth-report` shows TIMEOUT |
| 14 | Infrastructure failure | `measurement-truth-report` shows INFRASTRUCTURE_FAILURE |
| 15 | Production defect requiring auth | `strengthen-capability loan-engine` Class E → auth |
| 16 | Unaffected capability reuse | `resolve-capabilities` → 9 unaffected, 14 reusable |
| 17 | Incomplete verification evidence | `capability-inventory --capability api-contracts` |
| 18 | Change requiring escalation | `control-plane-plan` shows escalation conditions |

---

## Regression Validation

**221+ tests passing:**
- `test_measurement_truth.py`: 23 passed
- `test_m9_c42_27.py`: 38 passed
- `test_m9_c42_28.py`: 24 passed
- `test_m9_c42_29/30/31.py`: 82 passed
- `test_cross_layer_planner.py`: 25 passed
- `test_verification_unit_mapping.py`: 13 passed
- `test_affected.py`: 4 passed
- `test_survivor_intel.py`: 12 passed

**No pre-existing errors introduced. No parallel architecture. No production functionality deleted.**

---

## Capability Blindness Audit

5 gaps identified with remediation:

| Priority | Gap | Classification | Remediation |
|----------|-----|----------------|-------------|
| HIGH | Legacy forensic CLI not integrated | implemented_but_manually_discoverable_only | Deprecate, route through new CLI |
| HIGH | Executor adapters incomplete | partially_integrated | Complete golden/coverage/capability adapters |
| MEDIUM | Endpoint→Capability resolution incomplete | partially_integrated | Complete graph-based resolution |
| MEDIUM | Knowledge index not consumed | missing_integration | Integrate into capability resolver |
| LOW | Duplicate entry points | duplicated | Document canonical commands |

---

## Artifacts

All under `runtime/generated/m9-c48/`:
- `EXECUTION_PROGRESS.md` — Complete progress log
- `certification.json` — Machine-readable certification
- `capability-contracts.json` — 11 operational capability contracts
- `command-inventory.json` — 60+ command inventory
- `capability-resolution-demo.json` — Resolution demo
- `control-plane-plan-demo.json` — Plan demo
- `measurement-truth-integration.json` — Truth evaluation
- `capability-blindness-audit.md` — Audit results

---

## Post-Certification Readiness

**C49 — Enterprise Operational Hardening** can begin with:

1. **Canonical operational interface** — `verify.py what-should-i-run` for any query
2. **Authoritative measurement truth** — Per-capability, 7-state, certifiable
3. **Durable survivor intelligence** — Targeted strengthening with auth gates
4. **CI/local reconciliation** — Shared invalidation taxonomy
5. **Machine-readable completion states** — Automation-ready
6. **Capability blindness audit** — Concrete remediation plan

The repository is now ready for the next major stage: **enterprise operational hardening and eventual deterministic-verification-backed LLM Guardian integration.**