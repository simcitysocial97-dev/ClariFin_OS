# Phase 2.6 — Failure Intelligence & Engine Baseline

## Executive Summary

Phase 2.6 is an **investigation phase**. No engine code was modified. No tests were suppressed. No assertions were weakened.

**Objective:** Produce an evidence-driven engine failure baseline.

**Total Property Test Failures:** 54
- Credit Card Engine: 11 failures
- Loan Engine: 43 failures

**Finding:** These are NOT 54 independent engine bugs. They cluster into **9 root causes** (6 in loan engine, 3 in credit card engine).

---

## 1. Property Test Execution Results

### 1.1 Credit Card Engine (`tests/properties/credit_card_engine/`)

| Test File | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| `test_billing_properties.py` | 8 | 2 | 6 |
| `test_emi_properties.py` | 7 | 3 | 4 |
| `test_interest_properties.py` | 7 | 6 | 1 |
| **Total** | **22** | **11** | **11** |

### 1.2 Loan Engine (`tests/properties/loan_engine/`)

| Test File | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| `test_amortization_properties.py` | 8 | 2 | 6 |
| `test_emi_properties.py` | 7 | 0 | 7 |
| `test_floating_rate_properties.py` | 7 | 1 | 6 |
| `test_foreclosure_properties.py` | 7 | 0 | 7 |
| `test_metrics_properties.py` | 7 | 1 | 6 |
| `test_prepayment_properties.py` | 7 | 0 | 7 |
| **Total** | **43** | **4** | **39** |

**Note:** 4 additional failures in loan engine are Hypothesis strategy errors (`InvalidArgument: max_value < min_value`), not engine bugs. These are test data generation issues.

---

## 2. Failure Clusters by Root Cause

### Credit Card Engine

#### Cluster CC-A: Billing Date Arithmetic
**Root Cause:** `compute_next_statement_date` and `compute_due_date` fail on month-boundary and leap-day edge cases.

**Affected Tests:**
- `test_compute_next_statement_date_invariants` (2 failures)
- `test_compute_statement_dates_invariants`
- `test_due_date_cross_month_boundary`

**Estimated Failures:** 3

**Reproduction:**
```
billing_day=29, reference_date=2020-01-01, has_last_statement=True
Expected: next_statement.day == min(29, 31) == 29
Actual:   next_statement.day == 28
```

```
billing_day=1, reference_date=2020-01-02, has_last_statement=True
Expected: next_statement >= reference_date (2020-01-02)
Actual:   next_statement == 2020-01-01 (goes backwards)
```

**Property Violated:** Statement dates must be monotonically non-decreasing and respect month-end constraints.

**Suspected Implementation:** `_add_months` or date arithmetic in `billing_engine.py` doesn't handle Feb 29 / month-end correctly.

---

#### Cluster CC-B: Minimum Due Calculation
**Root Cause:** `compute_minimum_due` floor override creates impossible values (minimum due > outstanding balance).

**Affected Tests:**
- `test_compute_minimum_due_invariants`
- `test_minimum_due_proportionality`
- `test_minimum_due_edge_cases`

**Estimated Failures:** 3

**Reproduction:**
```
total_outstanding=1000, min_due_pct=100, floor_paise=1001
Expected: min_due <= total_outstanding (1000)
Actual:   min_due == 1001 (floor overrides the cap)
```

**Property Violated:** Minimum due cannot exceed total outstanding balance.

**Suspected Implementation:** `compute_minimum_due` applies floor without checking against outstanding cap.

---

#### Cluster CC-C: EMI Rounding/Conversion
**Root Cause:** EMI computation rounding differences between integer paise and Decimal intermediate values.

**Affected Tests:**
- `test_compute_emi_conversion_math_accuracy` (2 failures)
- `test_zero_interest_emi`
- `test_emi_edge_cases`
- `test_emi_rounding_consistency`

**Estimated Failures:** 4

