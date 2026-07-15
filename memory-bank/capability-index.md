# Capability Index

> Auto-generated from `capability-registry.yaml`. Do not edit manually.

## Summary

| Capability | Risk | Coverage | Golden | Properties | Architecture | Contracts | Status |
|------------|------|----------|--------|-----------|--------------|-----------|--------|
| household_cashflow | low | 3/3 | 4 | 2 | ✅ | 2 | PASS |
| debt_management | medium | 3/3 | 3 | 2 | ✅ | 4 | PASS |
| credit_cards | medium | 3/3 | 3 | 2 | ✅ | 4 | PASS |
| financial_health | low | 3/3 | 3 | 2 | ✅ | 4 | PASS |
| forecasting | low | 3/3 | 3 | 2 | ✅ | 4 | PASS |
| transaction_intelligence | low | 3/3 | 3 | 1 | ✅ | 3 | PASS |
| reconciliation | medium | 3/3 | 2 | 3 | ✅ | 3 | PASS |
| financial_events | low | 3/3 | 2 | 1 | ✅ | 3 | PASS |
| recommendations | low | 3/3 | 3 | 2 | ✅ | 2 | PASS |
| account_management | low | 3/3 | 3 | 2 | ✅ | 4 | PASS |
| pattern_analysis | low | 3/3 | 2 | 1 | ✅ | 3 | PASS |

## Capability Details

### household_cashflow
- **Risk**: low
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 4 scenarios
- **Property Tests**: 2 modules
- **Invariants**: cashflow, money
- **Dependencies**: none
- **Failure Impact**: Core financial visibility loss

### debt_management
- **Risk**: medium
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: loan, cashflow
- **Dependencies**: household_cashflow
- **Failure Impact**: Loan repayment planning breaks

### credit_cards
- **Risk**: medium
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: credit, statement
- **Dependencies**: household_cashflow
- **Failure Impact**: Credit card optimization breaks

### financial_health
- **Risk**: low
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: behaviour, account
- **Dependencies**: household_cashflow, transaction_intelligence
- **Failure Impact**: Health assessments unreliable

### forecasting
- **Risk**: low
- **Criticality**: medium
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: forecast, cashflow
- **Dependencies**: household_cashflow, debt_management, credit_cards
- **Failure Impact**: Long-term planning unreliable

### transaction_intelligence
- **Risk**: low
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 1 module
- **Invariants**: statement, transaction
- **Dependencies**: household_cashflow, credit_cards, debt_management
- **Failure Impact**: Hidden obligations undetected

### reconciliation
- **Risk**: medium
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 2 scenarios
- **Property Tests**: 3 modules
- **Invariants**: transaction, cashflow
- **Dependencies**: household_cashflow, transaction_intelligence
- **Failure Impact**: Reconciliation accuracy breaks

### financial_events
- **Risk**: low
- **Criticality**: medium
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 2 scenarios
- **Property Tests**: 1 module
- **Invariants**: transaction, date_consistency
- **Dependencies**: household_cashflow, transaction_intelligence
- **Failure Impact**: Event tracking breaks

### recommendations
- **Risk**: low
- **Criticality**: medium
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: behaviour, account
- **Dependencies**: household_cashflow, debt_management, credit_cards, financial_health
- **Failure Impact**: Users miss actionable insights

### account_management
- **Risk**: low
- **Criticality**: high
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 3 scenarios
- **Property Tests**: 2 modules
- **Invariants**: account, money
- **Dependencies**: none
- **Failure Impact**: Account data inconsistent

### pattern_analysis
- **Risk**: low
- **Criticality**: medium
- **Coverage**: 3 smoke tests
- **Golden Datasets**: 2 scenarios
- **Property Tests**: 1 module
- **Invariants**: transaction, date_consistency
- **Dependencies**: household_cashflow, transaction_intelligence
- **Failure Impact**: Pattern detection breaks