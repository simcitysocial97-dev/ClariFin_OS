# C42 Phase 2 — Survivor Forensic Mapping

**Generated:** 2026-08-22T09:45:28+05:30
**Repository SHA:** 34d22cb763ec05da24f02a420905047afdc64b7f
**Baseline Mutation Run:** 16,427 mutants (4,315 survived, 7,439 no tests)

---

## Summary

| Priority | Engines | Survivors | No Tests | Total Risk |
|----------|---------|-----------|----------|------------|
| **P0** (Financial Critical) | reconciliation_engine, credit_card_engine, loan_engine, account_engine, balance_engine, ledger_audit_engine | 1,199 | 339 | **1,538** |
| **P1** (Business Rules) | behaviour_engine, financial_events, financial_intelligence | 2,834 | 5,876 | 8,710 |
| **P2** (Utility) | recommendation_engine, transaction_intelligence | 282 | 1,030 | 1,312 |

---

## P0 Engine Survivor Mapping

### 1. reconciliation_engine (97 survived, 54 no tests)

| Function | Survivors | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|-----------|----------------|----------------|-------------------|-----------|----------|
| `_parse_date_iso` | 8 | arithmetic, conditional, constant | `test_date_difference_days` (unit), property test | Invalid date format handling, deterministic idempotent parsing | Property + Unit | `tests/properties/reconciliation/test_engine_properties.py` |
| `_date_difference_days` | 9 | arithmetic, conditional | `test_date_difference_days` (unit), property test | None handling, absolute difference, boundary conditions | Property + Unit | `tests/properties/reconciliation/test_engine_properties.py` |
| `_calculate_confidence` | 31 | arithmetic, conditional, constant | `test_calculate_confidence` (unit), property test | Date diff >1 → 0.4 only, desc similarity >0.7 adds 0.2, cap at 1.0, 4 decimals | Property (boundary) | `tests/properties/reconciliation/test_engine_properties.py` |
| `_simple_description_similarity` | 18 | conditional, constant | Property test bounds | Both must have keywords for 1.0, empty=0.0, case-insensitive, 7 keywords | Property + Unit | `tests/properties/reconciliation/test_engine_properties.py` |
| `_check_match` | 24 | conditional, arithmetic | 5 unit tests | Same account rejection, exact amount, date window ≤3, opposite sign, deterministic key | Property + Integration | `tests/properties/reconciliation/test_engine_properties.py` |
| `_generate_explanation` | 37 | constant, conditional | **None directly** | Exact/window format, rupees not paise, account IDs | Unit | `tests/unit/engines/reconciliation/test_reconciliation.py` |
| `find_potential_matches` | 25 | conditional, arithmetic | 3 integration tests | Duplicate prevention via deterministic_key, ordering, empty DB, no matching amount | Integration | `tests/unit/engines/reconciliation/test_reconciliation.py` |

**Domain:** Financial reconciliation, cross-account matching, ledger integrity

---

### 2. credit_card_engine (314 survived, 0 no tests)

| Function | Survivors | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|-----------|----------------|----------------|-------------------|-----------|----------|
| `billing.compute_due_date` | 7 | arithmetic, conditional | Property tests | Due date = statement date + grace period, month-end/leap year handling | Property | `tests/properties/credit_card_engine/test_billing_properties.py` |
| `billing.compute_next_statement_date` | 24 | arithmetic, conditional | Property tests | Statement date + 1 month, month-end handling, consistent with `_add_months` | Property | `tests/properties/credit_card_engine/test_billing_properties.py` |
| `metrics.compute_financial_metrics` | 64 | arithmetic, conditional | Property tests | Revolving balance, minimum due (5%), interest accrual, utilization ratio | Property + Unit | `tests/properties/credit_card_engine/test_billing_properties.py`, `tests/unit/engines/credit_card/test_credit_card_engine.py` |
| `foreclosure.compute_card_foreclosure` | 55 | arithmetic, conditional | Property tests | Outstanding + interest + fees, no foreclosure if zero balance, interest to foreclosure date | Property + Unit | `tests/properties/credit_card_engine/test_billing_properties.py`, `tests/unit/engines/credit_card/test_credit_card_engine.py` |
| `emi.compute_emi` | 12 | arithmetic | Property tests | Formula: P×r×(1+r)^n/((1+r)^n-1), ceiling to paise, zero interest edge case | Property | `tests/properties/credit_card_engine/test_emi_properties.py` |
| `interest.compute_interest` | 12 | arithmetic | Property tests | Daily = balance × daily_rate, monthly compounding, transaction-level allocation | Property | `tests/properties/credit_card_engine/test_interest_properties.py` |
| `outstanding.compute_outstanding` | 8 | arithmetic, conditional | Property tests | Previous + charges - payments + interest, non-negative | Property | `tests/properties/credit_card_engine/test_billing_properties.py` |
| `utilization.compute_utilization` | 8 | arithmetic | Property tests | Outstanding/credit_limit, capped at 1.0, zero limit handling | Property | `tests/properties/credit_card_engine/test_billing_properties.py` |

