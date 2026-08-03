# System Architecture Map

---

## 1. System Layer Diagram
```
Browser
  │
  ▼
Next.js (App Router, SSR)
  │
  ▼
App Shell (OS-shell layer)
  │   LeftRail | TopCommandBar | WorkspaceContainer | RightInspector | BottomTimeline | StatusBar
  │
  ▼
Workspace Runtime (workspace-context.ts)
  │
  ▼
Page-Level Capability Hooks (useDashboardMetrics, useCashflowCapability, etc.)
  │
  ▼
React Query (TanStack) + Zod Schemas + Mappers
  │
  ▼
API Client (lib/api/client.ts)
  │
  ▼
FastAPI (backend/src/api.py)
  │
  ▼
Routers (src/routers/*.py) → Services (src/services/*.py) → Repositories (src/repositories/*.py)
  │
  ▼
Engines (src/engines/)
  │
  ▼
Core Domain (src/core/)
  │
  ▼
SQLite (backend/src/data/finance.db)
```

---

## 2. Folder Ownership Table
| Folder | Purpose | Owner |
|---|---|---|
| `backend/src/api.py` | FastAPI app factory | Architecture |
| `backend/src/routers/` | HTTP route handlers | API Layer |
| `backend/src/services/` | Business orchestration | Service Layer |
| `backend/src/repositories/` | SQLite read/write | Data Access |
| `backend/src/engines/` | Pure computation | Computation |
| `backend/src/extraction/` | PDF/CSV extraction | Ingestion |
| `backend/src/core/` | Domain models, DTOs, DB | Core |
| `frontend/app/` | Next.js App Router pages | UI |
| `frontend/lib/capabilities/` | Workspace orchestration hooks | UI Logic |
| `frontend/lib/workspace/` | Workspace context provider | UI Runtime |
| `frontend/lib/mappers/` | API → ViewModel mapping | Data Layer |
| `frontend/lib/schemas/` | Zod validation | Data Layer |

---

## 3. Router → Service Matrix
| Router | Service | Endpoints |
|---|---|---|
| `accounts.py` | `AccountService` | `/api/accounts` |
| `behaviour.py` | `BehaviourService` | `/api/behaviour` |
| `cashflow.py` | `CashflowService` | `/api/cashflow` |
| `credit_cards.py` | `CreditCardService` | `/api/credit-cards` |
| `dashboard.py` | `DashboardService` | `/api/dashboard` |
| `forecast.py` | `ForecastService` | `/api/forecast` |
| `investments.py` | `InvestmentService` | `/api/investments` |
| `loans.py` | `LoanService` | `/api/loans` |
| `networth.py` | `NetWorthService` | `/api/networth` |
| `reconciliation.py` | `ReconciliationService` | `/api/reconciliations` |
| `transactions.py` | `TransactionService` | `/api/transactions` |
| `import_router.py` | `ImportService` | `/api/upload`, `/api/import` |

---

## 4. Service → Repository Matrix
| Service | Repository | Key Methods |
|---|---|---|
| `AccountService` | `AccountRepository` | `get_accounts`, `get_account_balance_history` |
| `BehaviourService` | `BehaviourRepository` | `get_profile`, `get_wellness_score` |
| `CashflowService` | `CashflowRepository` | `get_monthly_cashflow`, `get_category_spend` |
| `CreditCardService` | `CreditCardRepository` | `get_cards`, `get_statements` |
| `DashboardService` | `TransactionRepository` | `get_recent_transactions`, `get_summary` |
| `ForecastService` | `LoanRepository`, `InvestmentRepository` | `get_loans`, `get_investments` |
| `InvestmentService` | `InvestmentRepository` | `get_investments`, `get_performance` |
| `LoanService` | `LoanRepository` | `get_loans`, `get_amortization_schedule` |
| `NetWorthService` | `NetWorthRepository` | `get_net_worth` |
| `ReconciliationService` | `ReconciliationRepository` | `get_pending_reconciliations` |
| `TransactionService` | `TransactionRepository` | `get_transactions`, `get_transaction` |
| `ImportService` | `StatementRepository`, `TransactionRepository` | `insert_statement`, `insert_transactions` |

---

