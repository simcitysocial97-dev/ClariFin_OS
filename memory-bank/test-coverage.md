# Test Coverage Matrix - ADF Framework

## Property Tests Summary

| Engine | Test File | Tests | Status |
|--------|-----------|-------|--------|
| Cashflow | `tests/properties/test_cashflow.py` | 2 | ✅ Pass |
| Loan | `tests/properties/test_loan.py` | 3 | ✅ Pass |
| Forecast | `tests/properties/test_forecast.py` | 4 | ✅ Pass |
| Behaviour (Money) | `tests/properties/test_money_invariants.py` | 18 | ✅ Pass |
| **Total** | | **26** | ✅ Pass |

## Invariant Coverage

| Invariant Module | Functions | Coverage |
|-----------------|-----------|----------|
| `money.py` | `assert_money_invariants`, `assert_all_paise_integers` | ✅ Complete |
| `cashflow.py` | `assert_cashflow_invariants`, `assert_cashflow_result_invariants` | ✅ Complete |
| `loan.py` | `assert_loan_schedule_valid`, `assert_loan_invariants`, `assert_prepayment_result_valid` | ✅ Complete |
| `forecast.py` | `assert_forecast_invariants`, `assert_liquidity_forecast_invariants` | ✅ Complete |
| `credit.py` | `assert_credit_invariants`, `assert_utilization_valid`, `assert_emi_conversion_valid`, `assert_minimum_due_valid` | ✅ Complete |
| `statement.py` | `assert_statement_integrity`, `assert_statement_detection_invariants` | ✅ Complete |

## Builder Coverage

| Builder | Methods | Status |
|---------|---------|--------|
| `HouseholdBuilder` | `with_id()`, `build()` | ✅ Complete |
| `AccountBuilder` | `with_balance()`, `with_type()`, `with_bank()`, `build()` | ✅ Complete |
| `TransactionBuilder` | `with_amount()`, `with_type()`, `with_date()`, `build()` | ✅ Complete |
| `LoanBuilder` | `with_principal()`, `with_outstanding()`, `with_rate_bps()`, `with_tenure()`, `with_date()`, `with_type()`, `build()` | ✅ Complete |
| `StatementBuilder` | `with_statement_date()`, `with_due_date()`, `with_outstanding()`, `with_min_due()`, `build()` | ✅ Complete |

## Strategy Coverage

| Strategy | Purpose | Status |
|----------|---------|--------|
| `paise_strategy` | Integer paise generation (-100M to 100M) | ✅ Complete |
| `positive_paise_strategy` | Positive paise only | ✅ Complete |
| `confidence_bps_strategy` | 0-10000 bps range | ✅ Complete |
| `iso_date_strategy` | ISO 8601 date strings | ✅ Complete |
| `loan_rate_bps_strategy` | 600-2400 bps (6%-24%) | ✅ Complete |
| `credit_rate_bps_strategy` | 1800-4800 bps (18%-48%) | ✅ Complete |
| `cash_summary_strategy` | Income/expense pairs | ✅ Complete |
| `financial_event_strategy` | Cashflow overlay events | ✅ Complete |
| `loan_data_strategy` | Complete loan test data | ✅ Complete |

## Validation Commands

```bash
# Run property tests
./venv/bin/python3 -m pytest tests/properties -v

# Run ruff check
./venv/bin/python3 -m ruff check tests/domain tests/properties

# Run mypy check
./venv/bin/python3 -m mypy tests/domain tests/properties