**Domain:** Credit card billing, EMI, interest, foreclosure, utilization

---

### 3. loan_engine (625 survived, 4 no tests)

| Function | Survivors | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|-----------|----------------|----------------|-------------------|-----------|----------|
| `amortization._add_months` | 0 | arithmetic, conditional | **7 unit tests** (leap year, month-end) | Covered by existing tests | Unit (covered) | `tests/unit/engines/loan/test_amortization.py` |
| `amortization._required_emi` | 0 | arithmetic | Indirect via generate_schedule | Ceiling rounding, zero interest, single month | Property | `tests/properties/loan_engine/test_amortization_properties.py` |
| `amortization.generate_schedule` | 180 | arithmetic, conditional, constant | 15 unit + property tests | **Ill-conditioned detection** (annuity_factor/2 > principal/100), monthly re-anchoring, last month settlement, ROUND_HALF_EVEN, principal bounds, cumulative interest monotonic, sequential months, payment dates | Property + Integration | `tests/properties/loan_engine/test_amortization_properties.py`, `tests/unit/engines/loan/test_amortization.py` |
| `amortization.find_schedule_row` | 1 | conditional | **None** | Valid month → row, invalid → None | Unit | `tests/unit/engines/loan/test_amortization.py` |
| `amortization.total_payment_paise` | 3 | arithmetic | **None** | Sum of EMI payments, empty→0 | Unit | `tests/unit/engines/loan/test_amortization.py` |
| `amortization.total_principal_paise` | 3 | arithmetic | `test_principal_sum_equals_original` | Sum principal = original, empty→0 | Unit (partial) | `tests/unit/engines/loan/test_amortization.py` |
| `amortization.validate_schedule_invariants` | 10 | conditional, arithmetic | 2 unit tests | Principal mismatch detection, negative balance, descriptive ValueError | Unit | `tests/unit/engines/loan/test_amortization.py` |
| `amortization.validate_schedule` | 40 | conditional, arithmetic | **None** | Balance ≥0, principal=original, final balance=0, EMI consistency, cumulative interest monotonic, sequential months, tenure length, debug_mode raises | Property + Unit | `tests/properties/loan_engine/test_amortization_properties.py`, `tests/unit/engines/loan/test_amortization.py` |
| `prepayment.compute_remaining_months` | 6 | arithmetic, conditional | Property tests | Original - elapsed, partial prepayments, non-negative | Property | `tests/properties/loan_engine/test_prepayment_properties.py` |
| `prepayment.apply_multiple_prepayments` | 29 | arithmetic, conditional | Property tests | Reduces principal, interest recalculated, same-month aggregation, ≤outstanding | Property + Integration | `tests/properties/loan_engine/test_prepayment_properties.py`, `tests/unit/engines/loan/test_loan_engine.py` |
| `floating_rate.simulate_floating_rate_schedule` | 55 | arithmetic, conditional | Property tests | Rate changes at specified months, EMI recalculated, reflects from change month, multiple changes | Property + Integration | `tests/properties/loan_engine/test_floating_rate_properties.py`, `tests/unit/engines/loan/test_loan_engine.py` |

**Domain:** Loan amortization, prepayment, floating rate, schedule validation

---

### 4. account_engine (163 survived, 0 no tests)

