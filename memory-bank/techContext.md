# Technical Context

## Technology Stack

### Core Stack
| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend Framework | Next.js 16.1.6 (App Router) | React-based SSR/SPA |
| Language | TypeScript (strict mode) | Type-safe frontend development |
| Styling | Tailwind CSS | Utility-first CSS |
| UI Components | shadcn/ui | Accessible, composable components |
| State Management | Zustand | Lightweight client state |
| Server State | React Query (TanStack Query) | API data fetching and caching |
| Charts | Recharts, Chart.js | Data visualization |
| PDF Parsing (client) | pdfjs-dist | Client-side PDF text extraction |
| Backend Framework | FastAPI | REST API |
| Database | SQLite (raw, no ORM) | Local persistent storage |
| PDF Parsing (server) | pdfplumber | Server-side PDF extraction |
| E2E Testing | Playwright | Browser automation tests |
| Unit Testing | pytest | Python test suite |

### Deprecated
- **Reflex Dashboard**: Archived to `backend/_archived_reflex_dashboard/`

---

## Repository Structure

```
ClariFin_OS/
├── frontend/                    # Next.js application
│   ├── app/                     # App Router pages
│   │   ├── dashboard/           # Dashboard views
│   │   ├── transactions/        # Transaction list/filter
│   │   ├── accounts/            # Account management
│   │   ├── cards/               # Card management
│   │   ├── settings/            # Application settings
│   │   └── test/                # Test pages [REMOVED]
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui primitives
│   │   ├── dashboard/           # Dashboard widgets (cashflow-chart, dashboard-skeleton, recent-transactions)
│   │   ├── cards/               # Card components
│   │   ├── import/              # Import workflow
│   │   ├── layout/              # Layout components
│   │   ├── members/             # Member management
│   │   ├── onboarding/          # Onboarding flow
│   │   └── upload/              # Upload components
│   ├── hooks/                   # React hooks (React Query + custom)
│   ├── types/                   # TypeScript type definitions
│   ├── lib/                     # API client, parser, utilities
│   ├── mocks/                   # MSW handlers and fixtures
│   │   ├── handlers/            # API route handlers (accounts.ts added)
│   │   └── fixtures/            # Mock data (accounts.ts added)
│   └── tests/                   # Playwright E2E tests
├── backend/                     # FastAPI + SQLite
│   ├── src/                     # Application code
│   │   ├── api.py               # Monolithic FastAPI (1805 lines, 28 routes)
│   │   ├── db.py                # Database operations (49KB, 1290+ lines)
│   │   ├── categorizer.py       # Transaction categorization
│   │   ├── csv_importer.py      # CSV/Excel import
│   │   ├── engines/             # Deterministic computation engines
│   │   │   ├── balance_engine.py       # Account balance computation
│   │   │   ├── behavior_engine.py      # 5 behavioral indices + health score
│   │   │   ├── insight_generator.py    # Evidence-based insights
│   │   │   ├── ledger_audit_engine.py  # Hash verification, integrity
│   │   │   ├── nudge_engine.py         # Rules-based financial suggestions
│   │   │   └── reconciliation_engine.py # Confidence-based matching
│   │   ├── core/                # Domain models (UNUSED — not wired)
│   │   │   ├── domain/          # money.py, __init__.py
│   │   │   ├── dtos/            # account_dto, analytics_dto, dashboard_dto, etc.
│   │   │   └── mappers/         # account_mapper, analytics_mapper, etc.
│   │   ├── extraction/          # PDF extraction (UNUSED — not wired)
│   │   │   ├── camelot_extractor.py
│   │   │   └── hybrid_extractor.py
│   │   ├── app/                 # EMPTY — no .py files
│   │   ├── audits/              # EMPTY — no .py files
│   │   ├── db/                  # EMPTY — no .py files
│   │   ├── parsers/             # EMPTY — no .py files
│   │   ├── reports/             # EMPTY — no .py files
│   │   ├── routers/             # EMPTY — no .py files
│   │   └── utils/               # EMPTY — no .py files
│   ├── tests/                   # Python test suite (5 tests)
│   └── data/                    # Database + uploads
├── memory-bank/                 # Cline context (project documentation)
├── servers/                     # MCP server implementations
├── Audit_Report.md              # Append-only audit findings
└── README.md                    # Project overview
```

