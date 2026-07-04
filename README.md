# ClariFin_OS

[![Backend Tests](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/backend-tests.yml)
[![Frontend Build](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/frontend-build.yml/badge.svg)](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/frontend-build.yml)
[![Full Stack Validation](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/full-validation.yml/badge.svg)](https://github.com/simcitysocial97-dev/ClariFin_OS/actions/workflows/full-validation.yml)

> Personal Financial Management System with automated statement processing and intelligent categorization

## Status
- ✅ Backend: 10/10 tests passing, 95.5% classification coverage
- ✅ Frontend: Build passing, 0 TypeScript errors
- ✅ Database: SQLite with proper paise handling and immutability triggers

## What Is This

![ClariFin OS Screenshot](docs/screenshot.png)

**Personal finance management system with behavioral intelligence**

ClariFin OS is a comprehensive, local-first personal finance management system designed for individuals who want complete control over their financial data. Built with deterministic computation and an immutable ledger, ClariFin provides a complete financial picture without cloud dependencies.

## What Is This

ClariFin OS is your personal financial intelligence system that:

- **Runs entirely on your machine** - No cloud dependency, your data stays private
- **Provides deterministic computation** - Same inputs always produce same outputs
- **Maintains an immutable ledger** - Transactions cannot be altered once recorded
- **Offers behavioral analysis** - Understand your spending patterns and financial habits

ClariFin gives you a complete picture of your financial life with bank statement import, categorization, loan tracking, investment monitoring, and intelligent insights - all while keeping your sensitive financial data under your control.

## Features

### 💰 Transaction Management
- PDF bank statement import (HDFC, SBI, ICICI, Axis, IDFC First, IndusInd)
- **NEW: V2 Staging Pipeline** - Atomic statement import with validation
- **NEW: Docling AI Extraction** - Optional AI-powered PDF extraction
- **NEW: Auto-Heal Engine** - Conservative statement repair for OCR errors
- CSV/Excel import with column mapping
- Automatic categorization with keyword-based rules
- Duplicate detection via SHA256 hash signatures
- Immutable transaction ledger with audit trails
- **NEW: Quarantine System** - Manual review for failed validations

### 🏦 Account & Card Tracking
- Multiple bank accounts (savings, current, wallet)
- Credit/debit card management with billing cycles
- Running balance computation and reconciliation
- Account-specific transaction filtering

### 📊 Loans & Liabilities
- Loan tracking with EMI calculation
- Amortization schedule generation
- Payment history recording
- Prepayment impact simulation (reduce tenure / reduce EMI)
- Loan payoff projections with interest savings

### 📈 Investments & Assets
- Portfolio tracking (mutual funds, stocks, FD, PPF, gold, real estate, crypto)
- Asset allocation visualization
- Gain/loss calculation with time-weighted returns
- Net worth computation across all asset classes
- Investment performance tracking

### 💵 Income & Cash Flow
- Income source tracking (salary, freelance, dividends, interest, etc.)
- Monthly cash flow analysis with trend visualization
- Fixed vs variable expense breakdown
- Savings rate calculation
- Burn rate and runway estimation

### 🔄 Recurring Transactions
- Auto-detection of recurring patterns
- Subscription tracking with renewal alerts
- EMI/SIP monitoring
- Next due date prediction
- Recurring expense forecasting

### 🧠 Behavioral Intelligence
- 5 behavioral indices (loss aversion, impulsivity, habit stability, financial stress, savings discipline)
- Composite financial health score (0-100)
- Evidence-based insights from spending patterns
- Personalized nudges based on transaction history
- India-specific risk detection (late payments, high credit utilization)

### 📅 Financial Planning
- Net worth projection (5-year forecast)
- Goal planning calculator with target dates
- What-if scenario analysis
- Monthly financial snapshots with comparisons
- Retirement planning estimates

### 🔍 Reconciliation & Audit
- Cross-account transfer matching
- Ledger integrity verification
- Hash signature validation
- Orphan record detection
- Statement validation with bank records

### 📤 Data Portability
- Full JSON export/import of all financial data
- CSV export for accounting software
- Database backup/restore functionality
- Statement archive management

## Current Status

> **Last Updated:** 01 March 2026

### System Health
- ✅ **Backend:** All core engines operational (253 tests)
- ⚠️ **Frontend:** Build requires fix (missing generateStaticParams)
- ✅ **Database:** 19 tables, immutable ledger verified
- ✅ **Docling:** Integration complete, optional dependency

### Known Issues
- Frontend build fails on `/quarantine/[id]` page (see [#1](PROJECT_AUDIT_REPORT.md))
- 4 auto-heal tests failing (non-critical, disabled by default)
- Loans page is placeholder (feature in development)
- 21 unused backend routes (cleanup pending)

### Recent Updates
- **V2 Import Pipeline:** Staging-based atomic commits with validation
- **Docling Integration:** AI-powered PDF extraction (opt-in via env var)
- **Quarantine System:** Manual review workflow for failed validations
- **Auto-Heal Engine:** Conservative repair for common OCR errors

For detailed audit report, see [PROJECT_AUDIT_REPORT.md](PROJECT_AUDIT_REPORT.md)

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 16.1.6, React 19.2.3, TypeScript, Tailwind CSS, shadcn/ui, Recharts |
| **Backend** | FastAPI, Python 3.10+, SQLite (WAL mode) |
| **PDF Extraction** | camelot-py, pdfplumber, Ghostscript |
| **Data Processing** | pandas, numpy |
| **State Management** | Zustand |
| **Testing** | pytest, Playwright |

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Architecture
Backend: FastAPI + SQLAlchemy + SQLite
Frontend: Next.js 16 (App Router) + React Query + Tailwind + shadcn/ui
Testing: pytest (backend) + TypeScript strict mode (frontend)

## Development
All pushes to main automatically run:

- Backend pytest suite
- Frontend TypeScript checks and build validation
- Bundle size analysis

### Prerequisites
- Python 3.10+
- Node.js 20+
- Ghostscript (`sudo apt install ghostscript`)

### Setup

```bash
git clone <repo>
cd ClariFin_OS

# Backend
cd backend
make venv    # Creates venv, installs deps, verifies

# Frontend
cd ../frontend
npm ci
```

### Quick Start (Development)

```bash
# Start both backend and frontend dev servers
make start

# Or use the script directly
./start.sh

# Stop running servers
make stop
```

The servers will start on:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### With Docker

```bash
docker-compose up --build
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Health Check: http://localhost:8000/api/health
- API Docs: http://localhost:8000/docs

## Project Structure

```
ClariFin_OS/
├── frontend/          # Next.js application
│   ├── app/           # Pages and routes
│   ├── components/    # React components
│   ├── lib/           # Utilities and hooks
│   └── public/        # Static assets
├── backend/           # FastAPI + SQLite
│   ├── src/           # API and database code
│   │   ├── routers/   # 14 domain-specific routers
│   │   ├── engines/   # 11 financial computation engines
│   │   └── extraction/# PDF extraction modules
│   └── data/          # SQLite database + uploaded statements
├── memory-bank/       # Project documentation
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## API Reference

| Domain | Endpoint | Description |
|--------|----------|-------------|
| **Transactions** | `GET /api/transactions` | List transactions with filters |
|  | `POST /api/transactions/categorize` | Batch categorize transactions |
| **Accounts** | `GET /api/accounts` | List all accounts |
|  | `POST /api/accounts` | Create new account |
| **Cards** | `GET /api/cards` | List all cards |
|  | `POST /api/cards` | Add new card |
| **Loans** | `GET /api/loans` | List all loans |
|  | `POST /api/loans` | Create new loan |
|  | `GET /api/loans/{id}/amortization` | Get amortization schedule |
| **Investments** | `GET /api/investments` | List all investments |
|  | `POST /api/investments` | Add new investment |
| **Income** | `GET /api/income-sources` | List income sources |
|  | `POST /api/income-sources` | Add income source |
| **Recurring** | `GET /api/recurring` | List recurring transactions |
|  | `POST /api/recurring` | Add recurring transaction |
| **Behavior** | `GET /api/behavior/score` | Get behavioral score |
|  | `GET /api/behavior/insights` | Get financial insights |
| **Projections** | `GET /api/projections/networth` | 5-year net worth projection |
|  | `POST /api/projections/scenario` | What-if analysis |
| **Reconciliation** | `GET /api/reconciliation/matches` | Find transfer matches |
|  | `POST /api/reconciliation/confirm` | Confirm reconciliation |
| **Upload** | `POST /api/upload` | Upload PDF statement |
|  | `GET /api/upload/history` | Get import history |
| **Export** | `GET /api/export/json` | Full JSON export |
|  | `GET /api/export/csv` | CSV export |

## Database Design

ClariFin uses SQLite with 14 tables for comprehensive financial tracking:

| Table | Purpose |
|-------|---------|
| `statements` | Uploaded bank statements metadata |
| `transactions` | Immutable transaction ledger (hash signatures) |
| `accounts` | Bank accounts and wallets |
| `cards` | Credit/debit cards |
| `loans` | Loan tracking and amortization |
| `loan_payments` | Individual loan payments |
| `investments` | Investment portfolio tracking |
| `income_sources` | Regular income streams |
| `recurring_transactions` | Subscription and EMI tracking |
| `monthly_snapshots` | Historical financial snapshots |
| `reconciliations` | Cross-account transfer matching |
| `members` | Family members for expense tracking |
| `import_mappings` | CSV import configurations |
| `sqlite_sequence` | SQLite sequence tracking |

**Key Features:**
- Integer paise storage (no floating point for money)
- Deterministic computation (same input → same output)
- Immutable ledger with database triggers
- Hash-based duplicate detection

## Financial Computation Model

**Integer Paise Storage:**
- All monetary values stored as integers (paise)
- Eliminates floating-point rounding errors
- 1 INR = 100 paise

**EMI Formula:**
```
EMI = P × r × (1 + r)^n / ((1 + r)^n - 1)
Where P = principal, r = monthly interest rate, n = number of months
```

**Interest Calculation:**
- Daily reducing interest for loans
- Exact day count between payments

**Projection Methodology:**
- Monthly compounding for investments
- Conservative growth assumptions
- Inflation-adjusted returns

## Development

### Running Tests

```bash
# Backend tests
cd backend && make test           # All tests
cd backend && make test-golden    # Financial golden tests only

# Frontend tests
cd frontend && npm test           # Playwright tests
```

### Database Maintenance

```bash
cd backend && make db-status      # Show DB health
cd backend && make db-backup      # Create backup
cd backend && make db-vacuum      # Optimize database
```

### Validation

```bash
cd backend && make validate       # Pipeline validator
cd backend && make doctor         # Environment check
```

## Limitations

- **Single user only** - No multi-user authentication
- **INR (₹) only** - No multi-currency support
- **Manual import only** - No real-time bank sync
- **Web-only interface** - No mobile app
- **SQLite backend** - Single instance, no horizontal scaling
- **Deterministic analysis** - No AI/ML (all rules-based)

## License

MIT License - See [LICENSE](LICENSE) file for details.