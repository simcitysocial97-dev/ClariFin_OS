# M9-C39 Loan Engine Certification Report
**Generated:** 2026-08-20T12:59:09.098925+00:00
**Baseline:** HEAD `a74892ce6a7f83cde61abef09274df89f19aa071` · TREE `e96096f0aaeb52a53cc7727beff6a69ab33d7747`

## Executive Summary
The loan engine's reduce-EMI prepayment calculation had a quantization bug: `compute_emi_fixed` uses ROUND_HALF_EVEN, which can round DOWN when the true EMI's fractional part lies just below 0.5. For extreme loans (high rate ≥33%, long tenure ≥330 months), this creates asymmetric drift between the original and regenerated schedules, causing `new_total > original_total` despite a principal prepayment — violating the financial invariant.

### Root Cause
- **Mechanism:** EMI quantization error ±0.5 paise/month compounds over annuity_factor months (up to ~586k for n=356, r=33.12%), creating a total drift of up to ±293k paise. The original schedule's lucky rounding (EMI rounded UP) produced a small final denouement; the regenerated tail's unlucky rounding (EMI rounded DOWN) produced a large balloon. The net effect: new_total exceeded original_total by up to ~52k paise, far beyond the tolerance of n×10+1000.
- **Failing case:** P=₹455,637.99, r=33.12%, n=356, prepay=₹100 at month 1
- **Original:** EMI=1,257,639 (rounded up from 1,257,638.51), residual=-288,147 (overpaid)
- **New (broken):** EMI=1,257,362 (rounded down from 1,257,362.49), residual=+288,588 (underpaid)
- **New (fixed):** EMI=1,257,363, residual=-297,416 (overpaid), total within tolerance

### Fix Applied
In `apply_prepayment_at_month`, after regenerating the reduce-EMI tail, a bounded loop (max 20 iterations) checks:
1. **No balloon:** `tail[-1].emi_paise ≤ tail[0].emi_paise`
2. **Total invariant:** `new_total ≤ original_total + (remaining_months×10+1000)`
If either fails, EMI is incremented by 1 and the tail is regenerated. Each +1 changes total by approximately `-(annuity_factor - n)` paise (~-300k to -600k), so convergence is typically 1-2 iterations. The fix is scoped to the prepayment caller only; `regenerate_schedule` remains pure for non-prepayment callers.

### Verification Results
| Test Suite | Passed | Failed | Notes |
|---|---|---|---|
| Prepayment properties | 12 | 0 | Including previously-failing reduce_emi_mode |
| Loan engine units | 59 | 0 | |
| C39 regression tests | 5 | 0 | Deterministic cases covering the bug |
| Full backend suite | 1351 | 0 | All tests pass |
| API contracts gate | PASS | — | freshness, types, wire all clean |
| Golden profile | PASS | — | 28 capability integration tests |

### Regression Tests Added
- `test_original_failing_case_principal_45563799_rate_3312`: exact reproduced case
- `test_various_prepayment_months_same_loan`: months 1,50,100,200,300,356
- `test_high_rate_low_principal_long_tenure`: alternative extreme case (r=33.4%, n=330)
- `test_reduce_tenure_unchanged_by_fix`: ensure no regressions in reduce_tenure mode
- `test_interest_always_non_negative_after_prepay`: interest can never increase

### Files Changed
- `backend/src/engines/loan_engine/prepayment.py` (+22/-18 lines)
- `backend/tests/unit/engines/loan/test_c39_regression.py` (new, 5 tests)

---
*M9-C39 Loan Engine Certification — generated 2026-08-20T12:59:09.098925+00:00.*