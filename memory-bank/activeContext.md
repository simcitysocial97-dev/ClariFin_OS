# Active Context

## Current Mission

**AccountService Extraction** — COMPLETED

## AccountService Changes (2026-09-07)
- ✅ Created `src/services/account_service.py` with `get_accounts_list()`, `compute_account_balance()`, `compute_running_balance()` methods
- ✅ Removed `get_accounts_list`, `compute_account_balance`, `compute_running_balance` from `AccountRepository` (kept SQL methods: `get_all_accounts`, `create_account`, `update_account`, `delete_account`, `get_account_by_id`)
- ✅ Updated `src/routers/accounts.py` to use `AccountService` for orchestration endpoints
- ✅ Updated `src/routers/managed_accounts.py` to use `AccountService` for `/balance` and added `/running-balance` endpoint
- ✅ Added `AccountService` to `src/services/__init__.py` exports
- ✅ Validation: `GET /api/accounts` ✅, `GET /api/accounts/{id}/balance` ✅, `GET /api/accounts/{id}/running-balance` ✅

## Next Steps
- Continue extracting engine-call methods to services where appropriate

## AuditService Changes (2026-09-07)
- ✅ Created `AuditService` in `src/services/audit_service.py` extending `BaseService` with `run_full_audit()`
- ✅ Updated `src/routers/audit.py` to use `AuditService` instead of `AuditRepository`
- ✅ Deleted `src/repositories/audit_repository.py` (was pure orchestration, no SQL)
- ✅ Removed `AuditRepository` from `src/repositories/__init__.py` exports (was already absent)
- ✅ Added `AuditService` to `src/services/__init__.py` exports (was already present)
- ✅ Validation: ruff clean, mypy clean on all modified files

## BehaviorService Changes (2026-09-07)
- ✅ Created `BehaviorService` in `src/services/behavior_service.py` with `compute_profile()`, `get_cached_profile()`, `set_cached_profile()`, `generate_insights()`
- ✅ Updated `src/routers/behavior.py` to use `BehaviorService` instead of `BehaviorRepository`
- ✅ Deleted `src/repositories/behavior_repository.py` (was pure orchestration, no SQL)
- ✅ Removed `BehaviorRepository` from `src/repositories/__init__.py` exports
- ✅ Added `BehaviorService` to `src/services/__init__.py` exports
- ✅ Validation: ruff clean, mypy clean on all modified files

## NetWorthService Changes (2026-09-07)
- ✅ Created `NetWorthService` in `src/services/networth_service.py` with `calculate()` method
- ✅ Moved business logic (card statement deduplication, is_partial check) from router to service
- ✅ Updated router to use `NetWorthService` instead of `NetWorthRepository` directly (fixes Repository Boundary Rule violation)
- ✅ Removed unused `get_net_worth()` method (had dead SQL code) from `NetWorthRepository`

## Router Type Fixes (2026-09-07)
- ✅ Fixed `pyproject.toml` mypy module patterns: added `src.models` and `src.repositories` (without wildcard) to match packages correctly
- ✅ Fixed `src/routers/members.py`: Added `-> dict` return type annotations on `get_members` and `create_member`
- ✅ Fixed `src/routers/export.py`: Added `-> StreamingResponse` return type annotation
- ✅ Fixed `src/routers/cashflow.py`: Added `-> dict` return type annotation
- ✅ Fixed `src/routers/import_router.py`: Added null-safety for `file.filename` (using `or ""` fallback), fixed `amount_float` to use `0.0` instead of `None`
- ✅ Fixed `src/health.py`: Changed relative imports to absolute imports (`from config` → `from src.config`)
- ✅ Fixed `src/logger.py`: Changed relative imports to absolute imports (`from config` → `from src.config`)
- ✅ Cleaned unused imports (`uuid`) and missing newlines with `ruff --fix`

## Mypy Strict Mode Enablement (2026-09-07)
- ✅ **Validated**: `mypy src/models src/repositories src/routers` passes with 0 errors (42 source files)
- ✅ **Validated**: `ruff check src/models src/repositories src/routers` passes

## Account Domain Model Changes (2026-09-07)
- ✅ Created `src/models/account.py` with `Account(DomainModel)` (id, name, type: AccountType Literal, initial_balance: Money) + `from_db_row()` factory mapping `initial_balance_paise` → `Money`
- ✅ Exported `Account` from `src/models/__init__.py`
- ✅ Added `AccountRepository.get_all() -> list[Account]` (aliases `balance_paise AS initial_balance_paise`, `account_type AS type`); existing dict methods untouched (non-breaking)
- ✅ Validation: ruff clean; runtime import + model construction OK; 0 new mypy errors (pre-existing mypy warnings in engines/db/other repos unchanged)