## 5. Service → Engine Matrix
| Service | Engine | Key Methods |
|---|---|---|
| `AccountService` | `account_engine` | `calculate_metrics`, `validate_balance` |
| `BehaviourService` | `behaviour_engine` | `calculate_profile`, `generate_insights` |
| `CreditCardService` | `credit_card_engine` | `calculate_utilization`, `generate_statement_summary` |
| `LoanService` | `loan_engine` | `calculate_amortization`, `simulate_prepayment` |
| `ForecastService` | `financial_intelligence` | `generate_forecast`, `optimize_goals` |
| `ReconciliationService` | `reconciliation_engine` | `match_transactions`, `validate_matches` |
| `TransactionService` | `transaction_intelligence` | `classify_transaction`, `detect_emi_payments` |

---

## 6. Extraction Pipeline
```
User Upload (PDF/CSV)
  │
  ▼
ImportService
  ├── StatementExtractor (PDF)
  ├── CSVImporter (CSV)
  ├── ColumnMapper (header mapping)
  ├── TransactionParser (row parsing)
  ├── MetadataExtractor (bank/card details)
  ├── Categorizer (keyword-based categorization)
  └── Validation (balance_engine.validate_statement_balance)
  │
  ▼
StatementRepository.insert()
TransactionRepository.insert_transactions()
  │
  ▼
StatementProcessingOrchestrator (post-upload recalculations)
```

---

## 7. DTO Pipeline
```
SQLite (INTEGER paise)
  │
  ▼
Repository (dict with _paise int)
  │
  ▼
DTO (Pydantic: balance_paise: int)
  │
  ▼
API Response (JSON: { "balance_paise": 1000000 })
  │
  ▼
Frontend fetch() + Zod parse (z.number().int())
  │
  ▼
ViewModel (TypeScript: balance_paise: number)
  │
  ▼
formatINR(paise) → "₹10,000.00"
```

---

## 8. Database Pipeline
```
SQLite Schema (core/db/schema.py)
  │
  ▼
Repositories (src/repositories/*.py)
  │
  ▼
Services (src/services/*.py)
  │
  ▼
Engines (src/engines/)
  │
  ▼
DTOs (src/core/dtos/)
```

---

## 9. Import Dependency Summary
| Stage | Module | Dependencies |
|---|---|---|
| Detection | `StatementExtractor` | `pdfplumber`, `camelot` |
| CSV Import | `CSVImporter` | `pandas` |
| Column Mapping | `ColumnMapper` | `config/column_mappings.json` |
| Row Parsing | `TransactionParser` | `dateutil`, `Money` |
| Categorization | `Categorizer` | `config/categories.json` |
| Validation | `balance_engine` | `Money` |
| Persistence | `StatementRepository`, `TransactionRepository` | `core/db/connection.py` |
| Orchestration | `StatementProcessingOrchestrator` | All services |

---

## 10. Duplicate Matrix
| Candidate Pair | Verdict | Rationale |
|---|---|---|
| `engines/behavior_engine.py` vs `engines/behaviour_engine/` | **Compatibility** | `behavior_engine.py` is PARKED (legacy bridge) |
| `dtos/account_dto.py` vs `dtos/accounts_dto.py` | **Investigate** | `account_dto.py` (singular) vs `accounts_dto.py` (plural) |
| `services/base.py` vs `services/base_service.py` | **Compatibility** | `base_service.py` re-exports `base.py` |
| `lib/parser/extractors/metadata-extractor.ts` vs `lib/parser/metadata-extractor.ts` | **Duplicate** | Two implementations of the same extractor |

---

## 11. Placeholder Folder Matrix
| Folder | Status | Action |
|---|---|---|
| `backend/src/structural/` | **Experimental** | Investigate usage |
| `backend/src/utils/` | **Deprecated** | Empty `__init__.py` (delete) |
| `frontend/lib/formatters/` | **Deprecated** | Replaced by `lib/utils/format.ts` |
| `frontend/lib/hooks/` | **Compatibility** | Partial overlap with `capabilities/` |

---

## 12. Major Findings
1. **Money Pipeline**: All monetary values use `_paise` INTEGER columns. No FLOAT money fields.
2. **Workspace Runtime**: Centralized `workspace-context.ts` enables cross-workspace state sharing.
3. **Extraction Pipeline**: Hybrid PDF/CSV extraction with fallback mechanisms.
4. **Compatibility Layers**: Multiple deprecated files (e.g., `behavior_engine.py`, `base_service.py`) remain for backward compatibility.
5. **Duplicate Implementations**: Two metadata extractors (`metadata-extractor.ts`) and DTOs (`account_dto.py` vs `accounts_dto.py`).
6. **Placeholder Folders**: `backend/src/structural/` and `backend/src/utils/` are unused or experimental.