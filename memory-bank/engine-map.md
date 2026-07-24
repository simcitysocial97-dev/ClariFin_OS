# Engine Dependency Map

> Auto-generated from engine contracts. When changing an engine, all downstream consumers must be re-validated.

```
CashflowEngine (pure)
    ├── FinancialEventsEngine (lineage_walker)
    └── cashflow_monthly ← CashflowRepository

BalanceEngine (impure: sqlite3)
    └── account_balances ← AccountBalanceRepository

ReconciliationEngine (mostly pure)
    └── matches + audit_log ← ReconciliationRepository

AccountEngine (pure)
    ├── balance.py
    ├── cashflow.py
    ├── dormant.py
    ├── history.py
    ├── lifecycle.py
    └── metrics.py

BehaviourEngine (pure, 12 files)
    ├── account.py → AccountEngine balance.py
    ├── cashflow.py
    ├── credit_dependency.py → CreditCardEngine
    ├── debt.py
    ├── income.py
    ├── lifestyle.py
    ├── patterns.py
    ├── profile.py → (aggregates sub-scores)
    ├── resilience.py
    ├── savings.py
    ├── stress.py
    └── wellness.py

CreditCardEngine (pure, 7 files)
    ├── billing.py
    ├── emi.py → LoanEngine (amortization pattern)
    ├── foreclosure.py
    ├── interest.py
    ├── metrics.py
    ├── outstanding.py
    └── utilization.py

LoanEngine (pure, 9 files)
    ├── amortization.py
    ├── emi.py
    ├── floating_rate.py
    ├── foreclosure.py
    ├── metrics.py
    ├── models.py
    ├── prepayment.py
    └── utils.py

FinancialIntelligence (mostly pure, 8 files)
    ├── forecasting.py → CashflowEngine
    ├── goal_planner.py
    ├── intelligence.py → BehaviourEngine
    ├── optimization.py
    ├── scenario.py
    └── utils.py

TransactionIntelligence (pure, 4 files)
    ├── cash_conversion_detector.py → CreditCardEngine
    ├── cc_payment_detector.py → CreditCardEngine
    ├── detector_result.py
    └── loan_emi_detector.py → LoanEngine

NudgeEngine (pure)
    └── standalone — no engine dependencies

InsightGenerator (pure)
    └── standalone — no engine dependencies

RecommendationEngine (pure)
    └── standalone — no engine dependencies

LedgerAuditEngine (impure: sqlite3)
    └── standalone — reads DB for audit queries
```

### Change Impact Rules

| When you change... | Must re-validate... |
|--------------------|---------------------|
| CashflowEngine | Cashflow property tests, Cashflow golden scenarios, FinancialIntelligence |
| LoanEngine | Loan property tests, Loan golden scenarios, TransactionIntelligence (EMI) |
| CreditCardEngine | Credit Card property tests, Credit Card golden scenarios, BehaviourEngine (credit_dependency), TransactionIntelligence |
| AccountEngine | Account property tests, BehaviourEngine (account.py) |
| BehaviourEngine | Behaviour property tests, Behaviour golden scenarios, FinancialIntelligence |
| FinancialIntelligence | Forecasting property tests |
| TransactionIntelligence | Transaction intelligence property tests |
| NudgeEngine/InsightGenerator/RecommendationEngine | Respective property tests (when created) |
| ReconciliationEngine/BalanceEngine/LedgerAuditEngine | Respective property tests (when created) |