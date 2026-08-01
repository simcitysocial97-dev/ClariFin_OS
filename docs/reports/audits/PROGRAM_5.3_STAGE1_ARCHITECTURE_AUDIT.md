# Program 5.3 — Stage 1: Backend Architecture Audit Report

**Date:** 2026-08-01  
**Phase:** Program 5.3 — Backend Stabilization & Validation  
**Stage:** 1 — Repository Architecture Audit (READ-ONLY)  
**Status:** Evidence-based findings, no code modified  

---

## Table of Contents

1. [Repository Architecture Report](#1-repository-architecture-report)
2. [Database Ownership Report](#2-database-ownership-report)
3. [Duplicate Module Report](#3-duplicate-module-report)
4. [Import Violation Report](#4-import-violation-report)
5. [Endpoint Trace Report](#5-endpoint-trace-report)
6. [Backend Freeze Readiness Report](#6-backend-freeze-readiness-report)

---

## 1. Repository Architecture Report

### 1.1 Complete Repository Inventory

**Base class:** `BaseRepository` at `backend/src/repositories/base.py:15`  
**Connection pattern:** `_get_conn()` → `sqlite3.connect()` (raw sqlite3, no ORM)

| # | Repository Class | File Path | Status |
|---|---|---|---|
| 1 | `BaseRepository` | `src/repositories/base.py:15` | ✅ Canonical base |
| 2 | `AccountRepository` | `src/repositories/account_repository.py:13` | ✅ Active |
| 3 | `AccountBalanceRepository` | `src/repositories/account_balance_repository.py:15` | ✅ Active |
| 4 | `AccountLinkRepository` | `src/repositories/account_link_repository.py:15` | ✅ Active |
| 5 | `BankRepository` | `src/repositories/bank_repository.py` | ✅ Active |
| 6 | `BehaviourRepository` | `src/repositories/behaviour_repository.py` | ✅ Active |
| 7 | `CashflowRepository` | `src/repositories/cashflow_repository.py` | ✅ Active |
| 8 | `CreditCardRepository` | `src/repositories/credit_card_repository.py` | ✅ Active |
| 9 | `CreditCardStatementRepository` | `src/repositories/credit_card_statement_repository.py` | ✅ Active |
| 10 | `FinancialEventRepository` | `src/repositories/financial_event_repository.py` | ✅ Active |
| 11 | `FinancialGoalRepository` | `src/repositories/financial_goal_repository.py` | ✅ Active |
| 12 | `ImportMappingRepository` | `src/repositories/import_mapping_repository.py` | ✅ Active |
| 13 | `InstitutionRepository` | `src/repositories/institution_repository.py` | ✅ Active |
| 14 | `InvestmentRepository` | `src/repositories/investment_repository.py` | ✅ Active |
| 15 | `LiquidityPatternRepository` | `src/repositories/liquidity_pattern_repository.py:11` | ✅ Active |
| 16 | `LoanRepository` | `src/repositories/loan_repository.py` | ✅ Active |
| 17 | `LoanPaymentRepository` | `src/repositories/loan_payment_repository.py` | ✅ Active |
| 18 | `MemberRepository` | `src/repositories/member_repository.py` | ✅ Active |
| 19 | `NetWorthRepository` | `src/repositories/networth_repository.py` | ✅ Active |
| 20 | `PatternRepository` | `src/repositories/pattern_repository.py` | ⚠️ Legacy (only used by dead `behavior_service.py`) |
| 21 | `ReconciliationRepository` | `src/repositories/reconciliation_repository.py` | ✅ Active |
| 22 | `ReconciliationAuditRepository` | `src/repositories/reconciliation_audit_repository.py` | ✅ Active |
| 23 | `StatementRepository` | `src/repositories/statement_repository.py` | ✅ Active |
| 24 | `TransactionRepository` | `src/repositories/transaction_repository.py` | ✅ Active |
| 25 | `TransactionClassificationRepository` | `src/repositories/transaction_classification_repository.py` | ✅ Active |
| 26 | `AlertRepository` | `src/repositories/alert_repository.py:13` | ❌ DEAD — 0 references outside `__init__.py` |

### 1.2 Routers Bypassing Service Layer (Direct Repository Access)

The following routers import repositories directly, bypassing the service layer:

| Router File | Repository Imported | Evidence |
|---|---|---|
| `src/routers/banks.py:5` | `BankRepository` | `from src.repositories.bank_repository import BankRepository` |
| `src/routers/export.py:9` | `TransactionRepository` | `from src.repositories import TransactionRepository` |
| `src/routers/investments.py:9` | `InvestmentRepository` | `from src.repositories.investment_repository import InvestmentRepository` |
| `src/routers/members.py:8` | `MemberRepository` | `from src.repositories.member_repository import MemberRepository` |
| `src/routers/import_router.py:15` | `StatementRepository, TransactionRepository` | `from src.repositories import StatementRepository, TransactionRepository` |

**Severity:** HIGH — 5 routers bypass the service layer, breaking the Router → Service → Repository chain.

### 1.3 Services Performing SQL Directly

**Finding:** No services import `sqlite3` or use raw SQL directly. All active services use repository classes for data access.

**Evidence:** `grep -rln "import sqlite3\|sqlite3.connect" src/services/` → 0 results

### 1.4 Models Comparison

| Location | File Count | Status |
|---|---|---|
| `src/models/` | 22 `.py` files | ✅ **Canonical** — all Pydantic models live here |
| `src/core/models/` | 0 files (empty) | Does not exist as a populated directory |

**Canonical location:** `src/models/`  
**Duplicates:** None — `src/core/models/` is empty/nonexistent.

**Models inventory (22 files):**
`account.py`, `account_balance.py`, `account_link.py`, `base.py`, `behaviour.py`, `credit_card.py`, `credit_card_emi.py`, `credit_card_foreclosure.py`, `credit_card_statement.py`, `dashboard.py`, `financial_event.py`, `financial_goal.py`, `institution.py`, `investment.py`, `loan.py`, `loan_analysis.py`, `loan_payment.py`, `loan_simulation.py`, `reconciliation.py`, `statement.py`, `transaction.py`, `__init__.py`

---

## 2. Database Ownership Report

### 2.1 Database Entry Points

The backend uses **raw `sqlite3` only — no SQLAlchemy ORM**. There is no `create_engine`, `sessionmaker`, or `Session` usage. Database ownership is fragmented across **three entry points**:

| # | Entry Point | File Path | Responsibility | Status |
|---|---|---|---|---|
| 1 | `FinanceDB` class | `src/db.py:769` | Schema creation, migrations, CLI | ✅ Schema owner |
| 2 | `BaseRepository` class | `src/repositories/base.py:15` | Data access (CRUD) | ✅ **Canonical data layer** |
| 3 | `get_db()` / `DB_PATH` | `src/common/database.py:16` | Legacy compatibility shim | ❌ DEPRECATED |

### 2.2 Connection Creation

| Module | Connection Method | Line | Purpose |
|---|---|---|---|
| `src/db.py` | `sqlite3.connect(self.db_path)` | 808-813 (`_connect()`) | Schema/migration only |
| `src/repositories/base.py` | `sqlite3.connect()` | 27 (`_get_conn()`) | All domain data access |
| `src/health.py` | `sqlite3.connect()` | (in `/ready` endpoint) | Health check connectivity |

### 2.3 DB_PATH Duplication

The database path is resolved in **3 separate locations** with identical logic:

| Location | Line | Expression |
|---|---|---|
| `src/common/database.py` | 16 | `DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")` |
| `src/repositories/base.py` | 12 | `DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")` |
| `src/services/base.py` | 23 | `or os.getenv("FINANCE_DB_PATH")` |

All three fall back to `os.getenv("FINANCE_DB_PATH")` → hardcoded `data/finance.db`.

### 2.4 `get_db()` Consumers

| Consumer | File Path | Usage |
|---|---|---|
| `src/api_common.py:6` | `from src.common.database import DB_PATH` | Re-exports `DB_PATH` — **0 consumers of api_common** |
| `src/common/__init__.py:9` | `from .database import DB_PATH, get_db` | Package re-export |
| `src/services/financial_intelligence_service.py:11` | `from src.common import DB_PATH` | Uses `DB_PATH` as fallback at line 66 |

### 2.5 Canonical Database Architecture Recommendation

**Current state (fragmented):**
```
src/db.py (FinanceDB)          → Schema + migrations
src/repositories/base.py       → Data access (canonical)
src/common/database.py         → Legacy shim (get_db, DB_PATH)
src/services/base.py           → DB path resolution (duplicated)
```

**Recommended canonical (do NOT refactor yet):**
```
src/db.py (FinanceDB)          → Schema + migrations ONLY
src/repositories/base.py       → Data access + DB_PATH constant (single source)
src/common/database.py         → DELETE (legacy shim)
src/services/base.py           → Inherit DB_PATH from BaseRepository
```

---

## 3. Duplicate Module Report

### 3.1 Critical Duplicates

#### 3.1.1 Behavior vs Behaviour (Spelling Variant)

| File | Class | Spelling | Status | References |
|---|---|---|---|---|
| `src/services/behavior_service.py` | `BehaviorService` | American | ❌ DEAD | 0 production refs (only 1 test) |
| `src/services/behaviour_service.py` | `BehaviourService` | British | ✅ ACTIVE | `routers/behaviour.py`, `statement_orchestrator.py`, `financial_intelligence_service.py` |

**Engine duplication:**

| File | Type | Status |
|---|---|---|
| `src/engines/behavior_engine.py` | Single-file module (legacy) | ⚠️ Still imported by 4 modules |
| `src/engines/behaviour_engine/` | Package directory (current) | ✅ Active |

**Legacy `behavior_engine.py` consumers:**
- `src/engines/behaviour_engine/core.py:10` — bridge module
- `src/routers/import_router.py:19` — `invalidate_behavior_cache`
- `src/services/behavior_service.py:5` — dead service
- `src/services/dashboard_service.py:7` — **ACTIVE service using legacy engine**

#### 3.1.2 Account vs Accounts (Singular/Plural)

| File | Class | Router Consumer | Status |
|---|---|---|---|
| `src/services/account_service.py` | `AccountService` | `routers/accounts.py`, `routers/managed_accounts.py` | ✅ ACTIVE |
| `src/services/accounts_service.py` | `AccountsService` | `routers/accounts_router.py` (DEAD) | ❌ DEAD |

| File | Router | Prefix | Registered in `api.py` | Status |
|---|---|---|---|---|
| `src/routers/accounts.py` | `accounts` | `/api/v1` tags=["accounts"] | ✅ Yes (line 78) | ✅ ACTIVE |
| `src/routers/accounts_router.py` | `accounts_router` | `/api/v1` tags=["accounts-intelligence"] | ❌ No (0 matches) | ❌ DEAD |

### 3.2 Dead Routers

| Router File | Registered? | Status | Evidence |
|---|---|---|---|
| `src/routers/accounts_router.py` | ❌ Not in `api.py` | DEAD | `grep -c "accounts_router" src/api.py` → 0 |
| `src/routers/financial_intelligence.py` | ❌ Not in `api.py` | DEAD | `grep -c "financial_intelligence" src/api.py` → 0; 7 endpoints never exposed |

### 3.3 Dead Services

| Service File | Status | Evidence |
|---|---|---|
| `src/services/behavior_service.py` | DEAD | 0 production references; superseded by `behaviour_service.py` |
| `src/services/accounts_service.py` | DEAD | Only consumer is dead `accounts_router.py` |

### 3.4 Dead Repositories

| Repository File | Status | Evidence |
|---|---|---|
| `src/repositories/alert_repository.py` | DEAD | `grep -rn "AlertRepository" src/` → 0 results outside `__init__.py` |

### 3.5 Dead Mappers (ALL 5 mappers are unused)

| Mapper File | Status | Evidence |
|---|---|---|
| `src/core/mappers/account_mapper.py` | DEAD | 0 imports anywhere in `src/` |
| `src/core/mappers/analytics_mapper.py` | DEAD | 0 imports anywhere in `src/` |
| `src/core/mappers/dashboard_mapper.py` | DEAD | 0 imports anywhere in `src/` |
| `src/core/mappers/statement_mapper.py` | DEAD | 0 imports anywhere in `src/` |
| `src/core/mappers/transaction_mapper.py` | DEAD | 0 imports anywhere in `src/` |

**Evidence:** `grep -rn "from src.core.mappers" src/ --include="*.py"` → 0 results

### 3.6 Dead Infrastructure

| File | Status | Evidence |
|---|---|---|
| `src/api_common.py` | DEAD | Exports `DB_PATH` but 0 modules import from `api_common` |
| `src/routers/health.py` | SHIM | Re-exports from `src/health.py` — not registered in `api.py` (health registered via `register_health_routes(app)` at `api.py:46`) |

### 3.7 Naming Inconsistencies

| Pattern | Files | Issue |
|---|---|---|
| `_workspace` suffix | 8 services, 7 routers | Mixed convention — some domains have workspace variants, others don't |
| `_router` suffix | `src/routers/accounts_router.py` | Only router with `_router` suffix (all others use domain name) |
| `import_router.py` | `src/routers/import_router.py` | Only router with `_router` suffix that is active (avoids `import` keyword clash) |

### 3.8 Workspace Service Pattern

8 workspace services exist, wrapping core services with additional orchestration:

| Workspace Service | Wraps | Router |
|---|---|---|
| `behaviour_workspace_service.py` | `BehaviourService` | `behaviour_workspace.py` |
| `cashflow_workspace_service.py` | `CashflowService` | `cashflow_workspace.py` |
| `credit_cards_workspace_service.py` | `CreditCardService` | `credit_cards_workspace.py` |
| `investments_workspace_service.py` | `InvestmentRepository` (direct) | `investments_workspace.py` |
| `loans_workspace_service.py` | `LoanRepository` (direct) | `loans_workspace.py` |
| `networth_workspace_service.py` | Multiple repos | `networth_workspace.py` |
| `reconciliation_workspace_service.py` | `ReconciliationService` | `reconciliation_workspace.py` |

---

## 4. Import Violation Report

### 4.1 Architecture Boundary Violations

Per `.clinerules` Section 11:
- ONLY `src/repositories/` may import `FinanceDB`
- Routers MUST NOT import `FinanceDB` or `get_db()`
- Engines MUST NOT import `FinanceDB`

| Violation Type | File | Evidence | Severity |
|---|---|---|---|
| Router → Repository (bypass service) | `src/routers/banks.py:5` | `from src.repositories.bank_repository import BankRepository` | HIGH |
| Router → Repository (bypass service) | `src/routers/export.py:9` | `from src.repositories import TransactionRepository` | HIGH |
| Router → Repository (bypass service) | `src/routers/investments.py:9` | `from src.repositories.investment_repository import InvestmentRepository` | HIGH |
| Router → Repository (bypass service) | `src/routers/members.py:8` | `from src.repositories.member_repository import MemberRepository` | HIGH |
| Router → Repository (bypass service) | `src/routers/import_router.py:15` | `from src.repositories import StatementRepository, TransactionRepository` | HIGH |
| Service → Legacy DB_PATH | `src/services/financial_intelligence_service.py:11` | `from src.common import DB_PATH` | MEDIUM |
| Router → Engine (bypass service) | `src/routers/import_router.py:19` | `from src.engines.behavior_engine import invalidate_behavior_cache` | MEDIUM |
| Service → Legacy engine | `src/services/dashboard_service.py:7` | `from src.engines.behavior_engine import ...` | MEDIUM |

### 4.2 FinanceDB Import Check

**Finding:** No router or engine imports `FinanceDB` or `get_db()` directly.

**Evidence:** `grep -rn "FinanceDB\|get_db" src/routers/ src/engines/` → only comment-level mentions ("no FinanceDB import" in docstrings). The 4 router files flagged by grep (`accounts.py`, `behaviour.py`, `credit_cards.py`, `financial_intelligence.py`) contain only **comment text**, not actual imports.

### 4.3 Circular Import Analysis

**Finding:** No circular imports detected between services and routers.

**Evidence:** `grep -rn "from src.routers" src/services/` → 0 results (services do not import routers)

### 4.4 Legacy Bridge Modules

| Bridge Module | Bridges To | Status |
|---|---|---|
| `src/engines/behaviour_engine/core.py` | `src/engines/behavior_engine.py` | ⚠️ Active bridge — imports from legacy single-file module |
| `src/common/database.py` | `src/db.py` (FinanceDB) | ❌ Legacy shim — `get_db()` deprecated |
| `src/routers/health.py` | `src/health.py` | Re-export shim |
| `src/api_common.py` | `src/common/database.py` | Dead re-exporter |

---

## 5. Endpoint Trace Report

### 5.1 Summary Statistics

| Metric | Count |
|---|---|
| Total router files | 29 (including `__init__.py`) |
| Registered routers (in `api.py`) | 26 |
| Dead routers (not registered) | 2 (`accounts_router.py`, `financial_intelligence.py`) |
| Total endpoints | 115 |
| Endpoints with `response_model=` | 5 (4.3%) |
| Endpoints returning `dict[str, Any]` | 42 |
| Endpoints returning `list[dict[str, Any]]` | 10 |
| Endpoints returning typed DTOs | 5 |
| Routers importing DTOs (`src.core.dtos`) | 3 of 29 |
| Routers importing Pydantic models (`src.models`) | 3 of 29 |

### 5.2 Return Type Distribution

| Return Type | Count | DTO-compliant? |
|---|---|---|
| `dict[str, Any]` | 42 | ❌ No |
| `list[dict[str, Any]]` | 10 | ❌ No |
| `dict[str, int]` | 3 | ❌ No |
| `dict[str, str]` | 2 | ❌ No |
| `list[str]` | 1 | ❌ No |
| `DashboardSummaryDTO` | 1 | ✅ Yes |
| `CashflowSummaryDTO` | 1 | ✅ Yes |
| `CashflowCategoryResponse` | 1 | ✅ Yes |
| `AccountsDTO` | 1 | ✅ Yes |
| `AccountDetailDTO` | 1 | ✅ Yes |

### 5.3 Router → Service → Repository → Database Trace

#### Routers WITH Proper Service Layer

| Router | Service | Repository(s) | DTO? | Status |
|---|---|---|---|---|
| `accounts.py` | `AccountService` | `AccountRepository`, `AccountBalanceRepository`, `AccountLinkRepository` | ❌ dict | ✅ Chain complete |
| `audit.py` | `AuditService` | (uses `ledger_audit_engine`) | ❌ dict | ✅ Chain complete |
| `behaviour.py` | `BehaviourService` | `AccountRepository`, `BehaviourRepository`, `CreditCardRepository` | ❌ dict | ✅ Chain complete |
| `behaviour_workspace.py` | `BehaviourWorkspaceService` | `CreditCardRepository`, `LoanRepository` | ❌ dict | ✅ Chain complete |
| `cards_statements.py` | `StatementService` | `StatementRepository` | ❌ dict | ✅ Chain complete |
| `cashflow.py` | `CashflowService` | `CashflowRepository`, `TransactionRepository` | ✅ DTO | ✅ Chain complete |
| `cashflow_workspace.py` | `CashflowWorkspaceService` | (wraps `CashflowService`) | ❌ dict | ✅ Chain complete |
| `credit_cards.py` | `CreditCardService` | `CreditCardRepository`, `CreditCardStatementRepository` | ❌ dict | ✅ Chain complete |
| `credit_cards_workspace.py` | `CreditCardsWorkspaceService` | `CreditCardRepository`, `CreditCardStatementRepository` | ❌ dict | ✅ Chain complete |
| `dashboard.py` | `DashboardService` | `ReconciliationRepository`, `TransactionRepository` | ✅ DTO | ✅ Chain complete |
| `financial_events.py` | `FinancialEventsService` | `FinancialEventRepository` | ❌ dict | ✅ Chain complete |
| `forecast.py` | `ForecastService` | `CreditCardRepository`, `InvestmentRepository`, `LoanRepository` | ❌ dict | ✅ Chain complete |
| `investments_workspace.py` | `InvestmentsWorkspaceService` | `InvestmentRepository` | ❌ dict | ✅ Chain complete |
| `loans.py` | `LoanService`, `LoanAnalysisService`, `LoanSimulationService` | `LoanRepository`, `LoanPaymentRepository` | ❌ dict | ✅ Chain complete |
| `loans_workspace.py` | `LoansWorkspaceService` | `LoanRepository` | ❌ dict | ✅ Chain complete |
| `managed_accounts.py` | `AccountService` | `AccountRepository` | ❌ dict | ✅ Chain complete |
| `networth.py` | `NetWorthService` | `NetWorthRepository` | ❌ dict | ✅ Chain complete |
| `networth_workspace.py` | `NetWorthWorkspaceService` | `AccountRepository`, `CreditCardStatementRepository`, `InvestmentRepository` | ❌ dict | ✅ Chain complete |
| `reconciliation.py` | `ReconciliationService` | `ReconciliationRepository` | ❌ dict | ✅ Chain complete |
| `reconciliation_workspace.py` | `ReconciliationWorkspaceService` | `ReconciliationRepository` | ❌ dict | ✅ Chain complete |
| `transactions.py` | `TransactionService` | `TransactionRepository` | ❌ dict | ✅ Chain complete |

#### Routers BYPASSING Service Layer (Direct Repository Access)

| Router | Repository (direct) | DTO? | Status | Break |
|---|---|---|---|---|
| `banks.py` | `BankRepository` | ❌ dict | ⚠️ BREAK | Router → Repository (no service) |
| `export.py` | `TransactionRepository` | N/A (StreamingResponse) | ⚠️ BREAK | Router → Repository (no service) |
| `investments.py` | `InvestmentRepository` | ❌ dict | ⚠️ BREAK | Router → Repository (no service) |
| `members.py` | `MemberRepository` | ❌ dict | ⚠️ BREAK | Router → Repository (no service) |
| `import_router.py` | `StatementRepository`, `TransactionRepository` | ❌ dict | ⚠️ BREAK | Router → Repository + Engine (no service) |

#### Dead Routers (Not Registered)

| Router | Service | Would-be Chain | Status |
|---|---|---|---|
| `accounts_router.py` | `AccountsService` (dead) | Router → Service → Repo | ❌ DEAD — not in `api.py` |
| `financial_intelligence.py` | `FinancialIntelligenceService` | Router → Service → Repo | ❌ DEAD — not in `api.py` |

#### Health Router

| Router | Registration | Status |
|---|---|---|
| `src/health.py` | `register_health_routes(app)` at `api.py:46` | ✅ Active (registered differently) |
| `src/routers/health.py` | Re-export of `src/health.py` | ⚠️ Shim — not directly registered |

### 5.4 DTO Compliance Gaps

**Only 3 routers use DTOs:**
1. `src/routers/dashboard.py` — `DashboardSummaryDTO` ✅
2. `src/routers/cashflow.py` — `CashflowSummaryDTO`, `CashflowCategoryResponse` ✅
3. `src/routers/accounts_router.py` — `AccountsDTO`, `AccountDetailDTO` ✅ (but router is DEAD)

**52 of 115 endpoints (45.2%) return untyped `dict[str, Any]` or `list[dict[str, Any]]`** — no DTO, no mapper, no contract.

### 5.5 Mapper Usage

**Finding:** Zero mappers are used anywhere in the codebase.

**Evidence:** `grep -rn "from src.core.mappers" src/ --include="*.py"` → 0 results

All 5 mapper files are dead code. The Router → Service → Repository → **Mapper** → DTO chain is completely broken.

---

## 6. Backend Freeze Readiness Report

### 6.1 Freeze Blockers (Must Fix Before Program 6)

| # | Issue | Severity | Files | Impact |
|---|---|---|---|---|
| 1 | Dead router `accounts_router.py` imported in `__init__.py` | HIGH | `src/routers/accounts_router.py`, `src/routers/__init__.py` | Import side-effects, confusion |
| 2 | Dead router `financial_intelligence.py` not registered | HIGH | `src/routers/financial_intelligence.py` | 7 endpoints unreachable |
| 3 | Dead service `behavior_service.py` (American spelling) | HIGH | `src/services/behavior_service.py` | Conflicts with `behaviour_service.py` |
| 4 | Dead service `accounts_service.py` | HIGH | `src/services/accounts_service.py` | Only used by dead router |
| 5 | Dead repository `alert_repository.py` | MEDIUM | `src/repositories/alert_repository.py` | Unused code |
| 6 | All 5 mappers dead | HIGH | `src/core/mappers/*.py` | DTO chain broken |
| 7 | `api_common.py` dead | LOW | `src/api_common.py` | Unused re-export |
| 8 | Legacy `behavior_engine.py` still imported by active `dashboard_service.py` | HIGH | `src/engines/behavior_engine.py`, `src/services/dashboard_service.py:7` | Active code depends on legacy |
| 9 | 5 routers bypass service layer | HIGH | `banks.py`, `export.py`, `investments.py`, `members.py`, `import_router.py` | Architecture violation |
| 10 | DB_PATH duplicated in 3 locations | MEDIUM | `common/database.py:16`, `repositories/base.py:12`, `services/base.py:23` | Path drift risk |

### 6.2 Recommended Remediation Execution Order

**Phase 1: Dead Code Removal (Lowest Risk)**
1. Remove `src/routers/accounts_router.py` + remove from `src/routers/__init__.py`
2. Remove `src/services/accounts_service.py` (only consumer was dead router)
3. Remove `src/services/behavior_service.py` (American spelling, 0 refs)
4. Remove `src/repositories/alert_repository.py` + remove from `src/repositories/__init__.py`
5. Remove `src/api_common.py` (0 consumers)
6. Remove all 5 files in `src/core/mappers/` (0 imports)

**Phase 2: Dead Router Registration**
7. Either register `src/routers/financial_intelligence.py` in `api.py` OR remove it
   - If keeping: add `app.include_router(financial_intelligence.router)` to `api.py`
   - If removing: remove from `src/routers/__init__.py`

**Phase 3: Legacy Engine Consolidation**
8. Migrate `src/services/dashboard_service.py:7` from `behavior_engine` to `behaviour_engine`
9. Migrate `src/routers/import_router.py:19` from `behavior_engine` to `behaviour_engine`
10. Remove `src/engines/behavior_engine.py` after migration
11. Remove bridge module `src/engines/behaviour_engine/core.py` bridge imports

**Phase 4: Service Layer Compliance**
12. Create `BankService` → move `banks.py` router to use service
13. Create `ExportService` → move `export.py` router to use service
14. Create `InvestmentService` → move `investments.py` router to use service
15. Create `MemberService` → move `members.py` router to use service
16. Refactor `import_router.py` to use `StatementService` + `TransactionService`

**Phase 5: Database Path Consolidation**
17. Make `src/repositories/base.py:DEFAULT_DB_PATH` the single source of truth
18. Remove `DB_PATH` from `src/common/database.py`
19. Remove `DB_PATH` import from `src/services/financial_intelligence_service.py:11`
20. Remove `src/common/database.py` `get_db()` function (deprecated)

**Phase 6: DTO & Mapper Restoration (Program 6)**
21. Create DTOs for all 52 dict-returning endpoints
22. Implement mappers for each domain
23. Add `response_model=` annotations to all endpoints
24. Verify Router → Service → Repository → Mapper → DTO → Response chain

### 6.3 Freeze Readiness Verdict

| Category | Status | Details |
|---|---|---|
| Database ownership | ⚠️ NOT READY | 3 entry points, DB_PATH duplicated |
| Repository layer | ⚠️ NOT READY | 1 dead repo, 5 routers bypass services |
| Service layer | ⚠️ NOT READY | 2 dead services, 1 legacy engine dependency |
| Router layer | ⚠️ NOT READY | 2 dead routers, 5 bypass service layer |
| DTO compliance | ❌ NOT READY | Only 5/115 endpoints have response_model, 0 mappers used |
| Import hygiene | ⚠️ NOT READY | Legacy bridges, dead re-exports |
| Dead code | ❌ NOT READY | 10+ dead modules identified |

**Overall verdict:** ❌ **NOT READY FOR FREEZE** — 6 phases of remediation required before backend freeze.

### 6.4 Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Dead router import causes side-effect crash | MEDIUM | HIGH | Remove in Phase 1 |
| `behavior_engine.py` removal breaks `dashboard_service.py` | HIGH | HIGH | Migrate in Phase 3 before removal |
| DB_PATH drift between 3 locations | LOW | MEDIUM | Consolidate in Phase 5 |
| Service layer bypass causes inconsistent error handling | MEDIUM | MEDIUM | Fix in Phase 4 |
| DTO absence causes frontend contract breaks | HIGH | HIGH | Address in Program 6 |

---

## Appendix: Evidence Commands

All findings were produced using:
- CGC MCP subagents (5 parallel investigations)
- `grep -rn` for import/usage tracing
- `find` for file inventory
- `wc -l` for endpoint counts

No source files were modified during this audit.

---

**End of Report**