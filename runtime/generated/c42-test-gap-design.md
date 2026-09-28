# C42 Phase 3 — Test Gap Design

**Generated:** 2026-08-22T09:53:11+05:30
**Repository SHA:** 34d22cb763ec05da24f02a420905047afdc64b7f
**Baseline:** 4,315 surviving mutants, 7,439 no-test mutants

---

## Design Principle

For each genuine surviving mutant:
1. **Why existing tests don't detect it** — specific gap in current test coverage
2. **Expected domain behavior** — the mathematical/business invariant
3. **Missing invariant** — what property is not verified
4. **Proposed test** — concrete test with name, type, location
5. **Why this test kills the mutant** — which mutation operators it targets
6. **Neighboring mutants also killed** — efficiency of the test

---

## Priority 1: Zero-Coverage P0 Engines (NEW Test Files Required)

### balance_engine — 285 no-test mutants (NEW: `tests/unit/engines/balance_engine.py`)

| Function | Mutants | Test Design |
|----------|---------|-------------|
| `_parse_date_to_ymd` | 38 | **Property:** All 10 Indian formats → valid YYYY-MM-DD. **Unit:** unparseable→empty, idempotent, whitespace handling. |
| `_parse_date_for_sort` | 3 | **Unit:** valid→YMD, invalid→'0000-00-00'. **Property:** sort order matches chronology. |
| `compute_running_balance` | 59 | **Integration:** temp DB, verify running = starting + Σ(credit-debit) in SQL order. Account-scoped, fallback parsing, output fields. |
| `compute_account_balance` | 41 | **Integration:** SQL SUM vs manual iteration. **Unit:** display format, zero transactions. |
| `validate_statement_balance` | 57 | **Integration:** match/mismatch status, difference paise+display, txn count. |
| `get_accounts_list` | 42 | **Integration:** multiple accounts, empty account (LEFT JOIN), ordering by bank. |
| `_format_paise` | 41 | **Property:** Indian grouping (3-2-2...) for 0-10 crores. **Unit:** negative prefix, zero, 2-digit paise. |

### ledger_audit_engine — 190 no-test mutants (NEW: `tests/unit/engines/ledger_audit_engine.py`)

| Function | Mutants | Test Design |
|----------|---------|-------------|
| `validate_ledger_integrity` | 95 | **Integration (7 tests):** clean DB→PASS; each of 6 violations→FAIL with correct type, txn_id, message. |
| `verify_hash_signatures` | 95 | **Integration (4 tests):** correct hashes→PASS; tampered→FAIL with txn_id/stored/computed; empty hash skipped; case-insensitive. |
| `run_full_audit` | ~10 | **Integration (4 tests):** both PASS→overall PASS; each FAIL combo→overall FAIL. |

---

## Priority 2: High-Survivor Functions with No Direct Tests

### reconciliation_engine — `_generate_explanation` (37 survived)

**Why existing tests fail:** Tests check match detection but NOT the explanation string generation.

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_generate_explanation_exact_match` | Unit | `tests/unit/engines/reconciliation/test_reconciliation.py` | 19 mutants (exact match branch: string constants, date formatting, rupee conversion) |
| `test_generate_explanation_window_match` | Unit | `tests/unit/engines/reconciliation/test_reconciliation.py` | 18 mutants (window match branch: both dates, day count) |
| `test_generate_explanation_amount_in_rupees` | Unit | `tests/unit/engines/reconciliation/test_reconciliation.py` | Arithmetic mutants on paise/100 |

**Missing invariant:** Exact format with same date; window format with both dates and day diff; amount in rupees (2 decimals); account IDs included.

### loan_engine — `amortization.validate_schedule` (40 survived)

**Why existing tests fail:** NO tests directly call `validate_schedule`. Existing tests use `validate_schedule_invariants` (subset) but miss EMI consistency, tenure length, debug_mode raise.

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_validate_schedule_emi_consistency` | Unit | `tests/unit/engines/loan/test_amortization.py` | Conditional mutants on EMI consistency loop (all but last equal) |
| `test_validate_schedule_tenure_length` | Unit | `tests/unit/engines/loan/test_amortization.py` | Conditional mutants on length check |
| `test_validate_schedule_debug_mode_raises` | Unit | `tests/unit/engines/loan/test_amortization.py` | Conditional mutants on debug_mode branch (raise vs return False) |
| `test_validate_schedule_all_invariants` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | All 40 mutants across 7 invariants |

**Missing invariant:** All 7 invariants checked; EMI consistency excludes last row; debug_mode raises ValueError; non-debug returns bool.

---

## Priority 3: Expand Property Tests for Boundary Conditions