| Function | Survivors | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|-----------|----------------|----------------|-------------------|-----------|----------|
| `dormant.x_compute_days_since_activity` | 7 | arithmetic, conditional | `test_metrics.py` | Days since last txn, None for no txns, date parsing consistency | Property + Unit | `tests/unit/engines/account/test_account_engine.py` |
| `dormant.x_is_account_dormant` | 7 | conditional | `test_metrics.py` | Dormant if days > 180, not dormant if recent, no txns = dormant | Property + Unit | `tests/unit/engines/account/test_account_engine.py` |
| `cashflow.x_compute_net_cash_flow` | 1 | arithmetic | `test_metrics.py` | Net = total_credit - total_debit, per-period | Property | `tests/unit/engines/account/test_account_engine.py` |
| `cashflow.x_compute_cash_flow_rate` | 16 | arithmetic, conditional | `test_metrics.py` | Rate = net_cash_flow / avg_balance, zero balance handling, annualized | Property | `tests/unit/engines/account/test_account_engine.py` |
| `cashflow.x_compute_income_expense_ratio` | 17 | arithmetic, conditional | `test_metrics.py` | Ratio = income/expense, zero expense handling, categorization | Property | `tests/unit/engines/account/test_account_engine.py` |
| `balance.x_compute_balance_growth_percentage` | 19 | arithmetic, conditional | `test_metrics.py` | Growth% = (end-start)/start × 100, zero start handling, negative for decrease | Property | `tests/unit/engines/account/test_account_engine.py` |
| `lifecycle.x_compute_account_status` | 20 | conditional | `test_metrics.py` | active/dormant/closed, active=recent+positive, dormant=no recent, closed=explicit | Property + Unit | `tests/unit/engines/account/test_account_engine.py` |
| `lifecycle.x_is_account_closed` | 3 | conditional | `test_metrics.py` | True for closed, False for active/dormant | Unit | `tests/unit/engines/account/test_account_engine.py` |
| `history.x_compute_balance_trend` | 21 | arithmetic, conditional | `test_metrics.py` | increasing/decreasing/stable, velocity over window, min window | Property | `tests/unit/engines/account/test_account_engine.py` |
| `history.x_compute_balance_velocity` | 18 | arithmetic | `test_metrics.py` | Velocity = balance_change/time, per-month, zero time handling | Property | `tests/unit/engines/account/test_account_engine.py` |
| `metrics.x_compute_account_metrics` | 34 | arithmetic, conditional | `test_metrics.py` | Aggregates all metrics, consistent with individual functions | Integration | `tests/unit/engines/account/test_account_engine.py` |

**Domain:** Account lifecycle, cash flow metrics, balance trends, dormancy detection

---

### 5. balance_engine (0 survived, **285 no tests**) — **ZERO TEST COVERAGE**

| Function | No Tests | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|----------|----------------|----------------|-------------------|-----------|----------|
| `_parse_date_to_ymd` | 38 | conditional, constant | **None** | 5 Indian formats, month names, ISO, empty for unparseable, strips whitespace | Property + Unit | **NEW: `tests/unit/engines/balance_engine.py`** |
| `_parse_date_for_sort` | 3 | conditional | **None** | YMD for valid, '0000-00-00' for invalid, used for sorting | Unit | **NEW: `tests/unit/engines/balance_engine.py`** |
| `compute_running_balance` | 59 | arithmetic, conditional | **None** | Running = starting + Σ(credit-debit), ordered by date_iso ASC, id ASC, account-scoped, all fields, fallback parsing | Integration + Property | **NEW: `tests/unit/engines/balance_engine.py`** |
| `compute_account_balance` | 41 | arithmetic, conditional | **None** | Balance = starting + total_credit - total_debit, formatted display, SQL SUM | Integration + Unit | **NEW: `tests/unit/engines/balance_engine.py`** |
| `validate_statement_balance` | 57 | arithmetic, conditional | **None** | Computed = Σ(credit-debit), match/mismatch, difference paise+display, txn count | Integration + Unit | **NEW: `tests/unit/engines/balance_engine.py`** |
| `get_accounts_list` | 42 | arithmetic, conditional | **None** | All accounts with counts/balances, balance = credit-debit, ordered by bank | Integration | **NEW: `tests/unit/engines/balance_engine.py`** |
| `_format_paise` | 41 | arithmetic, conditional, constant | **None** | Indian formatting (lakhs/crores), negative prefix, 2-digit paise, zero | Property + Unit | **NEW: `tests/unit/engines/balance_engine.py`** |

