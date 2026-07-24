# Mutation Readiness Report

Generated: 2026-07-24T03:15:33.791231+00:00

## Engine Readiness Status

| Engine | Pure Functions | Impure Functions | Readiness | Killability Estimate |
|--------|----------------|------------------|-----------|---------------------|
| `src/engines/insight_generator.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/nudge_engine.py` | 3 | 0 | Ready | MEDIUM |
| `src/engines/transaction_intelligence/detector_result.py` | 0 | 0 | Partial | UNKNOWN |
| `src/engines/transaction_intelligence/cc_payment_detector.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/transaction_intelligence/cash_conversion_detector.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/transaction_intelligence/loan_emi_detector.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/utilization.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/interest.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/emi.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/metrics.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/foreclosure.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/billing.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/credit_card_engine/outstanding.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/financial_intelligence/models.py` | 0 | 0 | Partial | UNKNOWN |
| `src/engines/financial_intelligence/intelligence.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/financial_intelligence/scenario.py` | 6 | 0 | Ready | MEDIUM |
| `src/engines/financial_intelligence/goal_planner.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/financial_intelligence/utils.py` | 8 | 1 | Partial | MEDIUM |
| `src/engines/financial_intelligence/optimization.py` | 6 | 0 | Ready | MEDIUM |
| `src/engines/financial_intelligence/forecasting.py` | 3 | 1 | Partial | MEDIUM |
| `src/engines/account_engine/dormant.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/account_engine/cashflow.py` | 3 | 0 | Ready | MEDIUM |
| `src/engines/account_engine/balance.py` | 2 | 1 | Partial | MEDIUM |
| `src/engines/account_engine/lifecycle.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/account_engine/metrics.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/recommendation_engine/recommendations.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/income.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/cashflow.py` | 3 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/temporal.py` | 6 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/lifestyle.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/utils.py` | 3 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/resilience.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/patterns.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/debt.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/wellness.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/account.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/profile.py` | 1 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/credit_dependency.py` | 6 | 2 | Partial | MEDIUM |
| `src/engines/behaviour_engine/savings.py` | 3 | 0 | Ready | MEDIUM |
| `src/engines/behaviour_engine/stress.py` | 5 | 1 | Partial | MEDIUM |
| `src/engines/loan_engine/models.py` | 0 | 0 | Partial | UNKNOWN |
| `src/engines/loan_engine/amortization.py` | 6 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/prepayment.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/emi.py` | 4 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/metrics.py` | 5 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/utils.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/foreclosure.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/loan_engine/floating_rate.py` | 2 | 0 | Ready | MEDIUM |
| `src/engines/balance_engine.py` | 0 | 4 | Blocked | LOW |
| `src/engines/behavior_engine.py` | 0 | 5 | Blocked | LOW |
| `src/engines/ledger_audit_engine.py` | 0 | 3 | Blocked | LOW |
| `src/engines/reconciliation_engine.py` | 0 | 2 | Blocked | LOW |
| `src/engines/financial_events/lineage_walker.py` | 0 | 2 | Blocked | LOW |
| `src/engines/account_engine/history.py` | 0 | 2 | Blocked | LOW |

## Readiness Legend

| Status | Description |
|--------|-------------|
| Ready | Pure functions with no blockers - ready for mutation testing |
| Partial | Mix of pure/impure functions - limited mutation candidates |
| Blocked | Impure functions prevent safe mutation testing |

## Killability Estimate Legend

| Estimate | Meaning |
|----------|---------|
| HIGH | Strong test coverage likely to catch mutations |
| MEDIUM | Some coverage, may miss edge cases |
| LOW | Weak coverage, mutations may survive |
| UNKNOWN | Unable to determine |