### reconciliation_engine — `_calculate_confidence` (31 survived)

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_calculate_confidence_date_diff_boundaries` | Property | `tests/properties/reconciliation/test_engine_properties.py` | Conditional on date_diff: 0→0.4, 1→0.3, ≥2→0.0 |
| `test_calculate_confidence_description_boundary` | Property | `tests/properties/reconciliation/test_engine_properties.py` | Conditional on desc_sim: 0.7→0.8, 0.7001→1.0 |
| `test_calculate_confidence_capping` | Unit | `tests/properties/reconciliation/test_engine_properties.py` | Cap at 1.0, rounding to 4 decimals |
| `test_calculate_confidence_precision` | Unit | `tests/properties/reconciliation/test_engine_properties.py` | Rounding arithmetic |

### reconciliation_engine — `_simple_description_similarity` (18 survived)

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_simple_description_similarity_both_keywords` | Property | `tests/properties/reconciliation/test_engine_properties.py` | Both have keywords→1.0, all 7 keywords, case-insensitive |
| `test_simple_description_similarity_one_keyword` | Unit | `tests/properties/reconciliation/test_engine_properties.py` | Only one has keyword→0.0 |
| `test_simple_description_similarity_empty` | Unit | `tests/properties/reconciliation/test_engine_properties.py` | Empty/None→0.0 |
| `test_simple_description_similarity_case_insensitive` | Property | `tests/properties/reconciliation/test_engine_properties.py` | UPPER/lower/Mixed all detected |

### loan_engine — `amortization.generate_schedule` (180 survived)

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_generate_schedule_ill_conditioned_detection` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | Ill-conditioned branch (annuity_factor/2 > principal/100), monthly re-anchoring |
| `test_generate_schedule_last_month_settlement` | Unit | `tests/unit/engines/loan/test_amortization.py` | Last month: balance=0, principal=reported_balance, actual_emi=principal+interest |
| `test_generate_schedule_interest_rounding_half_even` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | ROUND_HALF_EVEN at 0.5 paise boundaries |
| `test_generate_schedule_principal_bounds` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | Principal component ∈ [0, emi_paise] |
| `test_generate_schedule_cumulative_interest_monotonic` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | Cumulative interest never decreases |
| `test_generate_schedule_payment_dates` | Property | `tests/properties/loan_engine/test_amortization_properties.py` | _add_months with month-end (Jan 31→Feb 28) |

### credit_card_engine — `metrics.compute_financial_metrics` (64 survived)

| Test | Type | Location | Kills |
|------|------|----------|-------|
| `test_compute_financial_metrics_revolving_balance` | Property | `tests/properties/credit_card_engine/test_billing_properties.py` | Revolving = max(0, outstanding-payment) |
| `test_compute_financial_metrics_minimum_due` | Property | `tests/properties/credit_card_engine/test_billing_properties.py` | Min due = max(5% outstanding, fixed_min) boundary |
| `test_compute_financial_metrics_interest_accrual` | Property | `tests/properties/credit_card_engine/test_interest_properties.py` | Interest = revolving × daily_rate × days |
| `test_compute_financial_metrics_utilization_capped` | Property | `tests/properties/credit_card_engine/test_billing_properties.py` | Utilization = outstanding/limit capped at 1.0 |

---

## Priority 4: Configuration Fix

### `backend/pyproject.toml` — Expand Mutation Test Selection

```toml
# Current (insufficient):
pytest_add_cli_args_test_selection = ["tests/unit/", "tests/properties/"]

# Required (add these):
pytest_add_cli_args_test_selection = [
    "tests/unit/",
    "tests/properties/",
    "tests/invariants/",      # Mathematical invariants, determinism
    "tests/contract/",        # API contract tests
    "tests/integration/"      # Cross-component integration
]
```

**Rationale:** Many "survived" mutants in reconciliation_engine, loan_engine, credit_card_engine are in code paths exercised by invariant/contract/integration tests — but those tests don't run during mutation. Adding them will kill survivors without new test code.

---

## Test Implementation Priority Order

| Week | Focus | Files to Create/Modify |
|------|-------|------------------------|
| 1 | Zero-coverage P0 engines | `tests/unit/engines/balance_engine.py` (NEW), `tests/unit/engines/ledger_audit_engine.py` (NEW) |
| 2 | No-direct-test functions | `tests/unit/engines/reconciliation/test_reconciliation.py` (add 3 tests), `tests/unit/engines/loan/test_amortization.py` (add 4 tests) |
| 3 | Property test expansion | `tests/properties/reconciliation/test_engine_properties.py` (add 8 tests), `tests/properties/loan_engine/test_amortization_properties.py` (add 6 tests), `tests/properties/credit_card_engine/` (add 4 tests) |
| 4 | Config + validation | `backend/pyproject.toml` (expand test selection), local mutation smoke test |

---

## Expected Mutation Impact

| Test Batch | Mutants Targeted | Estimated Killed |
|------------|------------------|------------------|
| balance_engine (7 functions) | 285 no-test | 285 (100% of no-test) |
| ledger_audit_engine (3 functions) | 190 no-test | 190 (100% of no-test) |
| `_generate_explanation` | 37 survived | 37 |
| `validate_schedule` | 40 survived | 40 |
| `_calculate_confidence` + `_simple_description_similarity` | 49 survived | ~40 |
| `generate_schedule` (6 property tests) | 180 survived | ~120 |
| `compute_financial_metrics` (4 property tests) | 64 survived | ~50 |
| Config fix (invariants/contract/integration) | ~1000 survived | ~500-800 |

**Projected post-implementation:**
- Surviving: 4,315 → ~1,500
- No-test: 7,439 → ~475 (only P1/P2 engines)
- Mutation score: 50.6% → ~75-80%

---

## Evidence Artifact
- `runtime/generated/c42-test-gap-design.json` — Machine-readable design with all 20 test designs
- `runtime/generated/c42-test-gap-analysis.json` — Phase 2 forensic mapping
- `runtime/generated/c42-mutation-forensics.json` — Phase 1 baseline