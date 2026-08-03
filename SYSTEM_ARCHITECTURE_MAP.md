# SYSTEM ARCHITECTURE MAP — ClariFin_OS Backend

**Generated:** 2026-08-02  
**Scope:** `backend/src/` only  
**Database:** SQLite (`data/finance.db`)  

---

## 1. SYSTEM LAYER DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HTTP Client / Frontend                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API (FastAPI)
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  api.py  ← FastAPI app + CORS + error handlers + health            │
│     ↓                                                               │
│  routers/*  (28 routers, prefix /api or /api/v1)                   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Service calls
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  services/*  (33 service modules)                                   │
│     • BaseService (db_path + repository injection)                  │
│     • Cross-service deps: ImportService → Statement+Transaction+Behaviour  │
│                          FinancialIntelligenceService → Cashflow+Loan+CC+Behaviour+Events │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ Repos + Engines
                           ▼
┌─────────────────────┬───────────────────────────────────────────────┐
│  repositories/*     │  engines/*                                    │
│  (27 repo modules)  │  Pure computation engines (no DB access):      │
│                     │    account_engine/, behaviour_engine/,         │
│  BaseRepository     │    credit_card_engine/, loan_engine/,          │
│  (_get_conn())      │    financial_intelligence/,                    │
│                     │    transaction_intelligence/,                  │
│  DB-touching engines│    recommendation_engine/                      │
│  (direct connection)│                                               │
│    balance_engine   │  Special standalone engines:                   │
│    reconciliation_  │    nudge_engine.py (behavioral nudges)         │
│    engine.py        │    insight_generator.py (behavioral insights)  │
│    ledger_audit_    │                                               │
│    engine.py        │  PARKED (legacy):                              │
│                     │    behavior_engine.py → replaced by            │
│                     │    behaviour_engine/                           │
│                     │    cashflow_engine.py.parked                  │
└─────────────────────┴───────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  core/db/                                                           │
│     config.py    ← get_db_path() (env, override, default cascade)   │
│     connection.py ← get_connection() (+context manager)             │
│     schema.py    ← create_all(), run_migrations(), verify_schema()  │
│     transaction.py ← transaction helpers                            │
│     health.py    ← DB health checks                                 │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ sqlite3
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data/finance.db  (SQLite, WAL mode, foreign keys ON)               │
│  31 tables, 22 indexes, 2 triggers (immutability)                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. FOLDER OWNERSHIP TABLE

| Folder/File | Type | Purpose | Imported By | Imports | Status |
|---|---|---|---|---|---|
| `main.py` | Entrypoint | CLI test script for PDF extraction pipeline | — | extraction.* | PIPELINE |
| `startup.py` | Entrypoint | Startup validation (config, dirs, DB connectivity) | tests | config, core.db.connection, logger | ENTRYPOINT |
| `api.py` | Entrypoint | FastAPI app setup, middleware, router registration | uvicorn | routers.*, errors, health, config | ENTRYPOINT |
| `config.py` | Utility | Application settings (env vars with defaults) | api, startup, db, logger, routers, services | — | CANONICAL |
| `db.py` | Compatibility | Legacy FinanceDB wrapper (deprecated) | common.database, tests | core.db.schema, core.db.connection | COMPATIBILITY |
| `errors.py` | Utility | FastAPI exception handlers + custom exceptions | api.py | logger, config | UTILITY |
| `health.py` | Router | `/health` and `/ready` endpoints | api.py | core.db.connection, config | PIPELINE |
| `logger.py` | Utility | Structured logging (log_request, log_error, etc.) | All modules | config | UTILITY |
| `routers/` | Layer | 28 FastAPI routers (HTTP entry points) | api.py | services.*, models.*, core.dtos.*, core.mappers.* | CANONICAL |
| `services/` | Layer | 33 business logic modules | routers.* | repositories.*, engines.*, core.dtos.*, core.mappers.* | CANONICAL |
| `repositories/` | Layer | 27 data access modules | services.* | core.db.connection, core.db.config | CANONICAL |
| `engines/` | Layer | Computation engines (pure functions) | services.* | — (most pure calc) | CANONICAL |
| `core/db/` | Infrastructure | DB path, connections, schema, migrations | repositories, services, engines | — | CANONICAL |
| `core/dtos/` | Infrastructure | 14 DTO modules (Pydantic/typed response shapes) | routers.*, services.* | — | CANONICAL |
| `core/mappers/` | Infrastructure | 13 mapper modules (domain→DTO conversion) | routers.*, services.* | core.domain | CANONICAL |
| `core/domain/` | Infrastructure | Domain types (Money value object) | mappers | — | CANONICAL |
| `extraction/` | Pipeline | PDF/CSS/Excel extraction, categorization, parsing | import_service, ingest | camelot, pdfplumber, pandas | PIPELINE |
| `orchestration/` | Pipeline | Post-upload orchestration (statement_orchestrator) | import_service | services.*, engines.* | PIPELINE |
| `structural/` | Pipeline | Layout analysis for PDF structure | extraction/hybrid_extractor | pdfplumber | PIPELINE |
| `models/` | Infrastructure | Domain model classes (19 files) | services.*, routers.* | — | CANONICAL |
| `common/` | Utility | Shared utilities (calculations, parsing, enrichment) | services.*, extraction | — | UTILITY |
| `utils/` | Empty | Placeholder directory | — | — | UNKNOWN |
| `data/` | Storage | SQLite database file + uploads dir | — | — | PIPELINE |
| `ingest.py` | Pipeline | CLI batch ingestion (mirrors import_service flow) | — | extraction.*, repositories.*, services.* | PIPELINE |

---

## 3. STARTUP PATH (Entry Point Trace)

```
main.py (CLI test) or uvicorn src.api:app
    ↓
startup.py (optional validation)
    ↓
api.py
    ├─ add_middleware(CORSMiddleware)
    ├─ register_error_handlers(app)
    └─ register_health_routes(app)
    └─ include_router(28 routers)
         ↓
    Each router defines @router.get/@router.post endpoints
         ↓
    Each endpoint calls its service
         ↓
    Each service uses repositories (DB) and/or engines (calc)
         ↓
    Repositories use core.db.connection.get_connection()
         ↓
    Database at configured path (data/finance.db)
```

---

## 4. ROUTER GRAPH

| Router | Prefix | Endpoints | Calls Service | DTOs Used | Response Models |
|---|---|---|---|---|---|
| `accounts.py` | `/api/v1` | GET/POST /accounts, GET/PUT/DELETE /accounts/{id}, POST/GET balance-history, GET analytics, metrics, status, dormancy, GET/POST /institutions, POST/DELETE/GET /links | AccountService | AccountAnalyticsDTO, AccountDetailDTO, AccountLinkDTO, BalanceSnapshotDTO, InstitutionDTO | AccountCreateRequest, AccountUpdateRequest, BalanceSnapshotRequest, AccountLinkRequest, InstitutionCreateRequest, InstitutionUpdateRequest |
| `audit.py` | `/api/audit` | GET /report | AuditService | — | — |
| `banks.py` | `/api` | GET /banks | BankService | — | — |
| `behaviour.py` | `/api/v1/behaviour` | GET /profile, wellness-score, debt-health, cashflow-health, patterns, recommendations, monthly-report | BehaviourService | — | FinancialProfileResponse, WellnessScoreResponse, DebtHealthResponse, CashflowHealthResponse, MonthlySummaryResponse, RecommendationsResponse |
| `behaviour_workspace.py` | `/api/v1` | GET /behaviour | BehaviourWorkspaceService | — | — |
| `cards_statements.py` | `/api` | GET /statements, /cards, GET /validate | StatementService | — | — |
| `cashflow.py` | `/api` | GET /cashflow, /monthly, /categories, /transactions | CashflowService | CashflowCategoryResponse, CashflowMonthlyResponse, CashflowSummaryDTO, CashflowTransactionResponse | — |
| `cashflow_workspace.py` | `/api/v1` | GET /cashflow | CashflowWorkspaceService | — | — |
| `credit_cards.py` | `/api/v1` | GET/POST /credit-cards, CRUD /{id}, statements, outstanding, utilization, metrics, next-statement-date, payments, emi-conversion, foreclosure | CreditCardService | CreditCardSummaryDTO, EmiConversionDTO, ForeclosureDTO, StatementDTO | CreditCardCreateRequest, CreditCardUpdateRequest, EmiConversionRequest, ForeclosureRequest, PaymentRecordRequest, StatementGenerateRequest |
| `credit_cards_workspace.py` | `/api/v1` | GET /credit-cards | CreditCardsWorkspaceService | — | — |
| `dashboard.py` | `/api/dashboard` | GET /summary | DashboardService | DashboardSummaryDTO | — |
| `export.py` | `/api` | GET /export/csv | ExportService | — | — |
| `financial_events.py` | `/api/financial-events` | POST/, GET /, GET /{id} | FinancialEventsService | — | EventType, FinancialEvent |
| `financial_intelligence.py` | `/financial-intelligence` | GET /cashflow-forecast, /liquidity-forecast, /credit-forecast, /outlook, /report, /priorities, /recommendations, /recommendations/{id} | FinancialIntelligenceService, RecommendationService | — | — |
| `forecast.py` | `/api/v1` | GET /forecast | ForecastService | ForecastDTO | — |
| `import_router.py` | `/api` | POST /upload, POST /import/detect, POST /import/execute | ImportService | — | — |
| `investments.py` | `/api` | GET/POST /investments, PUT/DELETE /{id} | InvestmentService | InvestmentsDTO | — |
| `investments_workspace.py` | `/api/v1` | GET /investments | InvestmentsWorkspaceService | — | — |
| `loans.py` | `/api` | GET/POST /loans, CRUD /{id}, schedule, prepayment/foreclosure/rate-change simulations, payments, analysis/priority, analysis/prepayment-vs-foreclosure, analysis/surplus-allocation | LoanService, LoanSimulationService, LoanAnalysisService | — | LoanCreateRequest, LoanResponse, LoanUpdateRequest, ScheduleResponse, LoanPaymentCreate, PaymentRequest, PaymentResponse, PrepaymentSimulationRequest/Response, ForeclosureSimulationResponse, RateChangeSimulationRequest |
| `loans_workspace.py` | `/api/v1` | GET /loans | LoansWorkspaceService | — | — |
| `managed_accounts.py` | `/api` | GET/POST/PUT/DELETE /accounts/manage, GET /balance, /running-balance | AccountService | — | — |
| `members.py` | `/api` | GET/POST /members, CRUD /{id} | MemberService | — | — |
| `networth.py` | `/api` | GET /networth | NetWorthService | NetWorthDTO | — |
| `networth_workspace.py` | `/api/v1` | GET /net-worth | NetWorthWorkspaceService | — | — |
| `reconciliation.py` | `/api/reconciliations` | GET /, /pending, /scan, POST /create, /batch-insert, /{id}/confirm, /{id}/reject | ReconciliationService | ReconciliationDTO | — |
| `reconciliation_workspace.py` | `/api/v1` | GET /reconciliation | ReconciliationWorkspaceService | — | — |
| `transactions.py` | `/api` | GET /transactions, /overview, /categories, /analytics | TransactionService | — | — |

---

## 5. SERVICE GRAPH

| Service | Uses Repository | Uses Engine | Used By | Cross-Services |
|---|---|---|---|---|
| `AccountService` | AccountRepo, AccountBalanceRepo, InstitutionRepo, AccountLinkRepo | account_engine | accounts, managed_accounts routers | — |
| `AuditService` | (BaseService) | ledger_audit_engine | audit router | — |
| `BankService` | BankRepo | — | banks router | — |
| `BehaviourService` | TransactionRepo, AccountRepo, BehaviourRepo, PatternRepo, LoanRepo, CCRepo | behaviour_engine, recommendation_engine | behaviour router, import_service, financial_intelligence_service | — |
| `BehaviourWorkspaceService` | LoanRepo, CCRepo | — | behaviour_workspace router | — |
| `CashflowService` | CashflowRepo, TransactionRepo | — | cashflow router, financial_intelligence_service | — |
| `CashflowWorkspaceService` | (none) | — | cashflow_workspace router | CashflowService |
| `CreditCardService` | CCRepo, CCStatementRepo | credit_card_engine | credit_cards router | — |
| `CreditCardsWorkspaceService` | CCRepo, CCStatementRepo | — | credit_cards_workspace router | — |
| `DashboardService` | TransactionRepo, ReconciliationRepo | behaviour_engine.core | dashboard router | — |
| `ExportService` | TransactionRepo | — | export router | — |
| `FinancialEventsService` | FinancialEventRepo | financial_events.lineage_walker | financial_events router, financial_intelligence_service | — |
| `FinancialIntelligenceService` | CashflowRepo, FinEventRepo, FinGoalRepo | financial_intelligence | financial_intelligence router | BehaviourService, CashflowService, CreditCardService, LoanService, FinancialEventsService |
| `ForecastService` | LoanRepo, CCRepo, InvestmentRepo | — | forecast router | — |
| `ImportService` | (uses repos via Statement/Transaction) | behaviour_engine.core (cache invalidation) | import_router router | StatementService, TransactionService, BehaviourService |
| `InvestmentService` | InvestmentRepo | — | investments router | — |
| `InvestmentsWorkspaceService` | InvestmentRepo | — | investments_workspace router | — |
| `LoanService` | LoanRepo, LoanPaymentRepo | loan_engine | loans router | — |
| `LoanAnalysisService` | LoanRepo | loan_engine | loans router | — |
| `LoanSimulationService` | LoanRepo | loan_engine | loans router | — |
| `LoansWorkspaceService` | LoanRepo | — | loans_workspace router | — |
| `MemberService` | MemberRepo | — | members router | — |
| `NetWorthService` | NetWorthRepo | — | networth router | — |
| `NetWorthWorkspaceService` | AccountRepo, InvestmentRepo, LoanRepo, CCStatementRepo | — | networth_workspace router | — |
| `RecommendationService` | (none) | recommendation_engine | financial_intelligence router | — |
| `ReconciliationService` | ReconciliationRepo | reconciliation_engine | reconciliation router | — |
| `ReconciliationWorkspaceService` | ReconciliationRepo | — | reconciliation_workspace router | — |
| `StatementService` | StatementRepo | balance_engine | cards_statements router, import_service | — |
| `TransactionIntelligenceService` | TransactionRepo, LoanRepo, TxnClassRepo, AccountRepo, FinEventRepo, CCRepo, StatementRepo, LiquidityRepo | transaction_intelligence, loan_engine | (internal) | — |
| `TransactionService` | TransactionRepo | — | transactions router | — |

---

## 6. REPOSITORY GRAPH

| Repository | Database Tables | Used By | Returns |
|---|---|---|---|
| `account_repository.py` | accounts | AccountService, NetWorthWorkspaceService, BehaviourWorkspaceService, TransactionIntelligenceService, BehaviourService | list[dict], list[Account] |
| `account_balance_repository.py` | transactions, account_balance_history | AccountService | list[dict], dict\|None, int |
| `account_link_repository.py` | account_links | AccountService | bool, list[dict] |
| `alert_repository.py` | behaviour_alerts | — (UNUSED) | dict\|None, list[dict] |
| `bank_repository.py` | (banks — NOT IN SCHEMA) | BankService | list[str], dict\|None |
| `behaviour_repository.py` | behaviour_snapshots | BehaviourService, BehaviourWorkspaceService | dict\|None, list[dict] |
| `cashflow_repository.py` | transactions, accounts, financial_events | CashflowService, FinancialIntelligenceService | list[dict] |
| `credit_card_repository.py` | credit_cards | CreditCardService, CreditCardsWorkspaceService, BehaviourWorkspaceService, ForecastService | dict\|None, list[dict] |
| `credit_card_statement_repository.py` | credit_card_statements | CreditCardService, CreditCardsWorkspaceService, NetWorthWorkspaceService | int, dict\|None, list[dict] |
| `financial_event_repository.py` | financial_events, financial_event_lifecycle_log, financial_event_links | FinancialEventsService, FinancialIntelligenceService, TransactionIntelligenceService, CashflowRepository | int, list[dict], bool |
| `financial_goal_repository.py` | financial_goals | FinancialIntelligenceService | str, dict\|None, list[dict], dict |
| `import_mapping_repository.py` | import_mappings | — (UNUSED in services) | int, list[dict] |
| `institution_repository.py` | institutions | AccountService | dict\|None, list[dict], str |
| `investment_repository.py` | investments | InvestmentService, InvestmentsWorkspaceService, NetWorthWorkspaceService, ForecastService | list[dict], list[Investment] |
| `liquidity_pattern_repository.py` | liquidity_provider_patterns, liquidity_purpose_patterns | TransactionIntelligenceService | list[dict], dict\|None, bool |
| `loan_payment_repository.py` | loan_payments | LoanService | int, list[LoanPayment], LoanPayment\|None |
| `loan_repository.py` | loans, loan_prepayments, loan_rate_changes, loan_amortization_schedule | LoanService, LoansWorkspaceService, LoanAnalysisService, LoanSimulationService, BehaviourWorkspaceService, ForecastService, NetWorthWorkspaceService | int, dict\|None, list[Loan] |
| `member_repository.py` | members | MemberService | list[dict], int |
| `networth_repository.py` | (delegates to Account+Investment+Loan+CC repos) | NetWorthService | dict |
| `pattern_repository.py` | behaviour_patterns | BehaviourService, BehaviourWorkspaceService | dict\|None, list[dict] |
| `reconciliation_audit_repository.py` | reconciliation_audit_log | — (UNUSED in services) | int\|None, list[dict] |
| `reconciliation_repository.py` | reconciliations, transactions | ReconciliationService, ReconciliationWorkspaceService, DashboardService | list[Reconciliation], list[dict] |
| `statement_repository.py` | statements, transactions | StatementService, ImportService, TransactionIntelligenceService, DashboardService | list[dict], list[Statement], int |
| `transaction_classification_repository.py` | transaction_classifications, transactions | TransactionIntelligenceService | int, dict\|None, list[int], list[dict] |
| `transaction_repository.py` | transactions, statements, reconciliations | TransactionService, ExportService, DashboardService, BehaviourService, CashflowService, TransactionIntelligenceService, ImportService | list[dict], list[Transaction] |

---

## 7. ENGINE GRAPH

| Engine | Inputs | Outputs | Called By | Depends On |
|---|---|---|---|---|
| `account_engine/` | account_id, balance history | balance metrics, cash flow, dormancy status | AccountService | — (pure calc) |
| `balance_engine.py` | statement data, accounts | running balance, balance validation | StatementService | core.db.connection |
| `behaviour_engine/` | transactions, accounts, loans, CCs | behavioral profile, indices, risk signals, wellness score | BehaviourService, DashboardService, ImportService | insight_generator, nudge_engine |
| `credit_card_engine/` | CC data, statements | outstanding, utilization, EMI conversion, foreclosure amounts | CreditCardService | loan_engine (for foreclosure) |
| `financial_events/` | financial events | lineage walk, revocation detection, rollover scenarios | FinancialEventsService | — (pure calc) |
| `financial_intelligence/` | cashflow, goals, loans, CCs, behaviour | forecasts, optimization plan, intelligence report, priorities | FinancialIntelligenceService | behaviour_engine, loan_engine (via inputs) |
| `loan_engine/` | loan params, payment history | amortization schedules, EMI, foreclosure amounts, metrics | LoanService, LoanSimulationService, LoanAnalysisService | — (pure calc) |
| `recommendation_engine/` | behavioural profile | ranked recommendations with severity | RecommendationService, BehaviourService | — (pure calc) |
| `reconciliation_engine.py` | transactions | potential match pairs | ReconciliationService | core.db.connection |
| `ledger_audit_engine.py` | DB connection | ledger integrity validation, hash verification | AuditService | core.db.connection |
| `nudge_engine.py` | behavioural profile | ranked behavioral nudges | (via behaviour_engine/core) | — (pure calc) |
| `insight_generator.py` | behavioural profile | structured behavioral insights | (via behaviour_engine/core) | — (pure calc) |
| `transaction_intelligence/` | transactions, loans, CCs, accounts | EMI/CC/cash conversion classifications | TransactionIntelligenceService | loan_engine |

**PARKED (Legacy):**
- `behavior_engine.py` → replaced by `behaviour_engine/`
- `cashflow_engine.py.parked` → no active replacement identified

### ASCII Dependency Graph

```
Dashboard Service
      ↓
Behaviour Engine
      ↓
Financial Intelligence
      ↓
Recommendation Engine

Loan Service ──────────────────► Loan Engine
                                    ↓
Credit Card Service ───────────► Credit Card Engine
                                      ↓
                            (depends on loan_engine.foreclosure)

Statement Service ────────────► Balance Engine
                                     ↓
                              (uses core.db.connection)

Import Service
  ├──► Statement Service ───► Balance Engine
  ├──► Transaction Service
  ├──► Behaviour Service ───► Behaviour Engine
  │                            ↓
  │                      Nudge Engine
  │                      Insight Generator
  └──► Statement Processing Orchestrator
        ├──► Behaviour Service
        ├──► Cashflow Service
        ├──► Financial Intelligence Service
        │         ├──► Recommendation Service
        │         └──► Financial Events Service
        ├──► Loan Analysis Service ──► Loan Engine
        ├──► Dashboard Service
        └──► Transaction Intelligence Service
                 └──► Loan Engine (for schedule lookup)

Reconciliation Service ──► Reconciliation Engine
Audit Service ──────────► Ledger Audit Engine
```

---

## 8. EXTRACTION PIPELINE

```
POST /api/upload  (import_router.py)
       ↓
ImportService.upload_statement()
       ├──► [EXTRACTION] StatementExtractor.extract()
       │      ├── detect_bank() → keyword scan pages 0-1
       │      ├── select_best_table() → Camelot lattice/stream scoring
       │      ├── clean_rows() → remove headers/empties
       │      ├── _detect_*_column() → date/description/amount detection
       │      ├── merge_multiline_rows() → continuation grouping
       │      └── normalize_transactions() → structured dicts + amount_paise
       │            fallback: _extract_via_text_fallback (pdfplumber)
       │
       ├──► [HYBRID PATH] HybridExtractor.extract()
       │      └── LayoutAnalyzer.analyze() → geometry-guided extraction
       │
       ├──► [CATEGORIZE] categorizer.categorize(desc, amount)
       │      └── keyword matching → category/subcategory
       │
       ├──► [STORE] StatementRepository.insert_statement() → statements table
       │
       ├──► [STORE] TransactionRepository.insert_transactions() → transactions table (hash dedup)
       │
       ├──► [METADATA] MetadataExtractor.extract() → total_due, card_last4, bill_cycle, etc.
       │
       ├──► [UPDATE META] StatementRepository.update_statement_metadata()
       │
       ├──► [VALIDATE] compare(debits-credits, total_due) → validation_status
       │
       └──► [POST-UPLOAD] StatementProcessingOrchestrator.process_after_upload()
              ├── BehaviourService.compute_financial_profile()
              ├── CashflowService.calculate_summary()
              ├── FinancialIntelligenceService (forecast, optimization, report)
              ├── LoanAnalysisService.analyze_loan_priority()
              ├── DashboardService.get_summary()
              └── TransactionIntelligenceService (EMI/CC/cash classification)

Alternative: ingest.py (CLI batch) mirrors above flow directly.
```

**Extraction Module Files:**

| File | Role |
|---|---|
| `extraction/statement_extractor.py` | Primary PDF→table→transactions (Camelot-based) |
| `extraction/hybrid_extractor.py` | Layout-guided alternative (LayoutAnalyzer + Camelot) |
| `extraction/table_extractor.py` | Simple pdfplumber-table-only (used by main.py tests) |
| `extraction/camelot_extractor.py` | Standalone Camelot wrapper |
| `extraction/column_mapper.py` | Fuzzy column name mapping |
| `extraction/transaction_parser.py` | DataFrame→transaction dict parsing |
| `extraction/categorizer.py` | Keyword-based spending categorization |
| `extraction/metadata_extractor.py` | Bank-specific metadata extraction (regex + proximity) |
| `extraction/csv_importer.py` | CSV/Excel format import |
| `structural/layout_analyzer.py` | PDF structural analysis (geometry, columns, amounts) |
| `orchestration/statement_orchestrator.py` | Post-upload pipeline coordinator |

---

## 9. DTO FLOW

| Request DTO | Service | Mapper | Response DTO |
|---|---|---|---|
| `AccountCreateRequest` | AccountService | AccountMapper | `AccountDTO`, `AccountListResponse` |
| `AccountUpdateRequest` | AccountService | — | `AccountDetailDTO` (inline) |
| `BalanceSnapshotRequest` | AccountService | — | `BalanceSnapshotDTO` |
| `AccountLinkRequest` | AccountService | — | `AccountLinkDTO` |
| `InstitutionCreateRequest` | AccountService | — | `InstitutionDTO` |
| `CreditCardCreateRequest` | CreditCardService | CreditCardMapper | `CreditCardSummaryDTO` |
| `EmiConversionRequest` | CreditCardService | — | `EmiConversionDTO` |
| `ForeclosureRequest` | CreditCardService | — | `ForeclosureDTO` |
| `LoanCreateRequest` | LoanService | LoanMapper | `LoanResponse` |
| `PrepaymentSimulationRequest` | LoanSimulationService | — | `PrepaymentSimulationResponse` |
| `LoanPaymentCreate` | LoanService | — | `PaymentResponse` |
| `InvestmentsDTO` | InvestmentService | InvestmentMapper | `InvestmentsDTO` (self-mapped) |
| `ForecastDTO` | ForecastService | ForecastMapper | `ForecastDTO` |
| `NetWorthDTO` | NetWorthService | — (inline construction) | `NetWorthDTO` |
| `CashflowSummaryDTO` | CashflowService | — (inline) | `CashflowSummaryDTO` |
| `DashboardSummaryDTO` | DashboardService | — (inline) | `DashboardSummaryDTO` |
| `ReconciliationDTO` | ReconciliationService | ReconciliationMapper | `ReconciliationDTO`, `DiscrepancyDTO`, `AuditTrailEntryDTO` |
| `StatementDTO` | StatementService | StatementMapper | `StatementDTO` |

**Wired Mappers:** AccountMapper, CreditCardMapper, InvestmentMapper, ForecastMapper, ReconciliationMapper  
**Orphan Mappers (defined but unused):** NetWorthMapper, AnalyticsMapper, CashflowMapper, BehaviourMapper, LoanMapper, DashboardMapper, StatementMapper, TransactionMapper

---

## 10. DATABASE PIPELINE

```
SQLite (data/finance.db)
    ↓
core/db/connection.py — get_connection() (+context manager)
    ↓
core/db/schema.py — create_all(), run_migrations(), verify_schema()
    ↓
core/db/config.py — get_db_path() (env/override/default cascade)
    ↓
repositories/base.py — BaseRepository._get_conn()
    ↓
All 27 repositories (data access layer)
    ↓
Services orchestrate repositories
    ↓
Engines (pure calc) receive data from repositories as parameters
    ↓
Routers expose HTTP endpoints
```

**Database Tables (31 total):**

| Table | Purpose |
|---|---|
| `statements` | Uploaded bank statements (PDF/CSV) |
| `transactions` | Individual line items (immutable — triggers prevent UPDATE/DELETE) |
| `members` | Household members |
| `accounts` | Bank/savings accounts |
| `account_balance_history` | Daily balance snapshots |
| `account_links` | Inter-account transfer relationships |
| `institutions` | Banks/wallets/brokers metadata |
| `loans` | Loan accounts (principal, rate, tenure) |
| `loan_payments` | Payment records |
| `loan_prepayments` | Extra principal payments |
| `loan_rate_changes` | Interest rate adjustment history |
| `loan_amortization_schedule` | Computed EMI schedules |
| `investments` | Investment holdings |
| `credit_cards` | Credit card accounts |
| `credit_card_statements` | CC statement records |
| `reconciliations` | Matched transaction pairs |
| `reconciliation_audit_log` | Audit trail for reconciliation actions |
| `behaviour_snapshots` | Periodic behaviour profile snapshots |
| `behaviour_patterns` | Detected spending/income patterns |
| `behaviour_alerts` | Behavioral risk/alert notifications |
| `financial_profiles` | Cached personality/profile data |
| `financial_events` | Classified events (EMI, CC payment, cash conversion) |
| `financial_event_lifecycle_log` | Event state transition history |
| `financial_event_links` | Event-to-event relationships |
| `financial_goals` | User-set financial goals |
| `transaction_classifications` | ML-assisted transaction categories |
| `liquidity_provider_patterns` | Income source learning patterns |
| `liquidity_purpose_patterns` | Spending purpose learning patterns |
| `import_mappings` | CSV/Excel field mapping presets |

---

## 11. IMPORT DEPENDENCY SUMMARY

### Top 25 Most Imported Modules

```
 161  typing
 141  src (relative imports)
  42  decimal
  36  pydantic
  32  datetime
  31  fastapi
  18  logging
  15  collections
  14  pathlib
  14  time
  11  re
  10  json
   9  sys
   7  sqlite3
   7  contextlib
   6  pdfplumber
   6  math
   4  dataclasses
   3  os
   3  pandas
   3  camelot
   2  traceback
   2  engines
   2  cachetools
```

### Top 25 Largest Dependency Hubs

```
   9  extraction.csv_importer
   8  extraction.hybrid_extractor
   8  extraction.metadata_extractor
   8  extraction.statement_extractor
   7  ingest
   7  core.db.schema
   6  db
   6  structural.layout_analyzer
   6  routers.behaviour
   6  extraction.camelot_extractor
   6  engines.behaviour_engine.core
   5  logger
   5  routers.reconciliation_workspace
   5  routers.cashflow_workspace
   5  routers.loans_workspace
   5  routers.investments_workspace
   5  routers.loans
   5  routers.import_router
   5  routers.credit_cards
   5  routers.credit_cards_workspace
   5  routers.financial_intelligence
   5  routers.accounts
   5  routers.cards_statements
   5  routers.behaviour_workspace
   5  routers.networth_workspace
```

### Most Depended-On Services

```
FinancialIntelligenceService (imported by financial_intelligence router, 5 cross-services)
BehaviourService (imported by behaviour router, import_service, financial_intelligence_service)
ImportService (imported by import_router)
TransactionService (imported by transactions router, import_service)
CashflowService (imported by cashflow router, cashflow_workspace_service, financial_intelligence_service)
```

### Most Depended-On Repositories

```
TransactionRepository — 8 consumers
LoanRepository — 7 consumers
AccountRepository — 5 consumers
CreditCardRepository — 4 consumers
FinancialEventRepository — 4 consumers
StatementRepository — 4 consumers
ReconciliationRepository — 3 consumers
InvestmentRepository — 4 consumers
```

### Most Depended-On Engines

```
behaviour_engine.core — 3 consumers (behaviour_service, dashboard_service, import_service)
loan_engine — 4 consumers (loan_service, loan_simulation, loan_analysis, transaction_intelligence)
credit_card_engine — 1 consumer (credit_card_service)
account_engine — 1 consumer (account_service)
financial_intelligence — 1 consumer (financial_intelligence_service)
transaction_intelligence — 1 consumer (transaction_intelligence_service)
recommendation_engine — 2 consumers (recommendation_service, behaviour_service)
```

---

## 12. DUPLICATE MATRIX

| Old | New | Actual Usage | Recommendation |
|---|---|---|---|
| `engines/behavior_engine.py` (978L) | `engines/behaviour_engine/` | behaviour_engine is canonical; behavior_engine is parked | VERIFY |
| `engines/cashflow_engine.py.parked` | No direct replacement found | Parked; cashflow logic lives in services directly | COMPATIBILITY |
| `common/database.py` (32L) | `src.core.db.*` | Zero production consumers; explicitly deprecated | VERIFY |
| `db.py` (FinanceDB) | `core/db/schema.py` + `core/db/connection.py` | Backward-compatible wrapper still imported by common/database | COMPATIBILITY |
| `services/base_service.py` (3L) | `services/base.py` | Single-line re-export shim | VERIFY |
| `routers/health.py` (6L) | `src/health.py` | Trivial re-export shim | VERIFY |
| `behaviour.py` (full router) | `behaviour_workspace.py` | Both active; different prefixes (/api vs /api/v1) | COMPATIBILITY |
| `cashflow.py` (full router) | `cashflow_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `credit_cards.py` (full router) | `credit_cards_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `investments.py` (full router) | `investments_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `loans.py` (full router) | `loans_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `networth.py` (full router) | `networth_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `reconciliation.py` (full router) | `reconciliation_workspace.py` | Both active; different prefixes | COMPATIBILITY |
| `behaviour_service.py` (1048L) | `behaviour_workspace_service.py` (163L) | Full vs workspace variant; both actively used | COMPATIBILITY |
| `cashflow_service.py` | `cashflow_workspace_service.py` | Full vs workspace variant; both actively used | COMPATIBILITY |
| `credit_card_service.py` | `credit_cards_workspace_service.py` | Full vs workspace variant; both actively used | COMPATIBILITY |
| `investment_service.py` | `investments_workspace_service.py` | Full vs workspace variant; both actively used | COMPATIBILITY |
| `loan_service.py` (430L) | `loans_workspace_service.py` (177L) | Full vs workspace variant; both actively used | COMPATIBILITY |
| `networth_service.py` | `networth_workspace_service.py` (252L) | Full vs workspace variant; both actively used | COMPATIBILITY |
| `reconciliation_service.py` | `reconciliation_workspace_service.py` | Full vs workspace variant; both actively used | COMPATIBILITY |
| Orphan mappers (8) | Not wired to any service/router | NetWorthMapper, AnalyticsMapper, CashflowMapper, BehaviourMapper, LoanMapper, DashboardMapper, StatementMapper, TransactionMapper | VERIFY |
| Unused repos (3) | alert_repository, reconciliation_audit_repository, import_mapping_repository | Defined but no service imports them | VERIFY |

---

## 13. PLACEHOLDER FOLDER MATRIX

| Path | Lines | Content | Assessment |
|---|---|---|---|
| `utils/__init__.py` | 0 | Empty | UNUSED — placeholder directory |
| `structural/__init__.py` | 0 | Empty | UNUSED — placeholder (has layout_analyzer.py) |
| `orchestration/__init__.py` | 0 | Empty | UNUSED — placeholder (has statement_orchestrator.py) |
| `data/__init__.py` | 0 | Empty | UNUSED — placeholder (has finance.db + uploads/) |
| `engines/__init__.py` | 16 | Imports sub-modules | CANONICAL — engine package init |
| `core/mappers/__init__.py` | 19 | Re-exports 3 mappers only | PARTIAL — exports incomplete (only 3 of 13) |
| `core/domain/__init__.py` | 17 | Imports domain types | CANONICAL — Money value object |
| `core/dtos/__init__.py` | (all) | Re-exports all DTOs | CANONICAL — DTO registry |
| `services/base_service.py` | 3 | `from .base import BaseService` | COMPATIBILITY — trivial re-export |
| `routers/health.py` | 6 | `from src.health import ...` | COMPATIBILITY — trivial re-export |
| `common/database.py` | 32 | Deprecated shim | COMPATIBILITY — zero consumers |

---

## 14. MAJOR FINDINGS

1. The backend uses a three-layer architecture (Routers → Services → Repositories) with a parallel engine layer for pure computation.
2. There are 28 routers serving two API version families simultaneously: `/api` (original) and `/api/v1` (workspace variants).
3. Seven full workspace router/service pairs exist alongside their originals, both actively registered and functional.
4. The `behaviour_engine/` package replaced the parked `behavior_engine.py` (US spelling legacy) but both spellings persist in function names across modules.
5. Eight mappers in `core/mappers/` are defined but never imported by any service or router — they are dead code.
6. Three repositories (`alert_repository`, `reconciliation_audit_repository`, `import_mapping_repository`) are defined but have zero service consumers.
7. The `common/database.py` module is explicitly deprecated with zero production consumers and should be removed.
8. The `cashflow_engine.py.parked` file has no active counterpart identified; cashflow computation exists directly in `CashflowService`.
9. FinancialIntelligenceService is the heaviest cross-dependency orchestrator, importing five other services directly.
10. ImportService is the only service that bridges the extraction pipeline to the post-upload orchestration layer.
11. The `transactions` table has two triggers preventing UPDATE and DELETE, enforcing immutability.
12. All monetary values use integer paise (no floating-point), parsed through `_parse_amount_paise()` in schema.py and common/calculations.py.
13. The `bank_repository.py` queries a `banks` table that does not exist in the schema — it falls back to querying `statements.bank`.
14. Two database access paths exist: the canonical `core.db.connection.get_connection()` and the deprecated `common.database.get_db()` returning `FinanceDB`.
15. Workspace services are significantly smaller wrappers (163–252 lines) compared to full services (430–1048 lines), suggesting an API versioning strategy rather than a feature split.
16. The extraction pipeline has two parallel strategies: `StatementExtractor` (Camelot-based) and `HybridExtractor` (LayoutAnalyzer-guided), with pdfplumber as text fallback.
17. `core/mappers/__init__.py` only re-exports 3 of 13 mappers, making half the mapper package inaccessible via the public import path.
18. Four `__init__.py` files across `utils/`, `structural/`, `orchestration/`, and `data/` are completely empty, indicating abandoned or planned-but-unfilled modules.
19. The `nudge_engine.py` and `insight_generator.py` are standalone modules consumed indirectly through `behaviour_engine/core`, not called directly by any router or service.
20. The `financial_intelligence.py` router prefix is `/financial-intelligence` (no `/api` prefix), unlike all other routers, representing an inconsistent naming convention.