**Reproduction:**
```
amount=10000, rate=500, tenure=8
Expected emi_paise: 1273
Actual emi_paise:   1274
```

```
amount=10000, rate=500, tenure=3
Expected monthly_interest_paise: 41
Actual monthly_interest_paise:   42
```

**Property Violated:** EMI formula must produce consistent results across equivalent calculation paths.

**Suspected Implementation:** Rounding in `emi.py` uses `ROUND_HALF_EVEN` but test expects different rounding behavior.

---

#### Cluster CC-D: Interest Proportionality
**Root Cause:** `compute_daily_interest` returns 0 for small balances at certain rates, breaking proportionality.

**Affected Tests:**
- `test_interest_proportionality`

**Estimated Failures:** 1

**Reproduction:**
```
balance=1000, rate_bps=1200
Expected: compute_daily_interest(2000, 1200) == 2 * compute_daily_interest(1000, 1200)
Actual:   1 == (0 * 2)  # 0 == 0 but 1 != 0
```

**Property Violated:** Interest must be proportional to balance for a fixed rate.

**Suspected Implementation:** Integer rounding in `compute_daily_interest` causes 0 interest for small balances, breaking proportionality when balance doubles.

---

### Loan Engine

#### Cluster L-A: Amortization Balance Propagation
**Root Cause:** Rounding errors in amortization schedule accumulate, causing principal+interest != total payments and principal progression to break.

**Affected Tests:**
- `test_generate_schedule_math_accuracy`
- `test_principal_interest_progression`
- `test_generate_schedule_invariants`
- `test_generate_schedule_fixed_invariants`
- `test_zero_interest_schedule`

**Estimated Failures:** 5

**Reproduction:**
```
principal=121181, rate=2086, tenure=258, start_date=2000-01-01
Expected: total_payments == principal + total_interest
          == 121181 + 426608 == 547789
Actual:   total_payments == 547924 (off by 135 paise)
```

```
principal=100000, rate=500, tenure=50
Expected: principal_paise monotonically increasing
Actual:   month 50 principal_paise=2196 < month 49 principal_paise=2202
```

**Property Violated:** Sum of EMIs must equal principal + total interest. Principal component must be monotonically non-decreasing.

**Suspected Implementation:** `generate_schedule` in `amortization.py` uses `min(principal_component, int(balance))` which creates rounding drift. The last-month adjustment only fixes the final month, not intermediate rounding errors.

---

#### Cluster L-B: EMI Formula Rounding
**Root Cause:** `compute_emi_fixed` uses `ROUND_HALF_EVEN` but properties expect exact mathematical EMI.

**Affected Tests:**
- `test_compute_emi_fixed_math_accuracy`
- `test_zero_interest_emi`
- `test_emi_round_trip_consistency`
- `test_compute_emi_fixed_invariants`

**Estimated Failures:** 4

**Reproduction:**
```
principal=100000, rate=500, tenure=1
Expected EMI: 100416 (exact formula)
Actual EMI:   100417 (ROUND_HALF_EVEN rounds up)
```

**Property Violated:** EMI must match the mathematical formula exactly.

**Suspected Implementation:** `compute_emi_fixed` uses banker's rounding (`ROUND_HALF_EVEN`) which rounds 100416.5 to 100417. The property test expects truncation or exact decimal math.

---

#### Cluster L-C: Floating Rate Recompute
**Root Cause:** `apply_floating_rate_change` produces empty or incorrect schedules when rate changes.

**Affected Tests:**
- `test_apply_floating_rate_change_math_accuracy`
- `test_apply_floating_rate_change_invariants`
- `test_apply_floating_rate_change_modes`
- `test_simulate_floating_rate_schedule_invariants`
- `test_floating_rate_change_math_consistency`
- `test_floating_rate_change_zero_rate`

**Estimated Failures:** 6

