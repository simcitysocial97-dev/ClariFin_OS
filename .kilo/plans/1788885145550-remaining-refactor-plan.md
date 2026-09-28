# Implementation Plan — ClariFin_OS Verification Refactor (Refined)

**Date:** 2026-09-09  
**Previous session:** executor_pipeline.py fully decomposed (2,280 → 432 lines, 12 modules in `execution/`)  
**Status:** Ready for Phase 0.3 + Phase 1 execution  

---

## Current State

| File | Lines | Status |
|------|-------|--------|
| `executor_pipeline.py` | 432 | ✅ Decomposed into `execution/` package |
| `execution_orchestrator.py` | 2,108 | ❌ Not started |
| `workflow_convergence.py` | 2,662 | Deferred (CI-only, high test surface) |
| `orchestrator.py` (existing) | 1,199 | Unrelated legacy module — DO NOT TOUCH |

**Test baseline:** 151 passed, 1 skipped across executor pipeline suite.

---

## Step 1: Decompose `execution_orchestrator.py` → `orchestration/` package

### Target structure

```
runtime/foundation/verification/orchestration/
├── __init__.py          # Lazy re-export proxy (all public API preserved)
├── models.py            # All enums + dataclasses + fingerprint helpers
└── orchestrator.py      # ExecutionOrchestrator class + convenience functions
```

### Line boundaries (verified from code inspection)

**`models.py`** ← lines 1–527 of original:
- Imports + REPO_ROOT + GENERATED_ROOT (L1-60)
- Enums: `CompletionState` (L67), `NON_PASS_STATES`, `PASSING_STATES` (L84), `FailureStage` (L102), `FinalDecision` (L119), `TaskOrigin` (L131)
- Fingerprint helpers: `_git()`, `_hash_file()`, `_hash_tree()`, `_hash_toolchain()` (L145-199)
- `RepositoryFingerprint` dataclass (L202-261)
- Capability mapping: `CAPABILITY_TO_MUTATION_TARGET` dict (L269-275)
- Dataclass models: `ExecutionTaskSpec` (L283-342), `ExecutionPlan` (L344-403), `TaskExecutionRecord` (L423-456), `ExecutionReport` (L458-493)
- Helpers: `_capability_components()` (L501), `_measurement_kind_for_task()` (L511)

**`orchestrator.py`** ← lines 528-2108 of original:
- `ExecutionOrchestrator` class (L529-2015)
- `_profile_from_command()` (L2017)
- Convenience: `build_plan()`, `format_plan()`, `format_report()` (L2030-2108)

### Migration steps

1. Create `runtime/foundation/verification/orchestration/` directory with `__init__.py` skeleton (lazy `__getattr__` pattern, same as `execution/__init__.py`)
2. Write `models.py` — copy L1-527 verbatim, update any relative imports
3. Write `orchestrator.py` — copy L528-2108 verbatim, add `from .models import *` at top
4. Update `execution_orchestrator.py` to thin re-export wrapper:
   ```python
   """M9-C49 — DEPRECATED proxy. Import from orchestration/ instead."""
   from runtime.foundation.verification.orchestration import *  # noqa: F401,F403
   ```
5. Run validation (below)

### External consumers to verify

| Consumer | What they import | Expected after refactor |
|----------|-----------------|------------------------|
| `control_plane_facade.py:67` | `ExecutionOrchestrator` | Still works via proxy |
| `blast_radius_cli.py:206` | `ExecutionOrchestrator`, `format_plan` | Still works via proxy |
| `test_m9_c49.py:48,282` | `ExecutionOrchestrator` | Still works via proxy |
| `test_m9_c50.py:26` | `ExecutionOrchestrator` | Still works via proxy |
| `test_m9_c51.py:245,419` | `ExecutionOrchestrator` | Still works via proxy |
| `test_m9c57_verification_self_contract.py:362,450,855` | `ExecutionOrchestrator`, `ExecutionPlan`, `ExecutionReport`, `RepositoryFingerprint` | Still works via proxy |

### Validation