---

## Backend Architecture

### FastAPI Application
- **Monolithic**: Single `api.py` (1805 lines) with 28 routes
- CORS configured for origins: `localhost:3000`, `localhost:3001`
- Raw SQLite3 (no ORM) with inline DDL
- Database file: `backend/data/finance.db`

### DB Schema (5 tables)
| Table | Purpose | Key Fields |
|-------|---------|------------|
| `statements` | Uploaded PDF metadata | bank, card_last4, period, file_name |
| `transactions` | Individual transactions | statement_id, date, description, amount, type, category |
| `members` | Multi-user support | name, color |
| `import_mappings` | CSV import configs | column mappings, date format, skip rows |
| `reconciliations` | Transfer matching | debit_txn_id, credit_txn_id, amount, match_confidence, status |

**Missing tables**: `loans`, `investments`, `accounts` (accounts are computed dynamically)

### Engine Architecture
Each engine is a deterministic computation module:
- **balance_engine.py**: Account balance computation, running balance history, statement validation
- **behavior_engine.py**: 5 behavioral indices (savings_discipline, habit_stability, impulsivity, financial_stress, loss_aversion) + financial health score + India-specific risk patterns (UPI micro, gambling, loan app patterns, EMI ratio)
- **insight_generator.py**: Evidence-based financial insights in natural language
- **ledger_audit_engine.py**: Hash verification, integrity validation, full audit report
- **nudge_engine.py**: Rules-based financial suggestions with prioritization
- **reconciliation_engine.py**: Confidence-based transaction matching with fuzzy description matching

### Ledger Integrity
- Append-only transaction storage
- Hash signature unique index prevents duplicates
- ISO date ordering ensures correct chronological replay
- Database-level trigger enforcement against mutation

### api.py Internal Module Imports
```
api.py imports:
  ├── config.settings                   → DB path, CORS, upload dir
  ├── logger.(log_info, log_error)      → Logging
  ├── errors.*                          → Error registration and types
  ├── db.FinanceDB                      → ALL database operations
  ├── categorizer.categorize            → Transaction categorization
  ├── statement_extractor.StatementExtractor → PDF parsing
  ├── metadata_extractor.MetadataExtractor     → PDF metadata
  ├── csv_importer.CSVImporter          → CSV/Excel import
  ├── engines.balance_engine.*          → Balance computation
  ├── engines.reconciliation_engine.*   → Transfer matching
  ├── engines.ledger_audit_engine.*     → Ledger integrity
  ├── engines.behavior_engine.*         → Behavioral scoring
  ├── engines.insight_generator.*       → Text insights
  └── engines.nudge_engine.*            → Nudge generation
```

**NOT imported by api.py (exists but unused):**
- `extraction.camelot_extractor` — on disk, not wired
- `extraction.hybrid_extractor` — on disk, not wired
- `structural.layout_analyzer` — on disk, not wired
- `core/` DTOs and mappers — on disk, not wired
- All empty directories: `app/`, `audits/`, `db/`, `parsers/`, `reports/`, `routers/`, `utils/`

---

## Frontend Architecture

### App Router Pages (6 routes)
- `/` — Redirects to /dashboard
- `/dashboard` — Financial dashboard with key metrics, cashflow chart, recent transactions
- `/transactions` — Transaction list with filtering and search
- `/accounts` — Account management (CRUD via API)
- `/cards` — Card/statement management
- `/settings` — Application settings (member management)

### Data Fetching
- React Query (TanStack Query) for server state — canonical
- Zustand for local UI state (theme, mode preference)
- MSW (Mock Service Worker) for API mocking in tests
- Contract tests with vitest (8 test files, 38 tests passing)

### Component Architecture
- Dashboard components: cashflow-chart, dashboard-skeleton, recent-transactions (3 components)
- Removed unused: insight-cards, quick-stats, spending-overview, widget-error-fallback
- Business components: ~25 across cards, import, layout, members, onboarding, upload
- shadcn/ui primitives: 22 components