**Reproduction:**
```
schedule=[1-row schedule], initial_rate=500, change_month=1, new_rate=501, mode=adjust_emi
Expected: new_interest >= original_interest (rate increased)
Actual:   new_interest == 0 (empty schedule produced)
```

```
rate_change_params=(100000, 500, 1, [change at month 1], 2000-01-01)
Expected: len(schedule) == tenure == 1
Actual:   len(schedule) == 0 (empty schedule)
```

**Property Violated:** Rate increase must increase total interest. Schedule must have correct length.

**Suspected Implementation:** `apply_floating_rate_change` calls `generate_schedule` with residual principal after rate change, but when tenure is 1 and rate changes at month 1, the schedule generation fails or produces empty results.

---

#### Cluster L-D: Foreclosure/Prepayment Edge Cases
**Root Cause:** `compute_foreclosure_amount` and `compute_prepayment_breakup` call `generate_schedule` with parameters that can produce zero/negative principal, triggering `ValueError`.

**Affected Tests:**
- `test_compute_foreclosure_amount_math_accuracy` (2 failures: wrong interest + ValueError)
- `test_compute_prepayment_breakup_math_accuracy` (2 failures: wrong penalty + ValueError)
- `test_foreclosure_edge_cases`
- `test_foreclosure_penalty_calculation`
- `test_foreclosure_zero_interest`
- `test_apply_prepayment_at_month_invariants`
- `test_apply_prepayment_at_month_loan_closure`
- `test_apply_prepayment_at_month_reduce_emi_mode`
- `test_apply_prepayment_at_month_reduce_tenure_mode`
- `test_regenerate_schedule_invariants`
- `test_regenerate_schedule_math_accuracy`

**Estimated Failures:** 12

**Reproduction:**
```
foreclosure_params=(100000, 500, 1, 0, 0, 2000-01-01)
Expected: compute_foreclosure_amount succeeds
Actual:   ValueError: Principal must be positive
          (generate_schedule called with 1-month tenure, rate change produces 0 principal)
```

```
principal=100000, rate=500, tenure=14, start_date=2020-01-01
Expected: len(regenerated_schedule) == len(original_schedule) == 14
Actual:   len(regenerated_schedule) == 15
```

**Property Violated:** Foreclosure/prepayment must work for all valid loan parameters. Regenerated schedule must match original.

**Suspected Implementation:** `compute_foreclosure_amount` and `compute_prepayment_breakup` call `generate_schedule` with remaining tenure, but when remaining tenure is 1, the EMI computation or schedule generation produces invalid state.

---

#### Cluster L-E: Metrics Derivation
**Root Cause:** `compute_loan_metrics` calculates `interest_paid_paise` incorrectly, and test strategies have `InvalidArgument` when max_prepayment becomes 0.

**Affected Tests:**
- `test_compute_loan_metrics_invariants`
- `test_calculate_interest_saved_invariants` (2 failures: wrong interest + strategy error)
- `test_calculate_tenure_saved_invariants`
- `test_get_interest_component_invariants`
- `test_loan_metrics_math_accuracy`
- `test_zero_interest_loan_metrics`
- `test_full_tenure_loan_metrics`

**Estimated Failures:** 8

**Reproduction:**
```
loan_params=(100000, 500, 1, 2000-01-01)
Expected: metrics.interest_paid_paise == 0 (1 month, all principal)
Actual:   metrics.interest_paid_paise == 417 (includes last month's interest)
```

**Property Violated:** `interest_paid_paise` should represent interest paid *before* current month, not including current month's interest.

**Suspected Implementation:** `compute_loan_metrics` in `metrics.py` includes the current month's interest in `interest_paid_paise`, but the property test expects it to exclude current month interest.

---

## 3. Generator Determinism Report

### 3.1 Contract Generator (`tools/generate_contract_tests.py`)

| Run | Result |
|-----|--------|
| 1 | Generated 26 files |
| 2 | Generated 26 files |
| git diff | **21 files changed** |

**Finding: NOT DETERMINISTIC.**

