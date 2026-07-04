# Technical Context

## Technologies Used

### Core Stack
- **Next.js 16.1.6** - React framework with App Router
- **React 19.2.3** - UI library
- **TypeScript 5.x** - Type-safe development
- **Tailwind CSS 4.x** - Styling
- **shadcn/ui** - UI component library
- **FastAPI** - REST API framework
- **Python 3.10+** - Backend language
- **SQLite 3.x** - File-based database with WAL mode

### Key Dependencies (Frontend)
- **@tanstack/react-query 5.90.21** - Data fetching (QueryClient configured in QueryProvider)
- **pdfjs-dist 5.4.624** - PDF parsing
- **zustand 5.0.11** - State management
- **recharts 3.7.0** - Chart rendering
- **lucide-react 0.563.0** - Icons
- **next-themes 0.4.6** - Dark mode support

### Key Dependencies (Backend)
- **fastapi>=0.100.0**
- **uvicorn[standard]>=0.23.0**
- **camelot-py[cv]>=1.0.0**
- **pdfplumber>=0.11.9**
- **opencv-python-headless>=4.8.0**
- **ghostscript>=0.7**
- **pandas>=2.0.0**
- **numpy>=1.24.0**

### Testing
- **Playwright** - E2E testing (194 tests, 91% pass rate)
- **Pytest** - Backend unit tests

---

## Architecture

### Frontend Build Status
- **TypeScript:** Clean compilation (0 errors) ✅
- **Production Build:** Successful ✅
- **Static Pages:** 27 routes generated ✅
- **QueryClient:** Configured in `lib/providers/query-provider.tsx`

### Modular Monolith Design
- **Single Backend Process:** FastAPI
- **Single Frontend Process:** Next.js with static export
- **Deterministic Engines:** Pure functions for financial calculations
- **Immutable Ledger:** Append-only transaction storage

---

## Development Setup

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # localhost:3000
npm run build  # production build
```

### Database
- Path: `backend/data/finance.db`
- Migrations: Automatic on app startup via `db_schema.ensure_schema()`
- Backup: Copy `finance.db` file

---

## Testing Commands

```bash
# Backend
cd backend
pytest tests/

# Frontend
cd frontend
npx playwright test
npm run build  # TypeScript check + production build
```

---

## Frontend Build Issues (RESOLVED)

### Fixed Errors (15 total)
| Type | Files | Errors | Fix |
|------|-------|--------|-----|
| Unused imports | 5 | TS6133/TS6192 | Removed unused declarations |
| Readonly tuples | 2 | TS4104 | Spread `[...queryKeys.overview]` |
| Type mismatch | 3 | TS2322 | mutateAsync + return type fixes |

### Commit History
- `b762a390` - Fix readonly tuples + mutateAsync + return types
- `4e42a2f6` - Remove unused imports + useNetWorthTrendQuery fix

---

*Last Updated: 2026-07-03 - Frontend Build Stabilized*