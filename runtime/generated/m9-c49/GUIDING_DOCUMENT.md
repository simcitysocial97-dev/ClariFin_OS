# M9-C49 — Control Plane Consolidation, Canonical Runtime & Enterprise Verification Convergence

**Repository SHA:** 35a31f50a0352e407b0936f50a7d7fe80206c16a  
**Branch:** m9c9-merge-authorization-resolution  
**Created:** 2026-09-04  
**Mission:** Transform the M9-C48 framework into a genuinely canonical enterprise verification control plane.

---

## 1. Authoritative Inputs

Primary evidence:
- `runtime/generated/m9-c47/` — Forensic audit, 18 gaps identified
- `runtime/generated/m9-c48/` — Remediation blueprint, 19 milestones, 123 acceptance tests
- `runtime/generated/m9-c48/capability-blindness-audit.md` — Post-C48 operational integration gaps

---

## 2. C49 Guiding Principles

1. **One canonical control plane** — The operator/AI expresses intent; the framework determines capabilities and obligations.
2. **Small public CLI surface** — ≤9 top-level commands. Internal complexity is acceptable; operator-facing complexity is not.
3. **Verification obligations, not commands** — The planner produces obligations; the task compiler converts them to executable tasks.
4. **Fail closed** — Every required task either executes or produces an explicit blocking state. No silent omissions.
5. **One semantic authority** — No duplicate authorities for capability, mutation, evidence, or certification.
6. **Evidence over claims** — COMPLETE requires objective evidence with sha256 artifacts.

---

## 3. Canonical Architecture

```
Operator / AI Agent
        ↓
   verify <canonical-op> [args]
        ↓
┌───────────────────────────────────────┐
│      CONTROL PLANE FACADE             │
│  (control_plane_facade.py)            │
│                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │Change    │  │Capability│  │Oblig.│ │
│  │Detector  │→ │Resolver  │→ │Engine│ │
│  └──────────┘  └──────────┘  └──────┘ │
│       ↓              ↓         ↓      │
│  ┌───────────────────────────────────┐│
│  │         Planner                   ││
│  │  (ControlPlanePlanner)            ││
│  └───────────────────────────────────┘│
│       ↓                               │
│  ┌───────────────────────────────────┐│
│  │      Task Compiler                ││
│  │  (executor_pipeline)              ││
│  └───────────────────────────────────┘│
│       ↓                               │
│  ┌───────────────────────────────────┐│
│  │         Executor                  ││
│  │  (ExecutionOrchestrator)          ││
│  └───────────────────────────────────┘│
│       ↓                               │
│  ┌───────────────────────────────────┐│
│  │     Evidence Collector            ││
│  └───────────────────────────────────┘│
│       ↓                               │
│  ┌───────────────────────────────────┐│
│  │       Verdict Engine              ││
│  └───────────────────────────────────┘│
└───────────────────────────────────────┘
        ↓
   Evidence + Verdict
```

---

## 4. Canonical CLI Surface (9 Commands)

| Command | Purpose |
|---------|---------|
| `verify check` | Primary verification entrypoint |
| `verify plan` | Plan-only mode (no execution) |
| `verify run` | Execute an explicit plan |
| `verify diagnose` | Failure/survivor diagnostic |
| `verify strengthen` | Test-strengthening control plane |
| `verify inspect` | Read-only inspection queries |
| `verify certify` | Certification (evidence-gated) |
| `verify ci` | CI orchestration/reconciliation |
| `verify doctor` | Framework health/integrity |

**Inspect sub-queries:** capabilities, evidence, plan, mutation, workflows, health

---

## 5. Verification Obligation Model

```
Change → Capability → Requirement → Verification Obligation → Task → Evidence → Disposition
```

**Disposition Vocabulary (Closed):**
- `CLOSED` — Required evidence exists and is valid
- `EXECUTED` — Task ran, evidence captured
- `OPEN` — Task not yet run; no evidence
- `BLOCKED` — Task cannot run (scope, config, infra)
- `INVALIDATED` — Prior evidence invalidated; needs re-execution
- `REUSED` — Valid prior evidence; obligation closed without execution
- `NOT_APPLICABLE` — Obligation does not apply
- `FAILED` — Task ran; required evidence not produced

---

## 6. Executor Task Matrix

| Kind | Adapter | Executable |
|------|---------|------------|
| mutation | `adapt_mutation_task` | ✓ |
| unit | `adapt_unit_task` | ✓ |
| property | `_not_executable_adapter` | ✗ (blocking) |
| invariant | `_not_executable_adapter` | ✗ (blocking) |
| contract | `_not_executable_adapter` | ✗ (blocking) |
| coverage | `_not_executable_adapter` | ✗ (blocking) |
| golden | `_not_executable_adapter` | ✗ (blocking) |
| capability | `_not_executable_adapter` | ✗ (blocking) |