### MSW Mock Structure
- handlers/: accounts, banks, cashflow, categories, dashboard, index, overview, statements, transactions
- fixtures/: accounts (NEW), dashboard, overview, transactions

---

## SQLite Architecture

- Raw SQLite3 driver (no ORM, no SQLAlchemy)
- Inline DDL in `db.py`
- Append-only transaction table with hash-based deduplication
- Immutability triggers at database level
- Deterministic keys for idempotent inserts

---

## API Architecture

- RESTful FastAPI application (28 routes)
- CORS configured for local development
- Endpoints organized by domain: transactions, overview, analytics, statements, accounts, reconciliation, audit, behavior, dashboard
- Full endpoint inventory maintained in memory-bank

### Route Summary
| Category | Routes |
|----------|--------|
| Health | GET /health, GET /ready |
| Transactions | GET /api/transactions, GET /api/export/csv |
| Overview | GET /api/overview |
| Categories | GET /api/categories, GET /api/categories/list |
| Analytics | GET /api/analytics |
| Statements | GET /api/statements, GET /api/statements/{id}/validate |
| Banks | GET /api/banks |
| Members | GET /api/members, POST /api/members |
| Cashflow | GET /api/cashflow/monthly |
| Accounts | GET /api/accounts, GET /api/accounts/{id}/balance, GET /api/accounts/{id}/running-balance |
| Accounts (Manual) | GET/POST/PUT/DELETE /api/accounts/manage |
| Reconciliations | GET /api/reconciliations, GET /api/reconciliations/pending, GET /api/reconciliations/scan, POST /api/reconciliations/create, POST /api/reconciliations/batch-insert, POST /api/reconciliations/{id}/confirm, POST /api/reconciliations/{id}/reject |
| Behavior | GET /api/behavior/summary, GET /api/behavior/score, GET /api/behavior/insights |
| Audit | GET /api/audit/report |
| Dashboard | GET /api/dashboard/summary |
| Upload | POST /api/upload |
| Import | POST /api/import/detect, POST /api/import/execute |

---

## Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| Backend unit | pytest | Engine logic, determinism, reconciliation (5 test files) |
| Backend invariants | pytest | Financial invariant validation |
| Contract tests | vitest | API contract verification (8 files, 38 tests passing) |
| E2E | Playwright | Navigation, dashboard, transactions, behavior, reconciliation (176 passing, 18 skipped) |
| Visual | Playwright | Screenshot comparison (deferred) |
| Performance | Playwright | Load time thresholds (CI-adjusted) |

### Playwright Configuration
- Auto-starts backend using venv Python
- Falls back to localStorage if backend unavailable
- Seeds deterministic test data via global setup
- 12 test specs

---

## MCP Usage

| MCP Server | Purpose |
|------------|---------|
| Filesystem | File read/write operations |
| SQLite | Database querying during audit |
| Git | Repository inspection and version control |
| Sequential Thinking | Complex problem decomposition |
| Playwright | E2E test execution and browser automation |
| Context7 | Documentation reference |
| shadcn | UI component registry |
| magic-ui | UI component registry |

---

## Financial Unit Policy

- All monetary values stored as integer paise (paise = rupees × 100)
- Frontend converts paise → rupees for display via `formatINR()`
- Backend is authoritative for all financial calculations
- Every monetary value must be traceable end-to-end: database → backend → API → frontend → display
- Dashboard summary returns `net_cash_flow_paise` (integer paise)
- Cashflow endpoint returns paise for all monetary fields
- Account balances use `balance_paise` field

---

## Build Configuration

- **Next.js**: Turbopack enabled, worker root configuration
- **TypeScript**: Strict mode, path aliases (`@/lib`, `@/components`, etc.), no implicit any
- **Backend**: uvicorn ASGI server, hot-reload enabled

## How to Run

```bash
# Frontend
cd frontend && npm run dev

# Backend
cd backend && uvicorn src.api:app --reload --port 8000