```bash
.venv/bin/python -m pytest runtime/tests/test_m9_c49.py -v --timeout=120
.venv/bin/python -m pytest runtime/tests/test_m9_c50.py -v --timeout=120
.venv/bin/python -m pytest runtime/tests/test_m9_c51.py -v --timeout=120
.venv/bin/python -m pytest runtime/tests/test_m9c57_verification_self_contract.py -v --timeout=120
.venv/bin/python -m runtime.verify runtime
```

### Notes

- `test_m9c57_verification_self_contract.py` imports `_collect_changed_files` from `runtime.foundation.verification.orchestrator` (the **existing** 1,199-line module, NOT the new package). This is unrelated and must not be touched.
- The new package is `orchestration/` (with an 'n'), distinct from the existing `orchestrator.py`.
- The lazy re-export in `__init__.py` prevents circular import issues during partial initialization.

---

## Step 2: Create Financial Semantic Layer (`semantics/` package)

### 2a: Core assertion infrastructure

Create `runtime/foundation/verification/semantics/`:
```
semantics/
├── __init__.py
├── assertions.py    # FinancialInvariant, FinancialInvariantViolation, FINANCIAL_INVARIANTS, FinancialAssertion
└── parser.py        # SemanticFailure, SemanticFailureParser
```

**`assertions.py`** — ~150 lines:
- `FinancialInvariant` dataclass (id, domain, description, consequence, remediation_pattern?)
- `FinancialInvariantViolation(AssertionError)` — formats: invariant_id, expected, actual, context, remediation
- `FINANCIAL_INVARIANTS` registry (10 entries mapped to actual engine domains)
- `FinancialAssertion` class with static methods per invariant

**Invariants to define (mapped to actual code locations):**
1. `emi_must_exceed_interest` → `backend/src/engines/loan_engine/emi.py`
2. `closure_requires_zero_balance` → `backend/src/engines/loan_engine/lifecycle.py`
3. `total_payment_covers_principal` → `backend/src/engines/loan_engine/prepayment.py`
4. `reconciliation_match_within_tolerance` → `backend/src/engines/reconciliation_engine/matching.py`
5. `balance_equals_sum_of_transactions` → `backend/src/engines/balance_engine/balance.py`
6. `prepayment_reduces_principal_or_tenure` → `backend/src/engines/loan_engine/prepayment.py`
7. `floating_rate_bounded` → `backend/src/engines/loan_engine/floating_rate.py`
8. `cashflow_category_valid` → `backend/src/engines/cashflow_engine/`
9. `forecast_horizon_positive` → `backend/src/engines/forecast_engine/`
10. `net_worth_equals_assets_minus_liabilities` → `backend/src/engines/net_worth/`

**`parser.py`** — regex extraction from FinancialInvariantViolation traceback strings.

### 2b: Migrate 5 critical tests to use FinancialAssertion

Select tests where bare `assert` currently checks financial properties:
1. `backend/tests/unit/engines/loan/test_prepayment.py` — closure balance check
2. `backend/tests/unit/engines/loan/test_emi.py` — EMI > interest check
3. `backend/tests/unit/engines/balance_engine/test_balance.py` — balance = sum of transactions
4. `backend/tests/unit/engines/reconciliation_engine/test_matching.py` — tolerance check
5. `backend/tests/properties/loan_engine/test_emi_properties.py` — property-based invariant

After migration, a failing test produces:
```
Financial Invariant Violated: emi_must_exceed_interest
Expected: emi > 1000
Actual: 500
Context: {'emi': 500, 'interest': 1000, 'principal': 100000, 'tenure': 12}
Remediation: Increase tenure or reduce principal to lower monthly interest
```

### 2c: Diagnostic formatter

Create `runtime/foundation/verification/diagnostics/`:
```
diagnostics/
├── __init__.py
└── formatter.py     # DiagnosticFormatter.format(report)
```

Integrates with `failure_report.py` — extend `FailureReport` dataclass with optional `semantic_failure: SemanticFailure | None` field, then `DiagnosticFormatter.format()` produces enriched output when semantic failures are present.

---

## Step 3: Financial Concept Graph

