# Active Context

## Current Mission

**Prompt 4A.1: Move Member SQL** — COMPLETED

## Prompt 4A.1 Changes (2026-07-08)
- Added `_get_conn()` method to `src/repositories/base.py` for direct connection access
- Moved `get_members()` and `add_member()` SQL from `db.py` into `src/repositories/member_repository.py`
- Updated `db.py` to delegate to `MemberRepository` (backward compatibility)
- All methods tested: `get_all()` and `create()` work correctly via repository and via `FinanceDB` wrapper

## Next Steps
- Continue moving other SQL methods into repositories as needed

## Phase 3B.9 Changes (2026-07-08)
- Created `src/repositories/dashboard_repository.py` with DashboardRepository wrapper (cross-domain orchestration)
- Wrapped method: get_summary (combines TransactionRepository + behavior profile)
- Updated `routers/dashboard.py` to use DashboardRepository instead of direct DB_PATH and get_db()
- Exported DashboardRepository in `src/repositories/__init__.py`

## Phase 3B.8 Changes (2026-07-08)
- Created `src/repositories/behavior_repository.py` with BehaviorRepository wrapper
- Wrapped methods: compute_profile, get_cached_profile, set_cached_profile, generate_insights
- Updated `routers/behavior.py` to use BehaviorRepository instead of direct DB_PATH

## Phase 3B.7 Changes (2026-07-08)
- Created `src/repositories/audit_repository.py` with AuditRepository wrapper
- Wrapped method: run_full_audit
- Updated `routers/audit.py` to use AuditRepository instead of direct DB_PATH

## Phase 3B.6 Changes (2026-07-08)
- Created `src/repositories/reconciliation_repository.py` with ReconciliationRepository wrapper
- Wrapped methods: get_reconciliations, get_pending_reconciliations, insert_reconciliation, confirm_reconciliation, reject_reconciliation, get_confirmed_transfer_ids
- Updated `routers/reconciliation.py` to use ReconciliationRepository instead of get_db()

## Phase 3B.5 Changes (2026-07-08)
- Created `src/repositories/transaction_repository.py` with TransactionRepository wrapper
- Wrapped methods: get_all_transactions, get_all_transactions_with_bank, insert_transactions, get_monthly_summary, get_category_summary, get_category_totals_by_month, bulk_update_category, get_uncategorized_patterns, get_confirmed_transfer_ids
- Updated `routers/transactions.py` to use TransactionRepository instead of get_db()
- Updated `routers/export.py` to use TransactionRepository instead of get_db()
- Exported TransactionRepository in `src/repositories/__init__.py`

## Phase 3B.4 Changes (2026-07-08)
- Added `get_networth_data` method to `db.py` returning accounts, loans, investments, statements
- Created `src/repositories/networth_repository.py` with NetWorthRepository wrapper
- Updated `routers/networth.py` to use NetWorthRepository instead of direct FinanceDB calls
- Exported NetWorthRepository in `src/repositories/__init__.py`

## Phase 3B.3 Changes (2026-07-08)
- Added `get_monthly_cashflow` method to `db.py` for month-by-month income/expense aggregation
- Created `src/repositories/cashflow_repository.py` with CashflowRepository wrapper
- Updated `routers/cashflow.py` to use CashflowRepository instead of direct `_get_conn()` calls
- Exported CashflowRepository in `src/repositories/__init__.py`
- All endpoints tested and working: /api/cashflow/monthly

## Phase 3B.2 Changes (2026-07-08)
- Created `src/repositories/statement_repository.py` with StatementRepository wrapper
- Wrapped methods: get_all_statements, get_all_statements_with_metadata, insert_statement, update_statement_metadata, update_validation_status, get_statement_validation_summary, delete_statement, get_statement_pdf_path
- Updated `routers/cards_statements.py` to use StatementRepository instead of get_db()
- Exported StatementRepository in `src/repositories/__init__.py`
- All endpoints tested and working: /api/statements, /api/cards

## Phase 3B.1 Changes (2026-07-08)
- Created `src/repositories/account_repository.py` with AccountRepository wrapper
- Wrapped methods: get_all_accounts, create_account, update_account, delete_account, compute_account_balance, compute_running_balance, get_accounts_list

## Import Router Cleanup (2026-07-08)
- Updated `routers/import_router.py` to use StatementRepository and TransactionRepository instead of get_db()
- Added `get_duplicate_check_by_filename` and `insert_csv_transactions` to repositories
- All routers now use repositories only — no direct FinanceDB or get_db() imports

## CGC Indexing Quality Improvements (COMPLETED 2026-07-08)
- Installed `scip-python` v0.6.6 (npm global), symlinked to `~/.local/bin/scip-python`
- CGC `.env` (`/home/vasantha/.codegraphcontext/.env`):
  - `SCIP_INDEXER=true`, `SCIP_LANGUAGES=python`
  - `ENABLE_INHERIT_RESOLVE=true` (resolves class hierarchies)
  - `IGNORE_DIRS` updated: `node_modules,venv,.venv,env,.env,dist,build,target,out,.git,idea,.vscode,__pycache__,public,mocks,_archived_reflex_dashboard,memory-bank,docs,servers,target,.cline`
- `.cgcignore` overhauled with global patterns
- ENOSPC Fix: Root partition `/dev/sda8` was 98% full (1.3G) — SCIP writes temp to `/tmp` on root
  - Created `/home/vasantha/.tmp` and set `TMPDIR` redirect

## Technical Debt (UPDATED)
- **enrich_transaction()** — Deprecated but still used for behavioral insights (non-monetary)
- **compute_is_large()** — Disabled (uses deprecated `amount` field)
- **formatRupees / formatRupeesCompact** — Deprecated, kept for backward compatibility (**PENDING REMOVAL**)
- **Empty modular directories**: `app/`, `audits/`, `db/`, `parsers/`, `reports/`, `routers/`, `utils/` — shell directories with no .py files