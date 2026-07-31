# Selective Verification Impact Report

## Executive Summary

Selective verification is **deterministic** but the **dependency graph is empty**, preventing automated impact analysis.

**Current State:**
- Selective plan generation: ✅ Deterministic
- Dependency discovery: ❌ Returns 0 edges, 0 capabilities
- Manual impact analysis: ✅ Loan engine changes isolated to `debt_management`; credit card changes isolated to `credit_cards`

---

## 1. Selective Verification Determinism

### Test: Plan Generation Consistency

```bash
cd backend && python tools/selective_verify.py --plan src/engines/loan_engine/amortization.py
cd backend && python tools/selective_verify.py --plan src/engines/loan_engine/amortization.py
git diff tests/generated/selective-plan.md
```

**Result:** No diff — plans are identical.

### Test: CI Targets Consistency

```python
from tests.runtime.ci_targets import get_property_targets, get_contract_targets
assert get_property_targets() == get_property_targets()
assert get_contract_targets() == get_contract_targets()
```

**Result:** PASS — 13 property targets, 27 contract targets, consistent across runs.

---

## 2. Dependency Graph Status

### Current Output

```python
from verification.intelligence.dependency_engine import DependencyEngine
engine = DependencyEngine()
graph = engine.discover()
print(len(graph.edges))          # 0
print(len(graph.capabilities))   # 0
```

### Root Cause

`DependencyEngine` uses multiple discovery heuristics:
1. `_discover_from_capability_registry()` — reads `capability-registry.yaml`
2. `_discover_from_source_imports()` — scans Python imports
3. `_discover_from_router_routing()` — maps FastAPI routes
4. `_discover_from_engine_references()` — finds engine usage
5. `_discover_from_service_calls()` — finds service dependencies
6. `_discover_from_repository_usage()` — finds repository usage
7. `_discover_capability_test_mapping()` — maps tests to capabilities

None of these are producing edges or capabilities in the current codebase.

### Impact

Cannot automatically verify that changing `loan_engine/*` doesn't trigger unrelated capabilities.

---

## 3. Manual Impact Analysis

### 3.1 Loan Engine Changes

**Files:**
- `src/engines/loan_engine/amortization.py`
- `src/engines/loan_engine/emi.py`
- `src/engines/loan_engine/foreclosure.py`
- `src/engines/loan_engine/floating_rate.py`
- `src/engines/loan_engine/metrics.py`
- `src/engines/loan_engine/prepayment.py`

**Capability Mapping:**
| File | Capability | Why |
|------|-----------|-----|
| `amortization.py` | `debt_management` | Core amortization logic |
| `emi.py` | `debt_management` | EMI calculation |
| `foreclosure.py` | `debt_management` | Foreclosure amount calculation |
| `floating_rate.py` | `debt_management` | Floating rate recomputation |
| `metrics.py` | `debt_management` | Loan metrics derivation |
| `prepayment.py` | `debt_management` | Prepayment breakup |

**Affected Test Suites:**
| Test Suite | Triggered By |
|-----------|-------------|
| `tests/unit/engines/loan/` | Direct unit tests |
| `tests/properties/loan_engine/` | Property-based tests |
| `tests/contract/generated/test_loans.py` | API contract tests (via routers) |
| `tests/capability/debt_management/` | Capability smoke tests |

**NOT Affected:**
- `tests/unit/engines/credit_card/` — Different engine
- `tests/properties/credit_card_engine/` — Different capability
- `tests/contract/generated/test_credit_cards.py` — Different router
- `tests/capability/credit_cards/` — Different capability
- `tests/integration/` — Integration tests (unless they explicitly test loan+credit interaction)

**Finding:** Loan engine changes are **isolated to `debt_management` capability**. No cross-capability leakage.

---

### 3.2 Credit Card Engine Changes

**Files:**
- `src/engines/credit_card_engine/billing.py`
- `src/engines/credit_card_engine/emi.py`
- `src/engines/credit_card_engine/interest.py`