### 3a: Concept registry

Create `runtime/foundation/verification/semantics/concepts.py`:
- `FinancialConcept` dataclass (id, domain, description, depends_on, affects, invariants, implemented_in)
- `FINANCIAL_CONCEPTS` dict — 15 concepts mapped to actual file paths in `backend/src/engines/`

### 3b: Blast radius analyzer

Create `runtime/foundation/verification/semantics/blast_radius.py`:
- `FinancialBlastRadius.compute_affected_concepts(changed_files)` — direct hit + transitive downstream closure
- `FinancialBlastRadius.compute_at_risk_invariants(affected_concepts)` — union of all invariant ids
- `FinancialBlastRadius.detect_cross_domain_impacts(affected_concepts)` — True if >1 domain

Integration: extend `runtime/foundation/verification/blast_radius.py`'s `BlastRadius` class with `compute_financial_impact()` method.

### 3c: Plan enrichment

Extend `runtime/foundation/verification/control_plane.py` to log semantic impact when building plans (print to stderr/console, non-blocking).

---

## Out of Scope (Deferred)

| Item | Reason | When to revisit |
|------|--------|-----------------|
| `workflow_convergence.py` decomposition | 2,662 lines, 1,178-line test file, CI-only concern | After Phase 1-2 validated end-to-end |
| Phase 3 (survivor analysis) | Lower ROI, pattern-matching complexity | After semantic layer proven useful |
| Phase 4 (AI integration) | Manual workflow only, no runtime dependency | Optional stretch goal |

---

## Risk Matrix

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Circular imports during orchestration split | Blocker | Lazy `__getattr__` in `__init__.py` (proven in executor_pipeline step) |
| Pre-existing test failure masked as regression | False positive | Run full suite before AND after each step; compare baselines |
| `orchestrator.py` vs `orchestration/` confusion | Developer error | Clear naming distinction; docstrings in both modules |
| Financial assertion migration breaks passing tests | Regression | Migrate one test at a time; each migration is a standalone commit |
| Concept graph file paths become stale | Graceful degradation | Missing paths → concept skipped, no crash |

---

## Execution Order

1. **Step 1** — Decompose `execution_orchestrator.py` → `orchestration/`
   - Validates decomposition pattern a second time
   - Low risk (cohesive class, well-scoped tests)
   - Gate: all 5 test suites pass

2. **Step 2a** — Create `semantics/assertions.py`
   - Pure data, no integration yet
   - Gate: module imports cleanly

3. **Step 2b** — Migrate 5 critical tests
   - One test at a time, verify each passes (with new error format on failure)
   - Gate: migrated tests produce semantic error messages on intentional failure

4. **Step 2c** — Diagnostic formatter
   - Gate: formatted output includes invariant info when present

5. **Step 3a** — Concept registry
   - Gate: `FINANCIAL_CONCEPTS` has 15 entries with real file paths

6. **Step 3b** — Blast radius analyzer
   - Gate: `compute_affected_concepts(["backend/src/engines/loan_engine/emi.py"])` returns expected concepts

7. **Step 3c** — Plan enrichment
   - Gate: `python -m runtime.verify backend` prints semantic impact section

---

## End-to-End Success Criterion

After all steps, changing `loan_engine/emi.py` and running verification produces:

```
❌ FAILURE: backend-unit

🔍 FINANCIAL INVARIANT VIOLATED
  Invariant: emi_must_exceed_interest
  Domain: loan_engine
  Description: EMI must exceed monthly interest to reduce principal
  Consequence: Creates negative amortization
  Expected: emi > 1000
  Actual: 500
  Context: {'emi': 500, 'interest': 1000, 'principal': 100000}
  💡 Remediation: Increase tenure or reduce principal to lower monthly interest

📍 FINANCIAL SEMANTIC IMPACT
  Affected Concepts: emi_calculation, loan_closure, prepayment_logic
  At-Risk Invariants: emi_must_exceed_interest, total_payment_covers_principal, closure_requires_zero_balance
  ⚠️ Cross-domain: affects reconciliation.expected_payment
```