**Domain:** Balance computation, statement validation, ledger formatting
**⚠️ CRITICAL:** This P0 engine has **ZERO test coverage** — all 285 mutants are "no tests"

---

### 6. ledger_audit_engine (0 survived, **190 no tests**) — **ZERO TEST COVERAGE**

| Function | No Tests | Mutation Types | Existing Tests | Missing Invariants | Test Type | Location |
|----------|----------|----------------|----------------|-------------------|-----------|----------|
| `validate_ledger_integrity` | 95 | conditional, constant | **None** | account_id NOT NULL, debit≥0, credit≥0, no dual entry, hash NOT NULL, hash uniqueness | Integration | **NEW: `tests/unit/engines/ledger_audit_engine.py`** |
| `verify_hash_signatures` | 95 | arithmetic, conditional | **None** | SHA256(account_id\|date_iso\|description\|debit\|credit), case-insensitive, detects tampering, only non-empty hashes | Integration + Property | **NEW: `tests/unit/engines/ledger_audit_engine.py`** |
| `run_full_audit` | 0 | conditional | **None** | Combines integrity + hash, overall PASS only if both PASS | Integration | **NEW: `tests/unit/engines/ledger_audit_engine.py`** |

**Domain:** Ledger integrity, hash verification, tamper detection
**⚠️ CRITICAL:** This P0 engine has **ZERO test coverage** — all 190 mutants are "no tests"

---

## Critical Test Scope Gap

### Current Mutation Test Selection (from `backend/pyproject.toml`)
```toml
pytest_add_cli_args_test_selection = ["tests/unit/", "tests/properties/"]
```

### Missing from Mutation Execution
| Test Suite | Purpose | Why Missing Matters |
|------------|---------|---------------------|
| `tests/invariants/` | Mathematical invariants, determinism | Would kill survivors in `_calculate_confidence`, `generate_schedule`, `validate_schedule` |
| `tests/contract/` | API contract tests | Would kill survivors in public API functions |
| `tests/integration/` | Cross-component integration | Would kill survivors in `find_potential_matches`, `compute_running_balance`, `validate_ledger_integrity` |

**Impact:** Many "survived" mutants (especially in reconciliation_engine, loan_engine, credit_card_engine) are in code paths exercised by invariant/contract/integration tests — but those tests don't run during mutation.

---

## Recommended Test Implementation Priority

### Immediate (Week 1) — Zero-Coverage P0 Engines
1. **`tests/unit/engines/balance_engine.py`** — 285 no-test mutants
2. **`tests/unit/engines/ledger_audit_engine.py`** — 190 no-test mutants

### Week 2 — High-Survivor P0 Functions
3. **`tests/properties/loan_engine/test_amortization_properties.py`** — expand for ill-conditioned, validate_schedule
4. **`tests/properties/reconciliation/test_engine_properties.py`** — expand for confidence, description similarity
5. **`tests/unit/engines/reconciliation/test_reconciliation.py`** — add `_generate_explanation` tests

### Week 3 — Property Test Expansion
6. **`tests/properties/credit_card_engine/`** — expand billing, metrics, foreclosure properties
7. **`tests/properties/loan_engine/`** — expand prepayment, floating rate properties
8. **`tests/unit/engines/account/test_account_engine.py`** — expand for account_engine metrics

### Configuration Fix
9. **Update `backend/pyproject.toml`** — add `tests/invariants/`, `tests/contract/`, `tests/integration/` to `pytest_add_cli_args_test_selection`

---

## Evidence Artifacts
- `runtime/generated/c42-test-gap-analysis.json` — Machine-readable mapping
- `runtime/generated/c42-mutation-forensics.json` — Baseline forensics
- `runtime/generated/c42-mutation-forensics.md` — Human-readable forensics