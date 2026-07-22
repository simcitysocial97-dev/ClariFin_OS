# Capability Index

> See `memory-bank/generated/coverage.md` for the auto-generated coverage matrix.
> This file is deprecated; capability-registry.yaml is now generated from manifests.

## Source of Truth

Capability manifests are in `memory-bank/capabilities/*.yaml`.
The registry is auto-generated at `memory-bank/generated/capability-registry.yaml`.
Coverage reports are at `memory-bank/generated/coverage.md` and `coverage.json`.

## Quick Links

| Capability | Link |
|------------|------|
| Household Cashflow | [coverage.md#household_cashflow](generated/coverage.md#household_cashflow) |
| Debt Management | [coverage.md#debt_management](generated/coverage.md#debt_management) |
| Credit Cards | [coverage.md#credit_cards](generated/coverage.md#credit_cards) |
| Financial Health | [coverage.md#financial_health](generated/coverage.md#financial_health) |
| Forecasting | [coverage.md#forecasting](generated/coverage.md#forecasting) |
| Transaction Intelligence | [coverage.md#transaction_intelligence](generated/coverage.md#transaction_intelligence) |
| Reconciliation | [coverage.md#reconciliation](generated/coverage.md#reconciliation) |
| Financial Events | [coverage.md#financial_events](generated/coverage.md#financial_events) |
| Recommendations | [coverage.md#recommendations](generated/coverage.md#recommendations) |
| Account Management | [coverage.md#account_management](generated/coverage.md#account_management) |
| Pattern Analysis | [coverage.md#pattern_analysis](generated/coverage.md#pattern_analysis) |

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