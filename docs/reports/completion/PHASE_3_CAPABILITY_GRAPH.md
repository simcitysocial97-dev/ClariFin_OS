# Phase 3 — Runtime Capability Graph

## Audit Date: 2026-07-23

## Database Schema
- statements, transactions, members, import_mappings, reconciliations
- accounts, loans, investments, loan_payments, loan_prepayments, loan_rate_changes

## Backend Summary
- Repositories: 22
- Services: 18
- Engines: 11
- Routers: 22

## Capability Status
- Accounts: ✅ Complete
- Transactions: ⚠️ Partial (no service layer)
- Statements: ✅ Complete
- Reconciliation: ✅ Complete
- Cashflow: ✅ Complete
- Behaviour: 🔁 Duplicate routers
- Credit Cards: ✅ Complete
- Loans: ✅ Complete
- Financial Intelligence: ✅ Complete
- Forecasting: ✅ Complete (part of FI)
- Goals: ✅ Complete (part of FI)
- Recommendations: ✅ Complete
- Financial Events: ❌ Missing router
- Dashboard: ✅ Complete

## Broken Edges
1. Upload → Intelligence (not automatic)
2. Upload → Recommendations (not automatic)
3. Intelligence → Recommendations (no data flow)
4. Duplicate routers: behaviour.py + behavior.py
5. Financial Events: no router
6. Transactions: no service layer

## Pipeline Integrity: 70%

## Frontend Integration: Pending