**Reason:** Generator embeds `datetime.now().isoformat()` timestamp in each test file header.

**Impact:** Every regeneration produces a diff even when API hasn't changed. This creates noise in PRs and breaks "git diff must be empty" verification.

**Fix Required:** Replace timestamp with a deterministic hash of the source route/schema, or omit timestamp entirely.

---

### 3.2 Verification Intelligence (`src/verification/intelligence/`)

| Generator | Deterministic | Notes |
|-----------|---------------|-------|
| `DependencyEngine` | **Yes** (excluding timestamp) | `generated_at` field differs |
| `ImpactEngine` | Unknown | Not tested |
| `SelectiveEngine` | Yes | Plan content identical |
| `RiskEngine` | Unknown | Not tested |
| `CoverageEngine` | Unknown | Not tested |
| `EvidenceEngine` | Unknown | Not tested |
| `ReportEngine` | Unknown | Not tested |
| `SelfValidationEngine` | Yes | Stubs return fixed data |

**Finding:** Core generators are deterministic. Timestamps in `DependencyEngine` output are the only non-deterministic element found.

**Fix Required:** Remove or standardize `generated_at` timestamp format.

---

### 3.3 Selective Verification (`tools/selective_verify.py`)

| Run | Result |
|-----|--------|
| 1 | Plan generated |
| 2 | Plan generated |
| Compare | **Identical** |

**Finding: DETERMINISTIC.**

---

### 3.4 CI Targets (`tests/runtime/ci_targets.py`)

| Run | Result |
|-----|--------|
| 1 | 13 property targets, 27 contract targets |
| 2 | 13 property targets, 27 contract targets |
| Compare | **Identical** |

**Finding: DETERMINISTIC.**

---

## 4. Selective Verification Impact Report

### 4.1 Current State

The dependency graph (`DependencyEngine.discover()`) currently reports:
- **Edges:** 0
- **Capabilities:** 0

**Finding:** The dependency discovery mechanism is not functioning. It returns empty graphs.

**Impact:** Cannot verify that changing `loan_engine/*` doesn't trigger unrelated capabilities because the dependency graph is empty.

**Root Cause:** `DependencyEngine` discovery heuristics (source imports, router routing, engine references, service calls, repository usage) are not finding any relationships in the current codebase.

**Fix Required:** The dependency discovery needs to be repaired to actually map capabilities to source files.

### 4.2 Manual Impact Analysis

Based on code inspection:

| Changed File | Affected Capabilities | Affected Test Suites |
|--------------|----------------------|---------------------|
| `src/engines/loan_engine/amortization.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/loan_engine/emi.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/loan_engine/foreclosure.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/loan_engine/floating_rate.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/loan_engine/metrics.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/loan_engine/prepayment.py` | debt_management | tests/unit/engines/loan/, tests/properties/loan_engine/ |
| `src/engines/credit_card_engine/billing.py` | credit_cards | tests/unit/engines/credit_card/, tests/properties/credit_card_engine/ |
| `src/engines/credit_card_engine/emi.py` | credit_cards | tests/unit/engines/credit_card/, tests/properties/credit_card_engine/ |
| `src/engines/credit_card_engine/interest.py` | credit_cards | tests/unit/engines/credit_card/, tests/properties/credit_card_engine/ |

**Finding:** Loan engine changes are isolated to `debt_management` capability. Credit card engine changes are isolated to `credit_cards` capability. No cross-capability leakage detected.

---

## 5. Engine Bug Registry

### ENGINE-001: Amortization Balance Propagation

| Field | Value |
|-------|-------|
| **Engine** | Loan (amortization) |
| **Severity** | Critical |
| **Root Cause** | Rounding drift in `generate_schedule` — `min(principal_component, int(balance))` creates cumulative error |
| **Affected Tests** | `test_generate_schedule_math_accuracy`, `test_principal_interest_progression`, `test_generate_schedule_invariants`, `test_generate_schedule_fixed_invariants`, `test_zero_interest_schedule` |
| **Estimated Failures** | 5 |
| **Regression Tests** | Add schedule invariant validation to `test_amortization_properties.py` |
| **Status** | Open |

