# ClariFin_OS — Architecture Map

## Topology

```
ClariFin_OS/                          # Monorepo root
├── backend/          (Python 3.12)   # FastAPI + SQLite (no ORM)
│   ├── 182 .py files
│   ├── venv/ + requirements.txt
│   └── src/ (9 layers)
│
├── frontend/         (Next.js 16)    # React 19 + shadcn/ui
│   ├── 73 .ts/.tsx files
│   ├── App Router (9 routes)
│   └── OpenAPI types via openapi-typescript
│
├── servers/          (MCP)           # Standalone npm MCP servers
├── docs/                             # Architecture ADRs, product audits
├── memory-bank/                      # AI session persistence (activeContext.md, projectbrief.md)
└── .clinerules                       # AI operational rules
```

## Communication Flow

```
Browser → Next.js (port 3000) ──HTTP──→ FastAPI (port 8000) ──sqlite3──→ data/finance.db
         ↑                                    ↑
         └── types/api-generated.ts ←── /openapi.json
```

---

## 1. Backend Architecture (Python FastAPI)

### Layer Hierarchy

```
Router (HTTP) ─→ Service (orchestration) ─→ Engine (pure logic) ─→ Repository (SQL) ─→ SQLite
    20 files         15 files                   10+ files                 24 files            1 db
```

### Layer Details

**Entry Point:** `backend/src/api.py` — FastAPI app, CORS, 21 routers registered

**Routers** (`src/routers/`, 24 files): `accounts`, `audit`, `banks`, `behavior`, `behaviour` (duplicate), `cards_statements`, `cashflow`, `credit_cards`, `dashboard`, `export`, `financial_intelligence`, `goals`, `import_router`, `investments`, `loans`, `managed_accounts`, `members`, `networth`, `patterns`, `reconciliation`, `scenarios`, `transactions`, `health`

**Services** (`src/services/`, 17 files): `AccountService`, `AuditService(BaseService)`, `BehaviorService(BaseService)`, `BehaviourService`, `CashflowService`, `CreditCardService`, `DashboardService(BaseService)`, `FinancialIntelligenceService`, `LoanAnalysisService`, `LoanService`, `LoanSimulationService`, `NetWorthService(BaseService)`, `ReconciliationService(BaseService)`, `StatementService(BaseService)`, `TransactionIntelligenceService`

**Engines** (`src/engines/`, 12+ packages):
- `reconciliation_engine.py` — Hungarian algorithm bipartite matching
- `balance_engine.py` — Running balance computation
- `cashflow_engine.py` — Monthly cashflow analysis with financial events
- `behavior_engine.py` (legacy) + `behaviour_engine/` (new)
- `loan_engine/` — Amortization schedules, reducing balance
- `credit_card_engine/` — Outstanding/interest calculations
- `account_engine/` — Account operations
- `transaction_intelligence/` — EMI detection, CC payment detection, cash conversion detection
- `financial_intelligence/` — Cashflow, liquidity, credit forecasting + goal planning (Phase 9.1/9.2)

**Repository Rule (enforced):** Only files under `src/repositories/` may import FinanceDB. 25 repositories all extend `BaseRepository` which provides `_get_conn()` → sqlite3.Connection.

**Repositories** (`src/repositories/`, 26 files): `AccountBalanceRepository`, `AccountLinkRepository`, `AccountRepository`, `AlertRepository`, `BankRepository`, `BehaviourRepository`, `CashflowRepository`, `CreditCardRepository`, `CreditCardStatementRepository`, `FinancialEventRepository`, `FinancialGoalRepository`, `ImportMappingRepository`, `InstitutionRepository`, `InvestmentRepository`, `LiquidityPatternRepository`, `LoanPaymentRepository`, `LoanRepository`, `MemberRepository`, `NetWorthRepository`, `PatternRepository`, `ReconciliationAuditRepository`, `ReconciliationRepository`, `StatementRepository`, `TransactionClassificationRepository`, `TransactionRepository`

