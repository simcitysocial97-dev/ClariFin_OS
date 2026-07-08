# Active Context

## Current Mission

**Phase 3A: Repository Layer (Wrapper Only)** — COMPLETED

## Phase 3A Changes (2026-07-08)
- Created `src/repositories/` package with BaseRepository, MemberRepository, BankRepository, InvestmentRepository, LoanRepository
- Updated `routers/members.py` to use MemberRepository instead of get_db()
- Updated `routers/banks.py` to use BankRepository instead of get_db()
- Updated `routers/investments.py` to use InvestmentRepository instead of FinanceDB context manager
- Updated `routers/loans.py` to use LoanRepository instead of FinanceDB context manager
- All endpoints tested and working: /api/members, /api/banks, /api/investments, /api/loans
- ruff check passed; mypy errors are pre-existing in codebase

## CGC Indexing Quality Improvements (COMPLETED 2026-07-08)

### Phase 0 — SCIP Enabled
- Installed `scip-python` v0.6.6 (npm global), symlinked to `~/.local/bin/scip-python`
- CGC `.env` (`/home/vasantha/.codegraphcontext/.env`):
  - `SCIP_INDEXER=true`, `SCIP_LANGUAGES=python`
  - `ENABLE_INHERIT_RESOLVE=true` (resolves class hierarchies)
  - `IGNORE_DIRS` updated: `node_modules,venv,.venv,env,.env,dist,build,target,out,.git,idea,.vscode,__pycache__,public,mocks,_archived_reflex_dashboard,memory-bank,docs,servers,target,.cline`
- `.cgcignore` overhauled with global patterns (node_modules/, venv/, __pycache__/, dist/, build/, public/, mocks/, tests/, *.spec.ts, *.test.ts, etc.)
  - Removed overly broad `*.mjs` rule (was blocking useful frontend code)
- ENOSPC Fix: Root partition `/dev/sda8` was 98% full (1.3G) — SCIP writes temp to `/tmp` on root
  - Created `/home/vasantha/.tmp` and set `TMPDIR` redirect
  - Added `export TMPDIR=/home/vasantha/.tmp` to `~/.bashrc` (persistent)

### Phase 1 — Automatic/Live Indexing (COMPLETED 2026-07-08)
Three-layer automatic coverage configured:
1. **File Watcher (live)**: `cgc watch` running as systemd user service `cgc-watch.service`
   - Service file: `/home/vasantha/.config/systemd/user/ccgc-watch.service`
   - `systemctl --user enable cgc-watch.service` (survives reboots)
   - `systemctl --user start cgc-watch.service` (active, PID 429065)
   - Verified: touching `db.py` triggered auto re-index (debug log shows parse activity)
2. **Git Hooks (commit-time)**: `cgc hook install` installed
   - Managed hooks: `post-commit`, `post-checkout`
   - Merge driver: installed
   - `.gitattributes`: installed
3. **MCP Server**: Already running (PID 326653) for IDE queries

### Verification Results
- ✅ `cgc update` re-indexed in 330s with SCIP (no ENOSPC)
- ✅ `FinanceDB`, `AccountDTO`, `TransactionMapper`, `Settings` resolve with symbol-level info
- ✅ 24 `INHERITS` edges found: DTOs→BaseModel, AppError→Exception, ValidationError/DatabaseError/FileError/NotFoundError→AppError
- ✅ `db.py` analysis: 59 functions, 226 variables, 1 class indexed; `__enter__` shows `Self@FinanceDB` return type (SCIP symbol-level)
- ✅ Watcher live and auto-updating on file changes
- ✅ Git hooks installed for commit-time sync

## Technical Debt (UPDATED)
- **enrich_transaction()** — Deprecated but still used for behavioral insights (non-monetary)
- **compute_is_large()** — Disabled (uses deprecated `amount` field)
- **formatRupees / formatRupeesCompact** — Deprecated, kept for backward compatibility (**PENDING REMOVAL**)
- **Empty modular directories**: `app/`, `audits/`, `db/`, `parsers/`, `reports/`, `routers/`, `utils/` — shell directories with no .py files
- **Unused extraction modules**: `camelot_extractor.py`, `hybrid_extractor.py` — exist on disk, not wired into upload flow
