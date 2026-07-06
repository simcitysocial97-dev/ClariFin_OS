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
│   │   └── test/                # Test pages
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui primitives
│   │   ├── dashboard/           # Dashboard widgets
│   │   ├── cards/               # Card components
│   │   ├── import/              # Import workflow
│   │   ├── layout/              # Layout components
│   │   ├── members/             # Member management
│   │   ├── onboarding/          # Onboarding flow
│   │   └── upload/              # Upload components
│   ├── hooks/                   # React hooks
│   ├── types/                   # TypeScript type definitions
│   ├── lib/                     # API client, parser, utilities
│   └── tests/                   # Playwright E2E tests
│       ├── specs/               # Test specifications
│       ├── fixtures/            # Custom fixtures
│       └── utils/               # Test utilities
├── backend/                     # FastAPI + SQLite
│   ├── src/                     # Application code
│   │   ├── api.py               # FastAPI application + endpoints
│   │   ├── db.py                # Database operations
│   │   ├── categorizer.py       # Transaction categorization
│   │   ├── csv_importer.py      # CSV/Excel import
│   │   ├── engines/             # Deterministic computation engines
│   │   │   ├── balance_engine.py
│   │   │   ├── behavior_engine.py
│   │   │   ├── insight_generator.py
│   │   │   ├── ledger_audit_engine.py
│   │   │   ├── nudge_engine.py
│   │   │   └── reconciliation_engine.py
│   │   ├── core/                # Domain models and services
│   │   ├── extraction/          # PDF extraction modules
│   │   ├── parsers/             # Bank-specific parsers
│   │   └── structural/          # Layout analysis
│   ├── tests/                   # Python test suite
│   └── data/                    # Database + uploads
├── memory-bank/                 # Cline context (project documentation)
├── servers/                     # MCP server implementations
├── Audit_Report.md              # Append-only audit findings
└── README.md                    # Project overview
```

---

## Backend Architecture

### FastAPI Application
- Single `api.py` entry point with CORS middleware
- Configured for origins: `localhost:3000`, `localhost:3001`
- Raw SQLite3 (no ORM) with inline DDL
- Database file: `backend/data/finance.db`

### Engine Architecture
Each engine is a deterministic computation module:
- **balance_engine.py**: Account balance computation, running balance history
- **behavior_engine.py**: 5 behavioral indices + financial health score
- **insight_generator.py**: Evidence-based financial insights
- **ledger_audit_engine.py**: Hash verification, integrity validation
- **nudge_engine.py**: Rules-based financial suggestions
- **reconciliation_engine.py**: Confidence-based transaction matching

### Ledger Integrity
- Append-only transaction storage
- Hash signature unique index prevents duplicates
- ISO date ordering ensures correct chronological replay
- Database-level trigger enforcement against mutation

---

## Frontend Architecture

### App Router Pages
- `/dashboard` — Dual-mode dashboard (Personal/Family)
- `/transactions` — Transaction list with filtering and search
- `/accounts` — Account management
- `/cards` — Card management
- `/settings` — Application settings

### Data Fetching
- React Query (TanStack Query) for server state
- Custom hooks wrapping API calls
- Zustand for local UI state (theme, mode preference)

### Parser Architecture
- Client-side PDF.js for text extraction
- Spatial text extraction using PDF.js transform coordinates
- Y-coordinate flipping (PDF origin is bottom-left → top-down)
- Items grouped into lines using Y position tolerance (5px)
- Bank-specific pattern matching for transaction extraction

---

## SQLite Architecture

- Raw SQLite3 driver (no ORM, no SQLAlchemy)
- Inline DDL in `db.py`
- Append-only transaction table with hash-based deduplication
- Immutability triggers at database level
- Deterministic keys for idempotent inserts

---

## API Architecture

- RESTful FastAPI application
- CORS configured for local development
- Endpoints organized by domain: transactions, accounts, behavior, audit, import/export
- Full endpoint inventory maintained in `Audit_Report.md` (append-only)

---

## Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| Backend unit | pytest | Engine logic, determinism, reconciliation |
| Backend invariants | pytest | Financial invariant validation |
| E2E | Playwright | Navigation, dashboard, transactions, behavior, reconciliation |
| Visual | Playwright | Screenshot comparison (deferred) |
| Performance | Playwright | Load time thresholds (CI-adjusted) |

### Playwright Configuration
- Auto-starts backend using venv Python
- Falls back to localStorage if backend unavailable
- Seeds deterministic test data via global setup
- 12 test specs covering navigation, financial logic, behavioral scoring, edge cases

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
- Frontend converts paise → rupees for display
- Backend is authoritative for all financial calculations
- Every monetary value must be traceable end-to-end: database → backend → API → frontend → display

---

## Current Engineering Principles

These principles take precedence over feature work:

1. **Read-Only During Audit**: No production code modifications, no refactoring, no formatting, no dependency updates
2. **Evidence First**: Every finding must include file path, function, line number, confidence, and supporting evidence. Never infer missing information.
3. **Financial Correctness**: Primary validation target — Database → Backend → API → Frontend → Hooks → Components → Charts → Display
4. **Append-Only Audit Report**: `Audit_Report.md` is never rewritten. Previous phases are preserved.
5. **SQLite Inventory**: The SQLite audit database is the supporting inventory for all audit findings.
6. **Implementation After Audit**: No new features or architectural changes until the audit is complete.

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