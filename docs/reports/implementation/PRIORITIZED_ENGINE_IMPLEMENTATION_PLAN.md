# Prioritized Engine Implementation Plan

## Objective

Fix engine failures in order that minimizes cascading failures.

**Principle:** Fix the most fundamental components first. Higher-level engines depend on lower-level ones.

**Constraint:** Do not modify tests. Do not suppress failures. Fix authoritative sources only.

---

## Dependency Map

```
amortization.py (ENGINE-001)
    ├── emi.py (ENGINE-002)
    ├── floating_rate.py (ENGINE-003)
    ├── foreclosure.py (ENGINE-004)
    ├── prepayment.py (ENGINE-004)
    └── metrics.py (ENGINE-005)

billing.py (ENGINE-006)
    ├── emi.py (ENGINE-008)
    └── interest.py (ENGINE-009)

emi.py (ENGINE-007) — credit card minimum due (independent)
```

---

## Implementation Order

### Phase 1: Core Loan Engine (Weeks 1-3)

#### Week 1: ENGINE-001 — Amortization Balance Propagation

**Files to modify:**
- `src/engines/loan_engine/amortization.py`

**Why first:** Every other loan engine component uses `generate_schedule`. If the schedule is wrong, everything downstream is wrong.

**Fix approach:**
1. Ensure `sum(principal_paise) == original_principal` by adjusting the last month's principal
2. Remove `min(principal_component, int(balance))` hack
3. Use Decimal for balance tracking, convert to int only for output

**Tests that will unblock:**
- `test_generate_schedule_math_accuracy`
- `test_principal_interest_progression`
- `test_generate_schedule_invariants`
- `test_generate_schedule_fixed_invariants`
- `test_zero_interest_schedule`

**Cascading benefits:** Fixes foundation for ENGINE-002, ENGINE-003, ENGINE-004, ENGINE-005.

---

#### Week 2: ENGINE-004 — Foreclosure/Prepayment Edge Cases

**Files to modify:**
- `src/engines/loan_engine/foreclosure.py`
- `src/engines/loan_engine/prepayment.py`
- `src/engines/loan_engine/amortization.py` (if needed for 1-month tenure)

**Why second:** Foreclosure and prepayment are critical financial operations. The `ValueError("Principal must be positive")` crash blocks all testing.

**Fix approach:**
1. Ensure `generate_schedule` handles 1-month tenure correctly
2. Ensure residual principal after rate change is always positive
3. Add guard in `compute_emi_fixed` for edge cases (or fix caller)

**Tests that will unblock:**
- 12 tests across `test_foreclosure_properties.py` and `test_prepayment_properties.py`

**Cascading benefits:** Fixes ENGINE-003 (floating rate uses similar pattern).

---

#### Week 3: ENGINE-003 — Floating Rate Recompute

**Files to modify:**
- `src/engines/loan_engine/floating_rate.py`

**Why third:** Floating rate is important but less critical than foreclosure. By this point, ENGINE-001 and ENGINE-004 fixes should stabilize the schedule generation.

**Fix approach:**
1. Fix `apply_floating_rate_change` to handle rate changes at month 1
2. Ensure schedule length matches remaining tenure after rate change
3. Verify interest changes in correct direction when rate changes

**Tests that will unblock:**
- 6 tests in `test_floating_rate_properties.py`

---

### Phase 2: Derived Loan Metrics (Weeks 4-5)

#### Week 4: ENGINE-002 — EMI Formula Rounding

**Files to modify:**
- `src/engines/loan_engine/emi.py`

**Why fourth:** EMI rounding is a refinement. The core issue is whether to use `ROUND_HALF_EVEN` or truncation. This requires domain expert confirmation.

**Fix approach:**
1. Confirm with domain expert: Is banker's rounding correct for EMI?
2. If yes: Update property tests to accept banker's rounding
3. If no: Change rounding mode in `compute_emi_fixed`

**Tests that will unblock:**
- 4 tests in loan EMI properties
- 4 tests in credit card EMI properties (ENGINE-008)

**Risk:** May require updating multiple property tests.

---

#### Week 5: ENGINE-005 — Metrics Derivation

**Files to modify:**
- `src/engines/loan_engine/metrics.py`

**Why fifth:** Metrics are derived from schedules. With ENGINE-001 fixed, metrics should be more stable.

**Fix approach:**
1. Confirm with domain expert: Does `interest_paid_paise` include current month's interest?
2. Fix `compute_loan_metrics` to match specification
3. Fix Hypothesis strategy `InvalidArgument` in test

**Tests that will unblock:**
- 7 tests in `test_metrics_properties.py`

---

### Phase 3: Credit Card Engine (Weeks 6-7)

#### Week 6: ENGINE-006 — Credit Card Billing Date Arithmetic

**Files to modify:**
- `src/engines/credit_card_engine/billing.py`

**Fix approach:**
1. Fix `_add_months` for leap day and month-end
2. Ensure statement dates are monotonically non-decreasing

**Tests that will unblock:**
- 3 tests in `test_billing_properties.py`

---

#### Week 7: ENGINE-007 + ENGINE-008 + ENGINE-009

**Files to modify:**
- `src/engines/credit_card_engine/billing.py` (ENGINE-007)
- `src/engines/credit_card_engine/emi.py` (ENGINE-008)
- `src/engines/credit_card_engine/interest.py` (ENGINE-009)

**Fix approach:**
1. ENGINE-007: Add `min(min_due, total_outstanding)` cap
2. ENGINE-008: Align rounding mode with ENGINE-002 decision
3. ENGINE-009: Use Decimal for interest calculation or accept integer truncation

**Tests that will unblock:**
- 3 + 4 + 1 = 8 tests

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|-----------|
| Phase 1 (Weeks 1-3) | High — core loan engine changes | Fix amortization invariants first; add regression tests |
| Phase 2 (Weeks 4-5) | Medium — rounding behavior change | Confirm with domain expert before changing rounding |
| Phase 3 (Weeks 6-7) | Low — isolated credit card changes | Credit card engine is independent |

---

## Verification Strategy

After each phase:

```bash
# Run affected property tests
cd backend && python -m pytest tests/properties/loan_engine/ -q --tb=short --timeout=60
cd backend && python -m pytest tests/properties/credit_card_engine/ -q --tb=short --timeout=60

# Run affected unit tests
cd backend && python -m pytest tests/unit/engines/loan/ -q --tb=short --timeout=60
cd backend && python -m pytest tests/unit/engines/credit_card/ -q --tb=short --timeout=60

# Run contract tests
cd backend && python -m pytest tests/contract/generated/test_loans.py tests/contract/generated/test_credit_cards.py -q --tb=short --timeout=60
```

---

## Exit Criteria

Phase 3 complete when:
1. All `tests/properties/loan_engine/` tests pass
2. All `tests/properties/credit_card_engine/` tests pass
3. All `tests/unit/engines/loan/` tests pass
4. All `tests/unit/engines/credit_card/` tests pass
5. No regressions in `tests/contract/generated/` for loan/credit card routers

---

## Out of Scope

This plan does NOT cover:
- Architecture changes
- New capabilities
- Frontend changes
- Database schema changes
- Performance optimization

Focus is exclusively on engine correctness.