**Fail-closed guarantee:** No task can be represented as required work while disappearing at execution time.

---

## 7. Authority Layering

### Capability Authority
- **Canonical:** `VerificationRegistry` (loads `verification.yaml`)
- **Derived:** `CapabilityContractRegistry` (enriches canonical with operational fields)
- **Runtime guard:** `capability_authority.assert_no_competing_authority()`

### Mutation Authority
- **Canonical entrypoint:** `runtime.foundation.verification.mutation_runner.run_mutation_cli`
- **Canonical runner:** `runtime.foundation.verification.mutation_runner.execute_mutation`
- **Canonical result:** `runtime.foundation.verification.mutation_contract.MutationResult`
- **Dormant:** `MutationOrchestrator` (declared non-canonical, future migration target)

### Knowledge Authority
- **Knowledge:** Projection of `runtime.foundation.architecture.provider`
- **Not authoritative:** Knowledge index does not independently define capabilities
- **Control plane:** Consumes capability graph directly

---

## 8. CLI Migration Summary

| Classification | Count | Behavior |
|---------------|-------|----------|
| CANONICAL | 9 | Direct dispatch |
| CANONICAL_ALIAS | 9 | Profile names → check |
| COMPATIBILITY | 6 | Retained, no deprecation |
| DEPRECATED | 55 | Emit warning, route to canonical |
| UNREACHABLE | 0 | — |

**Before:** ~97 dispatchable tokens  
**After:** 9 canonical operations + legacy routing

---

## 9. Success Criteria Met

- [x] One canonical control plane exists
- [x] Operator-facing surface reduced to 9 commands
- [x] All legacy commands route through canonical path
- [x] Verification obligation model implemented
- [x] Executor has explicit adapters for all task kinds
- [x] Capability authority convergence achieved
- [x] Mutation authority convergence achieved
- [x] CLI governance acceptance tests pass (23/23)
- [x] C48 tests remain passing (123/123)

---

## 10. Maturity Assessment

| Level | Status |
|-------|--------|
| ARCHITECTURALLY_CONVERGED | ✓ DEMONSTRATED |
| OPERATIONALLY_VALIDATED | Pending longitudinal evidence |
| SUSTAINED_IN_OPERATION | Pending |
| CERTIFIABLE | Pending |
| SELF_VERIFYING | Pending |

**Note:** A one-time successful implementation does not prove sustained self-verification. M9-C49 establishes the architecture; operational validation requires longitudinal evidence collected in future phases.

---

## 11. Artifacts Produced

- `runtime/foundation/verification/canonical_control_plane.py` — Canonical CLI surface definition
- `runtime/foundation/verification/obligation.py` — Verification obligation model
- `runtime/foundation/verification/control_plane_facade.py` — Canonical control plane facade
- `runtime/verify.py` — Thin compatibility shim (delegates to facade)
- `runtime/generated/m9-c49/GUIDING_DOCUMENT.md` — This document
- `runtime/generated/m9-c49/EXECUTION_PROGRESS.md` — Execution ledger
- `runtime/generated/m9-c49/execution-state.json` — Machine-verifiable state
- `runtime/generated/m9-c49/FINAL_CONVERGENCE_REPORT.md` — Final convergence report
- `runtime/tests/test_m9_c49_canonical_cli.py` — CLI governance acceptance tests

---

## 12. Known Limitations & Future Work

1. **Frontend arithmetic remediation** — 112 findings detected by C48, not remediated in C49 (requires frontend code changes outside verification framework scope)
2. **CI workflow migration** — 11 workflows still use legacy commands; migration deferred to future iteration
3. **Executor adapter completeness** — 6 task kinds have blocking adapters but no executable implementation; will be addressed as planner emits those task types
4. **Longitudinal validation** — Operational maturity requires sustained operation evidence beyond this implementation phase

---

## 13. Conclusion

M9-C49 successfully transformed the M9-C48 framework into a genuinely canonical enterprise verification control plane. The operator-facing CLI surface was reduced from ~97 tokens to **9 canonical operations**. All legacy commands now route through the canonical control plane facade with explicit deprecation warnings, eliminating duplicate semantic authority.

The framework is **ARCHITECTURALLY_CONVERGED**. Operational validation, sustained operation, certification, and self-verification will be demonstrated in subsequent phases.