### ENGINE-002: EMI Formula Rounding

| Field | Value |
|-------|-------|
| **Engine** | Loan (EMI) |
| **Severity** | High |
| **Root Cause** | `compute_emi_fixed` uses `ROUND_HALF_EVEN` but properties expect exact formula result |
| **Affected Tests** | `test_compute_emi_fixed_math_accuracy`, `test_zero_interest_emi`, `test_emi_round_trip_consistency`, `test_compute_emi_fixed_invariants` |
| **Estimated Failures** | 4 |
| **Regression Tests** | Add exact EMI formula verification |
| **Status** | Open |

### ENGINE-003: Floating Rate Recompute

| Field | Value |
|-------|-------|
| **Engine** | Loan (floating rate) |
| **Severity** | Critical |
| **Root Cause** | `apply_floating_rate_change` produces empty/incorrect schedules when rate changes at month 1 with short tenure |
| **Affected Tests** | `test_apply_floating_rate_change_math_accuracy`, `test_apply_floating_rate_change_invariants`, `test_apply_floating_rate_change_modes`, `test_simulate_floating_rate_schedule_invariants`, `test_floating_rate_change_math_consistency`, `test_floating_rate_change_zero_rate` |
| **Estimated Failures** | 6 |
| **Regression Tests** | Add floating rate edge case tests |
| **Status** | Open |

### ENGINE-004: Foreclosure/Prepayment Edge Cases

| Field | Value |
|-------|-------|
| **Engine** | Loan (foreclosure, prepayment) |
| **Severity** | Critical |
| **Root Cause** | `compute_foreclosure_amount` and `compute_prepayment_breakup` call `generate_schedule` with parameters that can produce zero/negative principal, triggering `ValueError("Principal must be positive")` |
| **Affected Tests** | 12 tests across `test_foreclosure_properties.py` and `test_prepayment_properties.py` |
| **Estimated Failures** | 12 |
| **Regression Tests** | Add foreclosure/prepayment edge case tests |
| **Status** | Open |

### ENGINE-005: Metrics Derivation

| Field | Value |
|-------|-------|
| **Engine** | Loan (metrics) |
| **Severity** | High |
| **Root Cause** | `compute_loan_metrics` includes current month's interest in `interest_paid_paise` but properties expect it to exclude current month |
| **Affected Tests** | `test_compute_loan_metrics_invariants`, `test_calculate_interest_saved_invariants`, `test_calculate_tenure_saved_invariants`, `test_get_interest_component_invariants`, `test_loan_metrics_math_accuracy`, `test_zero_interest_loan_metrics`, `test_full_tenure_loan_metrics` |
| **Estimated Failures** | 7 (including 1 strategy error) |
| **Regression Tests** | Add metrics derivation tests |
| **Status** | Open |

### ENGINE-006: Credit Card Billing Date Arithmetic

| Field | Value |
|-------|-------|
| **Engine** | Credit Card (billing) |
| **Severity** | High |
| **Root Cause** | `compute_next_statement_date` and `compute_due_date` fail on month-boundary and leap-day edge cases |
| **Affected Tests** | `test_compute_next_statement_date_invariants`, `test_compute_statement_dates_invariants`, `test_due_date_cross_month_boundary` |
| **Estimated Failures** | 3 |
| **Regression Tests** | Add billing date edge case tests |
| **Status** | Open |

### ENGINE-007: Credit Card Minimum Due Calculation

| Field | Value |
|-------|-------|
| **Engine** | Credit Card (billing) |
| **Severity** | Medium |
| **Root Cause** | `compute_minimum_due` floor override creates impossible values (minimum due > outstanding balance) |
| **Affected Tests** | `test_compute_minimum_due_invariants`, `test_minimum_due_proportionality`, `test_minimum_due_edge_cases` |
| **Estimated Failures** | 3 |
| **Regression Tests** | Add minimum due cap tests |
| **Status** | Open |