**Models** (`src/models/`, 19 files): All extend `DomainModel(BaseModel)` with `from_db_row()` classmethods. Key models: `Account`, `CreditCard`, `CreditCardStatement`, `DashboardSummary`, `FinancialEvent`, `Institution`, `Investment`, `Loan`, `LoanPayment`, `Reconciliation`, `Statement`, `Transaction`, `BehaviourSnapshotCreate`

**Database:** SQLite via `FinanceDB` class in `db.py`. Schemas: `statements`, `transactions` (with hash_signature immutability triggers), `accounts`, `loans`, `loan_payments`, `loan_prepayments`, `loan_rate_changes`, `investments`, `members`, `import_mappings`, `reconciliations`, `reconciliation_audit_log`, `loan_amortization_schedule`, `transaction_classifications`, `liquidity_provider_patterns`, `liquidity_purpose_patterns`, `financial_events`, `financial_event_links`, `financial_goals`

**Financial Rule:** All monetary values stored as INTEGER paise (₹1 = 100 paise). Use `_parse_amount_paise()` for conversion. NEVER float for currency.

### Key Classes (Root Layer, 9 files)

| Class | File | Purpose |
|-------|------|---------|
| `FinanceDB` | `db.py` | SQLite manager, schema creation, migrations |
| `Settings` | `config.py` | Env-based config (DB path, CORS, ports, feature flags) |
| `ColumnMapper` | `column_mapper.py` | Map bank columns to standard fields |
| `CSVImporter` | `csv_importer.py` | CSV/Excel import with auto-detect |
| `TableExtractor` | `table_extractor.py` | PDF table extraction |
| `TransactionParser` | `transaction_parser.py` | Parse rows to transactions |
| `MetadataExtractor` | `metadata_extractor.py` | Extract PDF metadata |
| `StatementExtractor` | `statement_extractor.py` | Bank statement PDF extraction |
| `AppError` tree | `errors.py` | 6 error types (Validation, Database, File, Import, NotFound, generic) |

---

## 2. Frontend Architecture (Next.js 16 + React 19)

### Route Map

```
/ → redirect(/dashboard)
/dashboard          → DashboardPage (useDashboardMetrics, useOverview)
/accounts           → Account management
/cards              → Credit cards
/investments        → Investments
/loans              → Loan management
/reconciliation     → Transaction reconciliation
/transactions       → Transaction listing
/settings           → User settings
```

### Component Architecture

```
app/layout.tsx → ThemeProvider → QueryProvider → MemberProvider → ErrorBoundary → MainLayout
                                                                                      ↕
                                                                               {children} (page)
```

**Key Dashboard Components:** `DashboardSkeleton`, `CashflowChart`, `CategorySpendChart`, `BehaviorScoreCard`, `InsightsPanel`, `AnalyticsSummaryBar`, `RecurringChargesWidget`, `TopMerchantsWidget`, `RecentTransactions`

**Libraries:** TanStack React Query, Zustand (state), Zod (validation), date-fns, recharts, lucide-react, radix-ui, shadcn/ui

**Type Safety:** OpenAPI-generated types in `types/api-generated.ts` from `http://localhost:8000/openapi.json`

---

## 3. Key Code Relationships

### Dependency Chain (Critical Path)

```
API Request
  → Router (validates HTTP params)
    → Service (orchestrates business logic)
      → Engine (pure computation, NO DB calls)
      → Repository (SQL access, inherits BaseRepository)
        → FinanceDB._get_conn() → sqlite3.Connection
          → data/finance.db
```

### Known Duplicate Code (Technical Debt)

| Component | Duplicate | Status |
|-----------|-----------|--------|
| `routers/behavior.py` | `routers/behaviour.py` | US/UK spelling (LIVE vs UK-only) |
| `services/behavior_service.py` | `services/behaviour_service.py` | Legacy wrapper → canonical implementation |
| `engines/behavior_engine.py` | `engines/behaviour_engine/` | Deprecated (warning added) vs canonical module |
| `errors.py` | Inline error handling in some routers | Inconsistent patterns |

