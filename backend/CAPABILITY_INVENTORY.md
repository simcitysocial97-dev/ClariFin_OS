# Capability Inventory

*API Endpoints only - schemas in openapi.json*

## Transactions/Ingestion

  - GET /api/banks
  - POST /api/upload
  - POST /api/import/detect
  - POST /api/import/execute
  - GET /api/transactions
  - GET /api/overview
  - GET /api/categories
  - GET /api/analytics

## Reconciliation

  - GET /api/audit/report
  - GET /api/reconciliations/pending
  - GET /api/reconciliations/scan
  - POST /api/reconciliations/create
  - POST /api/reconciliations/batch-insert
  - POST /api/reconciliations/{reconciliation_id}/confirm
  - POST /api/reconciliations/{reconciliation_id}/reject
  - POST /api/reconciliations/{reconciliation_id}/undo
  - GET /api/reconciliations/stats

## Financial Intelligence

  - GET /api/behavior/summary
  - GET /api/behavior/score
  - GET /api/behavior/insights
  - GET /api/v1/behaviour/profile
  - GET /api/v1/behaviour/wellness-score
  - GET /api/v1/behaviour/debt-health
  - GET /api/v1/behaviour/cashflow-health
  - GET /api/v1/behaviour/patterns
  - GET /api/v1/behaviour/recommendations
  - GET /api/v1/behaviour/monthly-report
  - GET /api/v1/behaviour/stress-index
  - GET /api/v1/behaviour/revolver-status
  - GET /api/v1/behaviour/household-divergence
  - GET /api/v1/financial-intelligence/cashflow-forecast
  - GET /api/v1/financial-intelligence/liquidity-forecast
  - GET /api/v1/financial-intelligence/credit-forecast
  - GET /api/v1/financial-intelligence/outlook
  - GET /api/v1/financial-intelligence/report
  - GET /api/v1/financial-intelligence/priorities
  - GET /api/v1/financial-intelligence/confidence

## Loans

  - GET /api/loans
  - GET /api/loans/{loan_id}
  - POST /api/loans
  - PUT /api/loans/{loan_id}
  - DELETE /api/loans/{loan_id}
  - GET /api/loans/{loan_id}/schedule
  - POST /api/loans/{loan_id}/prepayment-simulation
  - POST /api/loans/{loan_id}/foreclosure-simulation
  - POST /api/loans/{loan_id}/rate-change-simulation
  - POST /api/loans/{loan_id}/payments
  - GET /api/loans/analysis/priority
  - POST /api/loans/{loan_id}/analysis/prepayment-vs-foreclosure
  - POST /api/loans/analysis/surplus-allocation

## Credit Cards

  - GET /api/statements
  - GET /api/cards
  - GET /api/statements/{statement_id}/validate
  - GET /api/v1/credit-cards
  - GET /api/v1/credit-cards/{card_id}
  - POST /api/v1/credit-cards
  - PUT /api/v1/credit-cards/{card_id}
  - DELETE /api/v1/credit-cards/{card_id}
  - GET /api/v1/credit-cards/{card_id}/statements
  - POST /api/v1/credit-cards/{card_id}/statements
  - GET /api/v1/credit-cards/{card_id}/outstanding
  - GET /api/v1/credit-cards/{card_id}/utilization
  - GET /api/v1/credit-cards/{card_id}/metrics
  - GET /api/v1/credit-cards/{card_id}/next-statement-date
  - POST /api/v1/credit-cards/{card_id}/payments
  - POST /api/v1/credit-cards/{card_id}/emi-conversion
  - POST /api/v1/credit-cards/{card_id}/foreclosure

## Accounts

  - GET /api/v1/accounts
  - POST /api/v1/accounts
  - GET /api/v1/accounts/{account_id}
  - PUT /api/v1/accounts/{account_id}
  - DELETE /api/v1/accounts/{account_id}
  - POST /api/v1/accounts/{account_id}/balance-history
  - GET /api/v1/accounts/{account_id}/balance-history
  - GET /api/v1/accounts/{account_id}/balance-history/latest
  - GET /api/v1/accounts/{account_id}/analytics
  - GET /api/v1/accounts/{account_id}/metrics
  - GET /api/v1/accounts/{account_id}/status
  - GET /api/v1/accounts/{account_id}/dormancy
  - GET /api/v1/institutions
  - POST /api/v1/institutions
  - GET /api/v1/institutions/{institution_id}
  - PUT /api/v1/institutions/{institution_id}
  - POST /api/v1/accounts/{account_id}/links
  - DELETE /api/v1/accounts/{account_id}/links/{linked_account_id}
  - GET /api/v1/accounts/{account_id}/links
  - GET /api/accounts/manage
  - POST /api/accounts/manage
  - PUT /api/accounts/manage/{account_id}
  - DELETE /api/accounts/manage/{account_id}
  - GET /api/accounts/{account_id}/balance
  - GET /api/accounts/{account_id}/running-balance

## Investments

  - GET /api/investments
  - POST /api/investments
  - PUT /api/investments/{investment_id}
  - DELETE /api/investments/{investment_id}

## Goals

  - POST /api/v1/goals/
  - GET /api/v1/goals/
  - GET /api/v1/goals/{goal_id}
  - GET /api/v1/goals/{goal_id}/projection
  - GET /api/v1/goals/{goal_id}/health
  - DELETE /api/v1/goals/{goal_id}

## Dashboard/Analytics

  - GET /api/cashflow/monthly
  - GET /api/v1/cashflow/monthly
  - GET /api/dashboard/summary
  - GET /api/export/csv
  - GET /api/members
  - POST /api/members
  - GET /api/networth
  - GET /api/v1/optimization/plan
  - GET /api/v1/optimization/debt-strategy
  - GET /api/v1/optimization/goal-priority
  - GET /api/v1/optimization/surplus-allocation
  - POST /api/v1/patterns/confirm
  - POST /api/v1/patterns/new
  - GET /api/v1/patterns/providers
  - GET /api/v1/patterns/purposes
  - POST /api/v1/scenarios/expense-reduction
  - POST /api/v1/scenarios/income-change
  - POST /api/v1/scenarios/debt-prepayment
  - POST /api/v1/scenarios/new-loan
  - POST /api/v1/scenarios/credit-behaviour
  - POST /api/v1/scenarios/compare

## Household/Owner ID Defaults

- `household_id`: default = "default" (behaviour endpoints: profile, wellness-score, debt-health, cashflow-health, patterns, recommendations, monthly-report)
- `household_id`: default = "primary" (stress-index, revolver-status, household-divergence)
- `member` query param: default = "All" (transactions, categories, analytics)