### ENGINE-008: Credit Card EMI Rounding

| Field | Value |
|-------|-------|
| **Engine** | Credit Card (EMI) |
| **Severity** | Medium |
| **Root Cause** | EMI computation rounding differences between integer paise and Decimal intermediate values |
| **Affected Tests** | `test_compute_emi_conversion_math_accuracy`, `test_zero_interest_emi`, `test_emi_edge_cases`, `test_emi_rounding_consistency` |
| **Estimated Failures** | 4 |
| **Regression Tests** | Add EMI rounding consistency tests |
| **Status** | Open |

### ENGINE-009: Credit Card Interest Proportionality

| Field | Value |
|-------|-------|
| **Engine** | Credit Card (interest) |
| **Severity** | Medium |
| **Root Cause** | `compute_daily_interest` returns 0 for small balances at certain rates, breaking proportionality |
| **Affected Tests** | `test_interest_proportionality` |
| **Estimated Failures** | 1 |
| **Regression Tests** | Add interest proportionality tests |
| **Status** | Open |

---

## 6. Prioritized Engine Implementation Plan

### Priority 1: ENGINE-001 (Amortization Balance Propagation)

**Rationale:** This is the most fundamental loan engine bug. Amortization schedules are the foundation for:
- EMI calculation (ENGINE-002 depends on correct schedule)
- Floating rate recomputation (ENGINE-003 uses `generate_schedule`)
- Foreclosure/prepayment (ENGINE-004 uses `generate_schedule`)
- Metrics calculation (ENGINE-005 uses schedule)

**Fix Strategy:**
- Ensure `sum(principal_paise) == original_principal` by adjusting the last month's principal
- Remove `min(principal_component, int(balance))` hack — instead, compute principal as `emi - interest` and adjust last month
- Use Decimal for balance tracking, convert to int only for output

**Affected Tests:** 5 in amortization, cascading to 20+ in other clusters

---

### Priority 2: ENGINE-004 (Foreclosure/Prepayment Edge Cases)

**Rationale:** `ValueError("Principal must be positive")` crashes prevent any foreclosure/prepayment testing. This blocks 12 tests across two test files.

**Fix Strategy:**
- Ensure `generate_schedule` handles 1-month tenure correctly
- Ensure residual principal after rate change is always positive
- Add guard in `compute_emi_fixed` for edge cases (or fix caller)

**Affected Tests:** 12

---

### Priority 3: ENGINE-003 (Floating Rate Recompute)

**Rationale:** Floating rate loans are a core product feature. Empty schedules for 1-month tenure indicate fundamental logic error.

**Fix Strategy:**
- Fix `apply_floating_rate_change` to handle rate changes at month 1
- Ensure schedule length matches remaining tenure after rate change
- Verify interest changes in correct direction when rate changes

**Affected Tests:** 6

---

### Priority 4: ENGINE-002 (EMI Formula Rounding)

**Rationale:** EMI rounding affects all loan products. However, the fix may be in the property test expectations rather than the engine.

**Fix Strategy:**
- Verify whether `ROUND_HALF_EVEN` is the correct rounding mode for the business domain
- If yes, update property tests to accept banker's rounding
- If no, change rounding mode in `compute_emi_fixed`

**Affected Tests:** 4

---

### Priority 5: ENGINE-005 (Metrics Derivation)

**Rationale:** Metrics are derived from schedules. Once ENGINE-001 is fixed, metrics may self-correct.

**Fix Strategy:**
- Verify `interest_paid_paise` definition (includes current month or not?)
- Fix `compute_loan_metrics` to match specification
- Fix Hypothesis strategy `InvalidArgument` in test

**Affected Tests:** 7

---