### Engine Purity Issue

Some engines (`reconciliation_engine.py`, `behavior_engine.py`) still call `sqlite3.connect()` directly instead of accepting data via parameters. This violates the Repository Boundary Rule.

---

## 4. Database Schema Summary

| Table | Key Columns | Relationships |
|-------|-------------|---------------|
| `statements` | id, bank, card_last4, total_amount_due, payment_due_date, source | PK for transactions |
| `transactions` | id, statement_id, date, description, amount_paise, type, category, hash_signature | FK→statements, immutable (triggers) |
| `accounts` | id, name, bank, balance_paise, account_number_last4 | |
| `loans` | id, name, lender, principal_paise, outstanding_paise, interest_rate (REAL) | |
| `reconciliations` | id, debit_txn_id, credit_txn_id, amount_paise, confidence_bps, deterministic_key | FK→transactions(x2) |
| `reconciliation_audit_log` | id, reconciliation_id, action, changed_fields | FK→reconciliations |
| `loan_amortization_schedule` | id, loan_id, due_date, principal_paise, interest_paise | UNIQUE(loan_id, due_date) |
| `transaction_classifications` | id, transaction_id, classification | UNIQUE(transaction_id, classification) |
| `liquidity_provider_patterns` | id, provider_name, regex_pattern, fee_range_bps | |
| `members` | id, name, color | |
| `import_mappings` | id, mapping_name, date_column, description_column, amount_column | |
| `financial_events` | id, event_type, amount_paise, date_iso, month_bucket, account_id, lifecycle_state, outstanding_paise, confidence_bps | New Phase 6 table |
| `financial_event_links` | id, event_id, linked_event_id, link_type | settles/funds/rolls_over relationships |
| `financial_goals` | id, household_id, goal_type, name, target_amount_paise, current_amount_paise, target_date, priority, status | Phase 9.2 table |

---

## 5. Validation Pipelines

- **Frontend:** `npm run type-check` (tsc --noEmit) + `npm run lint` (eslint) + `npm test` (vitest) + `npm run build` (next build)
- **Backend:** `./venv/bin/python3 -m ruff check .` + `./venv/bin/python3 -m mypy .`
- **Monetary:** All amounts INTEGER paise, never float. `_parse_amount_paise()` converts safely.
- **API Contract:** OpenAPI schema → `openapi-typescript` generates `types/api-generated.ts`

---

## 6. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python | 3.12 |
| Backend Framework | FastAPI | 0.115.0 |
| Backend Testing | pytest | 8.3.0 |
| Backend Linting | ruff + mypy (strict) | latest |
| Database | SQLite (no ORM) | WAL mode, FK ON |
| Frontend | Next.js | 16.1.6 |
| UI Library | React | 19.2.3 |
| Styling | Tailwind CSS | v4 |
| Components | shadcn/ui (Radix) | |
| State | Zustand | 5.0.11 |
| Data Fetching | TanStack React Query | 5.101.2 |
| Frontend Testing | Vitest + Playwright | latest |
| Validation (FE) | Zod | 4.4.3 |
| API Types | openapi-typescript | 7.13.0 |

---

## 7. Quick Reference (for AI Context Optimization)

### To find a class definition:
```bash
rg "class (ClassName)" --type py
# Or use CGC: find_code("ClassName")
```

### To find all functions in a module:
```bash
rg "^def " backend/src/engines/reconciliation_engine.py
```

### To trace an endpoint:
```bash
rg "def (endpoint_name)" --type py backend/src/routers/
```

### To check imports of a symbol:
```bash
rg "from.*import.*FinanceDB" --type py
```

### To list all API routes:
```bash
rg "^@router\." --type py backend/src/routers/
```

### Token Budget Rules:
- Small fix (<5 files): Read only affected files + their tests
- Feature addition: Read router → service → engine → repository chain (4 files max)
- Bug investigation: Read router + service + repository (3 files max) + test files
- Architecture question: Use CGC queries, read only the layer files needed