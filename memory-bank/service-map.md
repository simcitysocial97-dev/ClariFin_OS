# Service Map

## Routers (HTTP Entry Points - 25 files)

| Router | Responsibilities |
|--------|------------------|
| `accounts.py` | Account CRUD, balance queries |
| `audit.py` | Audit trail queries |
| `banks.py` | Bank metadata, settings |
| `behavior.py` / `behaviour.py` | Behaviour score endpoints (duplicated) |
| `cards_statements.py` | Credit card statement parsing |
| `cashflow.py` | Cashflow analysis, monthly trends |
| `credit_cards.py` | Credit card management |
| `dashboard.py` | Dashboard summary aggregation |
| `export.py` | Data export (CSV, JSON) |
| `financial_intelligence.py` | Risk/opportunity analysis |
| `goals.py` | Financial goal tracking |
| `health.py` | Health check endpoints |
| `import_router.py` | Statement import pipeline |
| `investments.py` | Investment tracking (DEAD route) |
| `loans.py` | Loan management (DEAD route) |
| `managed_accounts.py` | Managed account operations |
| `members.py` | Household member management |
| `networth.py` | Net worth calculations |
| `optimization.py` | Optimization suggestions |
| `patterns.py` | Pattern management |
| `reconciliation.py` | Transaction reconciliation |
| `scenarios.py` | What-if scenarios |
| `transactions.py` | Transaction CRUD, queries |

## Services (Orchestration Layer - 17 files)

| Service | Extends | Responsibilities |
|---------|---------|------------------|
| `AccountService` | BaseService | Account lifecycle, balance management |
| `AuditService` | BaseService | Audit log orchestration |
| `BehaviorService` | BaseService | Legacy behaviour score computation |
| `BehaviourService` | BaseService | Canonical behaviour score computation |
| `CashflowService` | BaseService | Monthly cashflow analysis |
| `CreditCardService` | BaseService | Card operations, statement processing |
| `DashboardService` | BaseService | Dashboard data aggregation |
| `FinancialEventsService` | BaseService | Financial event lifecycle |
| `FinancialIntelligenceService` | BaseService | Risk/opportunity analysis |
| `LoanAnalysisService` | BaseService | Loan analytics |
| `LoanService` | BaseService | Loan lifecycle |
| `LoanSimulationService` | BaseService | Loan scenario simulation |
| `NetWorthService` | BaseService | Net worth calculations |
| `ReconciliationService` | BaseService | Transaction matching |
| `StatementService` | BaseService | Statement import workflow |
| `TransactionIntelligenceService` | BaseService | Transaction analysis |

## Engines (Pure Computation - 12+ packages)

| Engine | Purpose |
|--------|---------|
| `reconciliation_engine.py` | Hungarian algorithm bipartite matching |
| `balance_engine.py` | Running balance computation |
| `cashflow_engine.py` | Monthly cashflow with financial events |
| `behavior_engine.py` | Legacy behaviour scoring (deprecated) |
| `behaviour_engine/` | Canonical behaviour engine module |
| `loan_engine/` | Amortization, reducing balance |
| `credit_card_engine/` | Outstanding/interest calculations |
| `account_engine/` | Account state management |
| `financial_events/` | Event lifecycle processing |
| `financial_intelligence/` | Risk/opportunity analysis |
| `transaction_intelligence/` | EMI/CC payment detection |
| `recommendation_engine/` | Suggestion generation |
| `nudge_engine.py` | Behavioral nudges |
| `insight_generator.py` | Insight extraction |
| `ledger_audit_engine.py` | Ledger audit |

## Repositories (SQL Access - 26 files)

| Repository | Ownership | Key Operations |
|------------|-----------|----------------|
| `AccountRepository` | accounts table | CRUD, balance queries |
| `AccountBalanceRepository` | account_balances | Balance history |
| `AccountLinkRepository` | linkages | Member-account links |
| `AlertRepository` | alerts | Alert CRUD |
| `BankRepository` | bank metadata | Bank settings |
| `BehaviourRepository` | behaviour_snapshots | Score persistence |
| `CashflowRepository` | cashflow_monthly | Monthly aggregates |
| `CreditCardRepository` | cards | Card CRUD |
| `CreditCardStatementRepository` | statements | Statement CRUD |
| `FinancialEventRepository` | financial_events | Event lifecycle |
| `FinancialGoalRepository` | financial_goals | Goal tracking |
| `ImportMappingRepository` | import_mappings | Column mapping |
| `InstitutionRepository` | institutions | Bank metadata |
| `InvestmentRepository` | investments | Investment CRUD |
| `LiquidityPatternRepository` | liquidity patterns | Pattern matching |
| `LoanRepository` | loans | Loan CRUD |
| `LoanPaymentRepository` | loan_payments | Payment history |
| `MemberRepository` | members | Household members |
| `NetWorthRepository` | snapshots | Net worth history |
| `PatternRepository` | patterns | Pattern CRUD |
| `ReconciliationRepository` | reconciliations | Match CRUD |
| `ReconciliationAuditRepository` | audit_log | Audit trail |
| `StatementRepository` | statements | PDF processing |
| `TransactionRepository` | transactions | Transaction CRUD |

All repositories extend `BaseRepository` (in `base.py`) which provides `_get_conn()` → sqlite3.Connection.