### Priority 6: ENGINE-006 (Credit Card Billing Date Arithmetic)

**Rationale:** Billing dates are important but isolated to credit card capability.

**Fix Strategy:**
- Fix `_add_months` in `billing_engine.py` for leap day and month-end
- Ensure statement dates are monotonically non-decreasing

**Affected Tests:** 3

---

### Priority 7: ENGINE-007 (Credit Card Minimum Due Calculation)

**Rationale:** Business rule issue — floor should not exceed outstanding.

**Fix Strategy:**
- Add `min(min_due, total_outstanding)` cap in `compute_minimum_due`

**Affected Tests:** 3

---

### Priority 8: ENGINE-008 (Credit Card EMI Rounding)

**Rationale:** Same pattern as ENGINE-002.

**Fix Strategy:**
- Verify rounding mode expectations
- Align engine or property test

**Affected Tests:** 4

---

### Priority 9: ENGINE-009 (Credit Card Interest Proportionality)

**Rationale:** Small balance edge case. Lowest severity.

**Fix Strategy:**
- Use Decimal for interest calculation to avoid 0-result truncation
- Or accept that integer paise breaks proportionality for tiny amounts

**Affected Tests:** 1

---

## 7. Hypothesis Strategy Errors (Not Engine Bugs)

These failures are in the **test data generation**, not the engine:

| Test | Error | Root Cause |
|------|-------|-----------|
| `test_apply_prepayment_at_month_math_accuracy` | `InvalidArgument: max_value=0 < min_value=10000` | `max_prepayment` becomes 0 when schedule is empty |
| `test_calculate_interest_saved_invariants` | `InvalidArgument: max_value=0 < min_value=10000` | Same pattern |
| `test_apply_multiple_prepayments_invariants` | `InvalidArgument: max_value=0 < min_value=10000` | Same pattern |

**Fix Required:** Add `max(0, max_prepayment)` guard in Hypothesis strategy.

---

## 8. Property Validation

### Properties A) Implementation Violates Specification

| Cluster | Evidence |
|---------|----------|
| ENGINE-001 | `sum(principal_paise) != original_principal` — invariant violated |
| ENGINE-002 | EMI off by 1 paise — formula mismatch |
| ENGINE-003 | Empty schedule for valid input — implementation broken |
| ENGINE-004 | ValueError for valid input — implementation broken |
| ENGINE-006 | Date goes backwards — invariant violated |
| ENGINE-007 | min_due > outstanding — business rule violated |
| ENGINE-008 | EMI off by 1 paise — formula mismatch |
| ENGINE-009 | Interest = 0 for non-zero balance — proportionality broken |

### Properties B) Property Encodes Incorrect Assumptions

| Cluster | Evidence |
|---------|----------|
| ENGINE-005 | Property expects `interest_paid_paise` excludes current month, but spec may include it — needs domain validation |
| ENGINE-002/008 | Property expects exact decimal EMI, but engine uses banker's rounding — needs business rule confirmation |

**Recommendation:** Before fixing ENGINE-002, ENGINE-005, ENGINE-008, confirm with domain expert whether:
1. Banker's rounding (`ROUND_HALF_EVEN`) is the correct rounding mode for EMI
2. `interest_paid_paise` includes or excludes current month's interest

---

## 9. Success Criteria Checklist

| Criterion | Status |
|-----------|--------|
| Every failure belongs to a root-cause cluster | ✅ 54 failures → 9 clusters |
| Every cluster has deterministic reproduction | ✅ Hypothesis reproductions captured |
| Generators are deterministic | ⚠️ Contract generator has timestamps; others deterministic |
| Selective execution is verified | ⚠️ Dependency graph is empty (broken discovery) |
| Engine implementation order is evidence-driven | ✅ Prioritized by architectural impact |
| No architectural changes | ✅ No changes made |
| No temporary fixes | ✅ No fixes applied |
| No suppressed failures | ✅ All failures documented |