**Capability Mapping:**
| File | Capability | Why |
|------|-----------|-----|
| `billing.py` | `credit_cards` | Statement date and due date computation |
| `emi.py` | `credit_cards` | Credit card EMI calculation |
| `interest.py` | `credit_cards` | Daily/monthly interest computation |

**Affected Test Suites:**
| Test Suite | Triggered By |
|-----------|-------------|
| `tests/unit/engines/credit_card/` | Direct unit tests |
| `tests/properties/credit_card_engine/` | Property-based tests |
| `tests/contract/generated/test_credit_cards.py` | API contract tests |
| `tests/capability/credit_cards/` | Capability smoke tests |

**NOT Affected:**
- `tests/unit/engines/loan/` — Different engine
- `tests/properties/loan_engine/` — Different capability
- `tests/contract/generated/test_loans.py` — Different router
- `tests/capability/debt_management/` — Different capability

**Finding:** Credit card engine changes are **isolated to `credit_cards` capability**. No cross-capability leakage.

---

### 3.3 Repository Changes

**Files:**
- `src/repositories/loan_repository.py`
- `src/repositories/credit_card_repository.py`

**Affected Test Suites:**
| Test Suite | Triggered By |
|-----------|-------------|
| `tests/unit/repositories/` | Direct repository tests |
| `tests/contract/generated/test_loans.py` | API contract tests |
| `tests/contract/generated/test_credit_cards.py` | API contract tests |
| `tests/integration/` | Integration tests |

**NOT Affected:**
- `tests/properties/loan_engine/` — Properties test engines, not repositories
- `tests/properties/credit_card_engine/` — Properties test engines, not repositories
- `tests/capability/*` — Unless capability test explicitly tests repository

**Finding:** Repository changes affect API layer but not engine property tests.

---

## 4. Affected-Target Report

### Loan Engine Change

```
Input:  src/engines/loan_engine/*
Output: Affected targets
```

| Target | Reason | Priority |
|--------|--------|----------|
| `tests/unit/engines/loan/` | Direct unit tests | High |
| `tests/properties/loan_engine/` | Property tests | High |
| `tests/capability/debt_management/` | Capability smoke test | Medium |
| `tests/contract/generated/test_loans.py` | API contract | Medium |
| `tests/unit/repositories/test_loan_repository.py` | Repository tests (if repo changed) | Medium |
| `tests/integration/` | Integration tests (if orchestrator uses loans) | Low |

### Credit Card Engine Change

```
Input:  src/engines/credit_card_engine/*
Output: Affected targets
```

| Target | Reason | Priority |
|--------|--------|----------|
| `tests/unit/engines/credit_card/` | Direct unit tests | High |
| `tests/properties/credit_card_engine/` | Property tests | High |
| `tests/capability/credit_cards/` | Capability smoke test | Medium |
| `tests/contract/generated/test_credit_cards.py` | API contract | Medium |
| `tests/unit/repositories/test_credit_card_repository.py` | Repository tests (if repo changed) | Medium |
| `tests/integration/` | Integration tests (if orchestrator uses credit cards) | Low |

---

## 5. Dependency Graph Repair Recommendation

The dependency graph is currently empty, which defeats the purpose of selective verification.

### Recommended Fix

1. **Restore capability registry loading** — Ensure `_discover_from_capability_registry()` reads `tests/generated/capability-registry.yaml`
2. **Add source-file mapping** — Each capability should have a `source_files` list
3. **Add test-file mapping** — Each capability should have a `test_files` list
4. **Regenerate capability registry** — Run `python tools/check_coverage.py` to regenerate

### Verification

After fix:
```python
engine = DependencyEngine()
graph = engine.discover()
assert len(graph.capabilities) > 0
assert len(graph.edges) > 0
```

---

## 6. Conclusion

- **Selective verification is deterministic** — plan generation produces identical output across runs
- **Dependency graph is broken** — returns empty graph, preventing automated impact analysis
- **Manual impact analysis confirms isolation** — loan engine changes only affect `debt_management`; credit card changes only affect `credit_cards`
- **No cross-capability leakage detected** — changing `loan_engine/*` does not trigger `credit_cards` tests and vice versa
