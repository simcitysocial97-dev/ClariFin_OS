# Engine Validation Framework — Coverage Matrix

## Engine Maturity

| Engine | State | Contract | Properties | Golden | Invariants | Mutation |
|--------|-------|----------|------------|--------|------------|----------|
| CashflowEngine | Mature | ✅ | ✅ 6 tests | ✅ 2 scenarios | ✅ | ❌ |
| LoanEngine | Mature | ✅ | ✅ 6 tests | ⚠️ 2 scenarios | ✅ | ❌ |
| CreditCardEngine | Stable | ✅ | ✅ 6 tests | ✅ 1 scenario | ✅ | ❌ |
| BehaviourEngine | Stable | ✅ | ✅ 5 tests | ✅ 2 scenarios | ✅ (new) | ❌ |
| AccountEngine | Stable | ✅ | ✅ 2 tests | ⚠️ 1 scenario | ✅ (new) | ❌ |
| ReconciliationEngine | Good | ✅ | ❌ | ❌ | ⚠️ Partial | ❌ |
| FinancialIntelligence | Experimental | ✅ | ✅ 4 tests | ❌ | ✅ | ❌ |
| TransactionIntelligence | Experimental | ✅ | ✅ 1 test | ❌ | ❌ | ❌ |
| FinancialEvents | Experimental | ✅ | ❌ | ❌ | ❌ | ❌ |
| NudgeEngine | Prototype | ✅ | ❌ | ❌ | ❌ | ❌ |
| InsightGenerator | Prototype | ✅ | ❌ | ❌ | ❌ | ❌ |
| RecommendationEngine | Prototype | ✅ | ❌ | ❌ | ❌ | ❌ |
| LedgerAuditEngine | Prototype | ✅ | ❌ | ❌ | ❌ | ❌ |

## Property Tests Summary

| Test File | Tests | Engines Covered | Status |
|-----------|-------|-----------------|--------|
| `tests/properties/test_cashflow.py` | 2 | CashflowEngine | ✅ Legacy |
| `tests/properties/test_loan.py` | 3 | LoanEngine | ✅ Legacy |
| `tests/properties/test_forecast.py` | 4 | FinancialIntelligence | ✅ Legacy |
| `tests/properties/test_money_invariants.py` | 18 | Behaviour, Money | ✅ Legacy |
| `tests/properties/cashflow/test_engine_properties.py` | 4 | CashflowEngine | ✅ New |
| `tests/properties/lending/test_engine_properties.py` | 5 | LoanEngine + CreditCardEngine | ✅ New |
| `tests/properties/credit_cards/test_engine_properties.py` | 3 | CreditCardEngine + TransactionIntelligence | ✅ New |
| `tests/properties/behaviour/test_engine_properties.py` | 4 | BehaviourEngine + AccountEngine | ✅ New |
| `tests/properties/forecasting/test_engine_properties.py` | 2 | FinancialIntelligence | ✅ New |
| **Total** | **45** | **10 engines** | |

## Invariant Coverage

| Invariant Module | Functions | Coverage |
|-----------------|-----------|----------|
| `money.py` | `assert_money_invariants`, `assert_all_paise_integers` | ✅ Complete |
| `cashflow.py` | `assert_cashflow_invariants`, `assert_cashflow_result_invariants` | ✅ Complete |
| `loan.py` | `assert_loan_schedule_valid`, `assert_loan_invariants`, `assert_prepayment_result_valid` | ✅ Complete |
| `forecast.py` | `assert_forecast_invariants`, `assert_liquidity_forecast_invariants` | ✅ Complete |
| `credit.py` | `assert_credit_invariants`, `assert_utilization_valid`, `assert_emi_conversion_valid`, `assert_minimum_due_valid` | ✅ Complete |
| `statement.py` | `assert_statement_integrity`, `assert_statement_detection_invariants` | ✅ Complete |
| `behaviour.py` | `assert_behaviour_score_valid`, `assert_wellness_metrics_valid`, `assert_temporal_pattern_consistency`, `assert_credit_dependency_ratio_valid` | ✅ New |
| `account.py` | `assert_account_state_valid`, `assert_owner_scope_valid`, `assert_account_closed_valid` | ✅ New |
| `transaction.py` | `assert_transaction_ordering_valid`, `assert_amount_sign_convention`, `assert_reconciliation_match_valid` | ✅ New |
| `date_consistency.py` | `assert_date_iso_format`, `assert_month_bucket_alignment`, `assert_date_sequence_ordered`, `assert_date_in_range`, `assert_data_has_required_dates` | ✅ New |

## Golden Dataset Coverage

| Dataset | Scenario | Engines Exercised | Status |
|---------|----------|-------------------|--------|
| `normal_household.json` | Standard household | Cashflow, Behaviour | ✅ Legacy |
| `high_debt_household.json` | High debt | Cashflow, Loan, Behaviour | ✅ Legacy |
| `irregular_income.json` | Variable income | Cashflow, Behaviour | ✅ Legacy |
| `cc_statement_scenario.json` | CC processing | CreditCard, TransactionIntelligence | ✅ Legacy |
| `salary_only.json` | Single income | Cashflow, Behaviour | ✅ New |
| `salary_plus_loan.json` | Income + loan | Cashflow, Loan, Behaviour | ✅ New |
| `credit_card_revolver.json` | Revolving CC debt | Cashflow, CreditCard, Behaviour | ✅ New |
| `cash_advance.json` | Cash advance | Cashflow, CreditCard, TransactionIntelligence | ✅ New |
| `multiple_loans.json` | 2+ concurrent loans | Cashflow, Loan, Behaviour | ✅ New |
| `family_household.json` | Multi-member | Cashflow, Behaviour | ✅ New |

## Golden Regression Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/golden/test_regression.py` | 11 (4 legacy + 7 new) | ✅ |

## Remaining Gaps

| Engine | Missing Coverage |
|--------|-----------------|
| ReconciliationEngine | No property tests, no golden scenario, no invariants |
| FinancialEvents (lineage_walker) | No property tests, no golden scenario |
| NudgeEngine | No property tests, no golden scenario |
| InsightGenerator | No property tests, no golden scenario |
| RecommendationEngine | No property tests, no golden scenario |
| LedgerAuditEngine | No property tests, no golden scenario |

## Memory Bank Artifacts

| Artifact | Purpose | Status |
|----------|---------|--------|
| `engine-contracts.md` | Full contracts for all 15 engines | ✅ New |
| `engine-maturity.md` | Maturity tracking by engine | ✅ New |
| `engine-map.md` | Dependency diagram + change impact rules | ✅ New |
| `regression-history.md` | Bug → regression promotion log | ✅ New |

## Validation Commands

```bash
# Run property tests (includes all subdirectories)
./venv/bin/python3 -m pytest tests/properties -v

# Run golden tests
./venv/bin/python3 -m pytest tests/golden -v

# Run all validation
./scripts/verify-local.sh

# Run ruff check
./venv/bin/python3 -m ruff check tests/domain tests/properties tests/golden

# Run mypy check
./venv/bin/python3 -m mypy tests/domain tests/properties tests/golden
