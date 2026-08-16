# Program 5.3 — Backend Architecture Stabilization Audit

**Date:** 2026-08-01  
**Phase:** Program 5.3 — Backend Stabilization & Validation  
**Status:** READ-ONLY — No source files modified, no files moved, no renames performed  
**Audit Method:** CGC MCP tools (find_code, execute_cypher_query, subagent analysis) + grep/rg for literal verification  

---

## Table of Contents

1. [Stage 1 — Ownership Maps](#stage-1--ownership-maps)
2. [Stage 2 — Database Audit](#stage-2--database-audit)
3. [Stage 3 — Endpoint Verification](#stage-3--endpoint-verification)
4. [Stage 4 — Frontend Contract Audit](#stage-4--frontend-contract-audit)
5. [Stage 5 — Database Integrity](#stage-5--database-integrity)
6. [Stage 6 — Modular Database Recovery Design](#stage-6--modular-database-recovery-design)
7. [Stage 7 — Program 5.3 Execution Plan](#stage-7--program-53-execution-plan)

---

## Stage 1 — Ownership Maps

### 1.1 Database

| Question | Answer |
|---|---|
| **Who owns it?** | `src/db.py` — `FinanceDB` class (schema, migrations, path resolution) |
| **Who reads it?** | `src/common/database.py` re-exports `DB_PATH`; `src/repositories/base.py` resolves its own path independently |
| **Who writes it?** | `FinanceDB.__init__()` calls `_create_tables()` → `_run_migrations()` → `_verify_schema()` |
| **Who creates it?** | `FinanceDB()` instantiated in: `conftest.py:46`, `diagnose_db.py`, `api.py` startup; `BaseRepository._get_conn()` creates connections per-call |
| **Who should own it?** | `src/db.py` (schema/migration bootstrap); `src/repositories/base.py` (runtime data access); `src/common/database.py` should be removed |

### 1.2 Configuration

| Question | Answer |
|---|---|
| **Who owns it?** | `src/config.py` — `settings` dataclass (single config object) |
| **Who reads it?** | `src/db.py:791` (`settings._database_path_override`), `src/repositories/base.py:22`, `src/services/base.py:23` |
| **Who writes it?** | `.env` file + runtime env vars set in `conftest.py:40` |
| **Who creates it?** | `settings = _load_settings()` at module import time (lazy env var reading) |
| **Who should own it?** | `src/config.py` (sole owner); `BaseRepository` and `BaseService` should read from `settings`, not duplicate `Path()` resolution |

**Environment variables (from `config.py`):**
`FINANCE_DB_PATH`, `DATABASE_PATH`, `UPLOAD_DIR`, `BACKEND_PORT`, `FRONTEND_PORT`, `NEXT_PUBLIC_API_URL`, `CORS_ORIGINS`

**Path duplication — 3 independent resolutions of the same path:**

| Location | Line | Expression |
|---|---|---|
| `src/common/database.py:16` | `DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")` |
| `src/repositories/base.py:12` | `DEFAULT_DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")` |
| `src/services/base.py:23` | `or os.getenv("FINANCE_DB_PATH")` |

All three fall back to `os.getenv("FINANCE_DB_PATH")`.

### 1.3 Repositories

| Question | Answer |
|---|---|
| **Who owns it?** | `src/repositories/base.py` — `BaseRepository` (base class) |
| **Who reads it?** | All services via `BaseRepository._get_conn()`; `__init__.py` re-exports all 25 repository classes |
| **Who writes it?** | `src/repositories/__init__.py` (exports); individual repo files |
| **Who creates it?** | Services instantiate repository subclasses with `db_path` parameter; 25 repository files in `src/repositories/` |
| **Who should own it?** | `src/repositories/` (canonical); `src/repositories/base.py` should centralize `DB_PATH` resolution |

**Full inventory (26 files):** `base.py`, `account_repository.py`, `account_balance_repository.py`, `account_link_repository.py`, `alert_repository.py`, `bank_repository.py`, `behaviour_repository.py`, `cashflow_repository.py`, `credit_card_repository.py`, `credit_card_statement_repository.py`, `financial_event_repository.py`, `financial_goal_repository.py`, `import_mapping_repository.py`, `institution_repository.py`, `investment_repository.py`, `liquidity_pattern_repository.py`, `loan_payment_repository.py`, `loan_repository.py`, `member_repository.py`, `networth_repository.py`, `pattern_repository.py`, `reconciliation_audit_repository.py`, `reconciliation_repository.py`, `statement_repository.py`, `transaction_classification_repository.py`, `transaction_repository.py`

### 1.4 Services

| Question | Answer |
|---|---|
| **Who owns it?** | `src/services/base.py` — `BaseService` (base class) |
| **Who reads it?** | All registered routers; `src/orchestration/statement_orchestrator.py` |
| **Who writes it?** | 25 service files; `src/services/__init__.py` (exports) |
| **Who creates it?** | Routers instantiate services inline: `service = Service()` per endpoint call |
| **Who should own it?** | `src/services/` (canonical); `BaseService` should inherit `DB_PATH` from `BaseRepository` |

**25 service files:** `account_service.py`, `accounts_service.py`, `audit_service.py`, `base.py`, `behavior_service.py`, `behaviour_service.py`, `behaviour_workspace_service.py`, `cashflow_service.py`, `cashflow_workspace_service.py`, `credit_card_service.py`, `credit_cards_workspace_service.py`, `dashboard_service.py`, `financial_events_service.py`, `financial_intelligence_service.py`, `forecast_service.py`, `investments_workspace_service.py`, `loan_analysis_service.py`, `loan_service.py`, `loan_simulation_service.py`, `loans_workspace_service.py`, `networth_service.py`, `networth_workspace_service.py`, `reconciliation_service.py`, `reconciliation_workspace_service.py`, `statement_service.py`, `transaction_intelligence_service.py`, `transaction_service.py`

### 1.5 Routers

| Question | Answer |
|---|---|
| **Who owns it?** | `src/api.py` — single FastAPI app, all `include_router()` calls at lines 78–103 |
| **Who reads it?** | FastAPI runtime; `src/routers/__init__.py` (imports all 28 router modules) |
| **Who writes it?** | Individual router files; `api.py` registration block |
| **Who creates it?** | Each router file defines `router = APIRouter(...)` and exports it |
| **Who should own it?** | `src/routers/` (canonical); `api.py` is the single registration point |

**28 router files** (26 registered in `api.py`, 2 not registered):

| Router | Registered in `api.py`? | Service Used |
|---|---|---|
| `accounts.py` | ✅ | `AccountService` |
| `accounts_router.py` | ❌ | `AccountsService` |
| `audit.py` | ✅ | `AuditService` |
| `banks.py` | ✅ | ⚠️ None (direct repo) |
| `behaviour.py` | ✅ | `BehaviourService` |
| `behaviour_workspace.py` | ✅ | `BehaviourWorkspaceService` |
| `cards_statements.py` | ✅ | `StatementService` |
| `cashflow.py` | ✅ | `CashflowService` |
| `cashflow_workspace.py` | ✅ | `CashflowWorkspaceService` |
| `credit_cards.py` | ✅ | `CreditCardService` |
| `credit_cards_workspace.py` | ✅ | `CreditCardsWorkspaceService` |
| `dashboard.py` | ✅ | `DashboardService` |
| `export.py` | ✅ | ⚠️ None (direct repo) |
| `financial_events.py` | ✅ | `FinancialEventsService` |
| `financial_intelligence.py` | ❌ | `FinancialIntelligenceService` |
| `forecast.py` | ✅ | `ForecastService` |
| `health.py` | ✅ (via `register_health_routes`) | N/A (operational) |
| `import_router.py` | ✅ | ⚠️ None (direct repo + engine) |
| `investments.py` | ✅ | ⚠️ None (direct repo) |
| `investments_workspace.py` | ✅ | `InvestmentsWorkspaceService` |
| `loans.py` | ✅ | `LoanService`, `LoanAnalysisService`, `LoanSimulationService` |
| `loans_workspace.py` | ✅ | `LoansWorkspaceService` |
| `managed_accounts.py` | ✅ | `AccountService` |
| `members.py` | ✅ | ⚠️ None (direct repo) |
| `networth.py` | ✅ | `NetWorthService` |
| `networth_workspace.py` | ✅ | `NetWorthWorkspaceService` |
| `reconciliation.py` | ✅ | `ReconciliationService` |
| `reconciliation_workspace.py` | ✅ | `ReconciliationWorkspaceService` |
| `transactions.py` | ✅ | `TransactionService` |

### 1.6 DTOs

| Question | Answer |
|---|---|
| **Who owns it?** | `src/core/dtos/` (14 files: 13 DTO modules + `__init__.py`) |
| **Who reads it?** | Only 3 routers: `dashboard.py` (`DashboardSummaryDTO`), `cashflow.py` (`CashflowSummaryDTO`, `CashflowCategoryResponse`), `accounts_router.py` (`AccountsDTO`, `AccountDetailDTO`) |
| **Who writes it?** | DTO author (new layer, not yet wired to most endpoints) |
| **Who creates it?** | Pydantic model classes in each `*_dto.py` file |
| **Who should own it?** | `src/core/dtos/` (canonical) |

**13 DTO modules:** `account_dto.py`, `accounts_dto.py`, `analytics_dto.py`, `behaviour_dto.py`, `cashflow_dto.py`, `credit_cards_dto.py`, `dashboard_dto.py`, `forecast_dto.py`, `investments_dto.py`, `loans_dto.py`, `net_worth_dto.py`, `reconciliation_dto.py`, `statement_dto.py`, `transaction_dto.py`

**Usage gap:** 10 of 13 DTO modules have **0 imports** from routers. Only `dashboard_dto`, `cashflow_dto`, and `accounts_dto` are consumed.

### 1.7 Mappers

| Question | Answer |
|---|---|
| **Who owns it?** | `src/core/mappers/` (5 files + `__init__.py`) |
| **Who reads it?** | **Nobody** — 0 imports anywhere in `src/` or `tests/` |
| **Who writes it?** | Mapper author (new layer, not yet wired) |
| **Who creates it?** | Pydantic model classes in each `*_mapper.py` file |
| **Who should own it?** | `src/core/mappers/` (canonical — but currently dead) |

**5 mappers (all UNWIRED):**
| Mapper File | Intended Purpose | Imports |
|---|---|---|
| `account_mapper.py` | Domain → AccountDTO | 0 |
| `analytics_mapper.py` | Domain → AnalyticsDTO | 0 |
| `dashboard_mapper.py` | Domain → DashboardDTO | 0 |
| `statement_mapper.py` | Domain → StatementDTO | 0 |
| `transaction_mapper.py` | Domain → TransactionDTO | 0 |

**Evidence:** `grep -rn "from src.core.mappers" src/ --include="*.py"` → 0 results

### 1.8 Models

| Question | Answer |
|---|---|
| **Who owns it?** | `src/models/` (22 files + `__init__.py`) — **canonical** |
| **Who reads it?** | Routers (`accounts.py`, `credit_cards.py`, `loans.py`), services, tests |
| **Who writes it?** | Pydantic model definitions |
| **Who creates it?** | Model classes in each `*.py` file |
| **Who should own it?** | `src/models/` (sole location; `src/core/models/` is empty) |

**22 model files:** `account.py`, `account_balance.py`, `account_link.py`, `base.py`, `behaviour.py`, `credit_card.py`, `credit_card_emi.py`, `credit_card_foreclosure.py`, `credit_card_statement.py`, `dashboard.py`, `financial_event.py`, `financial_goal.py`, `institution.py`, `investment.py`, `loan.py`, `loan_analysis.py`, `loan_payment.py`, `loan_simulation.py`, `reconciliation.py`, `statement.py`, `transaction.py`, `__init__.py`

### 1.9 Runtime

| Question | Answer |
|---|---|
| **Who owns it?** | `src/orchestration/statement_orchestrator.py` (orchestration) + `src/runtime/` (runtime verification) + `src/verification/` (capability framework) |
| **Who reads it?** | `api.py` startup; `import_router.py`; test suite (`tests/runtime/`) |
| **Who writes it?** | Orchestration engine, runtime verification framework |
| **Who creates it?** | `StatementProcessingOrchestrator` instantiated in `import_router.py` |
| **Who should own it?** | `src/orchestration/` (orchestration), `src/runtime/` (runtime), `src/verification/` (capability framework) |

---

## Stage 2 — Database Audit

### 2.1 Database Entry Points

**Finding:** No SQLAlchemy. No `create_engine`. No `sessionmaker`. No `Session`. Raw `sqlite3` only.

**Every `sqlite3.connect()` call in `src/`:**

| File | Line | Function | Purpose |
|---|---|---|---|
| `src/db.py` | 808-813 (`_connect()`) | `FinanceDB._connect()` | Schema/migration bootstrap |
| `src/repositories/base.py` | 27 (`_get_conn()`) | `BaseRepository._get_conn()` | All domain data access |
| `src/health.py` | (in `/ready` endpoint) | Runtime health check | Connectivity probe |

**Engine entries:** `src/config.py:34` resolves `FINANCE_DB_PATH` env var → passed to `FinanceDB.__init__` / `BaseRepository.__init__` / `BaseService.__init__`

### 2.2 All 29 Tables (from `src/db.py`)

| # | Table | DDL Line | Paise Columns | FKs |
|---|---|---|---|---|
| 1 | `statements` | 111 | — | — |
| 2 | `transactions` | 124 | `amount_paise` | `statement_id → statements(id)` |
| 3 | `members` | 155 | — | — |
| 4 | `import_mappings` | 164 | — | — |
| 5 | `reconciliations` | 180 | — | — |
| 6 | `accounts` | 200 | `balance_paise` | — |
| 7 | `loans` | 217 | `principal_paise`, `outstanding_paise`, `emi_paise` | — |
| 8 | `investments` | 240 | `buy_price_paise` | — |
| 9 | `loan_payments` | 258 | `amount_paise` | `loan_id → loans(id)` |
| 10 | `loan_prepayments` | 272 | `amount_paise` | `loan_id → loans(id)` |
| 11 | `loan_rate_changes` | 283 | — | `loan_id → loans(id)` |
| 12 | `account_balance_history` | 294 | `balance_paise` | `account_id → accounts(id)` |
| 13 | `account_links` | 307 | — | `account_id → accounts(id)`, `linked_account_id → accounts(id)` |
| 14 | `credit_cards` | 318 | — | `account_id → accounts(id)` |
| 15 | `credit_card_statements` | 337 | — | `card_id → credit_cards(id)` |
| 16 | `institutions` | 353 | — | — |
| 17 | `reconciliation_audit_log` | 365 | — | `reconciliation_id → reconciliations(id) ON DELETE CASCADE` |
| 18 | `behaviour_snapshots` | 379 | — | — |
| 19 | `behaviour_patterns` | 396 | — | — |
| 20 | `behaviour_alerts` | 413 | — | — |
| 21 | `financial_profiles` | 429 | — | — |
| 22 | `financial_events` | 441 | — | — |
| 23 | `financial_goals` | 464 | — | — |
| 24 | `loan_amortization_schedule` | 483 | — | `loan_id → loans(id)` |
| 25 | `transaction_classifications` | 498 | — | `transaction_id → transactions(id)` |
| 26 | `financial_event_lifecycle_log` | 517 | — | `event_id → financial_events(id)` |
| 27 | `financial_event_links` | 531 | — | `event_id → financial_events(id)`, `linked_event_id → financial_events(id)` |
| 28 | `liquidity_provider_patterns` | 541 | — | — |
| 29 | `liquidity_purpose_patterns` | 557 | — | — |

### 2.3 PRAGMA Statements

| File | Line | PRAGMA |
|---|---|---|
| `src/db.py` | 810 | `PRAGMA journal_mode=WAL` |
| `src/db.py` | 811 | `PRAGMA foreign_keys=ON` |
| `src/repositories/base.py` | 30 | `PRAGMA journal_mode=WAL` |
| `src/repositories/base.py` | 31 | `PRAGMA foreign_keys=ON` |
| `src/db.py` | 886 | `PRAGMA table_info(accounts)` (verification) |
| `src/db.py` | 952 | `PRAGMA table_info(accounts)` (verification) |
| `src/db.py` | 985 | `PRAGMA foreign_keys` (check current value) |
| `src/db.py` | 1026 | `PRAGMA foreign_key_check` (integrity check) |

### 2.4 Transactions (commit/rollback)

| File | Line | Operation | Context |
|---|---|---|---|
| `src/db.py` | 864 | `conn.commit()` | After `_create_tables()` |
| `src/db.py` | 973 | `conn.commit()` | After `_run_migrations()` |
| `src/db.py` | 1040 | `conn.commit()` | After `_verify_schema()` |
| `src/db.py` | 1055 | `self._conn.commit()` | In `__exit__()` (normal path) |
| `src/db.py` | 1057 | `self._conn.rollback()` | In `__exit__()` (exception path) |

**Finding:** BaseRepository has **no transaction management** — connections are opened and closed per-call with no explicit `commit()`. Write operations in repositories call `conn.commit()` individually (verified via subagent grep across `src/repositories/`).

### 2.5 Cursor Usage

All data access in `BaseRepository._get_conn()` returns a raw `sqlite3.Connection`. Repositories use `conn.execute(...)` directly — **no cursor abstraction layer**. The pattern is:

```python
with self._get_conn() as conn:
    cur = conn.execute("SELECT ...", params)
    rows = cur.fetchall()
```

### 2.6 Paise Convention

**Verified:** All monetary columns use `INTEGER` with `_paise` suffix.

| Column | Table | Line |
|---|---|---|
| `amount_paise` | `transactions` | 130 |
| `balance_paise` | `accounts` | 205 |
| `principal_paise` | `loans` | 222 |
| `outstanding_paise` | `loans` | 223 |
| `emi_paise` | `loans` | 226 |
| `buy_price_paise` | `investments` | 245 |
| `amount_paise` | `reconciliations` | 186 |
| `confidence_bps` | `reconciliations` | 188 |

**Stored generated columns:** `credit` and `debit` in `transactions` (lines 148–149) are `INTEGER GENERATED ALWAYS AS (...) STORED` — derived from `amount_paise`.

### 2.7 Foreign Keys

**17 FOREIGN KEY REFERENCES found across DDL:**

Only **1** has cascade behavior:
- `reconciliation_audit_log.reconciliation_id → reconciliations(id) ON DELETE CASCADE` (line 374)

All other FKs have no explicit `ON DELETE` / `ON UPDATE` action — default is `NO ACTION`.

### 2.8 Indexes

**15 CREATE INDEX statements** (lines 571–584 in `src/db.py`):

| Line | Index | Table | Column(s) |
|---|---|---|---|
| 571 | `idx_txn_date` | transactions | date |
| 572 | `idx_txn_category` | transactions | category |
| 573 | `idx_txn_statement` | transactions | statement_id |
| 574 | `idx_txn_type` | transactions | type |
| 575 | `idx_txn_date_iso` | transactions | date_iso |
| 576 | `idx_account_date_iso` | transactions | account_id, date_iso, id |
| 577 | `idx_transaction_hash` (UNIQUE) | transactions | hash_signature |
| 578 | `idx_loan_payments_loan_id` | loan_payments | loan_id |
| 579 | `idx_loan_payments_date` | loan_payments | payment_date |
| 580 | `idx_loan_prepayments_loan_id` | loan_prepayments | loan_id |
| 581 | `idx_loan_prepayments_date` | loan_prepayments | prepayment_date |
| 582 | `idx_loan_rate_changes_loan_id` | loan_rate_changes | loan_id |
| 583 | `idx_loan_rate_changes_date` | loan_rate_changes | change_date |
| 584 | `idx_loan_payments_loan_date` | loan_payments | loan_id, payment_date |

### 2.9 UNIQUE Constraints (inline)

| Line | Constraint | Table |
|---|---|---|
| 119 | `UNIQUE(bank, file_name)` | import_mappings |
| 150 | `UNIQUE(statement_id, date, description, amount_paise, sequence_num)` | transactions |
| 157 | `name TEXT NOT NULL UNIQUE` | institutions |
| 191 | `deterministic_key TEXT NOT NULL UNIQUE` | reconciliations |
| 302 | `UNIQUE(account_id, date_iso)` | account_balance_history |
| 313 | `UNIQUE(account_id, linked_account_id)` | account_links |
| 348 | `UNIQUE(card_id, statement_date)` | credit_card_statements |
| 391 | `UNIQUE(household_id, snapshot_date)` | behaviour_snapshots |
| 408 | `UNIQUE(pattern_type, pattern_key, household_id)` | behaviour_patterns |
| 436 | `UNIQUE(household_id, profile_type)` | financial_profiles |
| 459 | `UNIQUE(event_type, date_iso, amount_paise, description)` | financial_events |
| 493 | `UNIQUE(loan_id, due_date)` | loan_amortization_schedule |
| 512 | `UNIQUE(transaction_id, classification)` | transaction_classifications |

### 2.10 Migration Scripts

| Script | Path | What it touches |
|---|---|---|
| migration_002 | `backend/scripts/migration_002_loan_engine.py` | `loans`, `loan_payments`, `loan_prepayments`, `loan_rate_changes` |
| migration_003 | `backend/scripts/migration_003_credit_card_engine.py` | `credit_cards`, `credit_card_statements`, `credit_card_emi` |
| migration_004 | `backend/scripts/migration_004_account_engine.py` | `accounts`, `account_balance_history`, `account_links` |
| migration_005 | `backend/scripts/migration_005_behaviour_engine.py` | `behaviour_snapshots`, `behaviour_patterns`, `behaviour_alerts` |
| migration_006 | `backend/scripts/migration_006_household.py` | `financial_profiles`, `liquidity_provider_patterns`, `liquidity_purpose_patterns` |
| migration_007 | `backend/scripts/migration_007_reconciliation_audit.py` | `reconciliation_audit_log` |

### 2.11 Database Dependency Graph

```
┌─────────────────────────────────────────────────────┐
│                    src/config.py                     │
│  (settings: env vars, DB_PATH resolution)            │
└──────────┬────────────────────────────┬─────────────┘
           │                            │
           ▼                            ▼
┌──────────────────┐    ┌──────────────────────────┐
│   src/db.py      │    │ src/common/database.py   │
│ (FinanceDB)      │    │ (LEGACY COMPAT)          │
│  - _create_tables│    │  - DB_PATH (duplicated)  │
│  - _run_migrations│   │  - get_db() (deprecated) │
│  - _verify_schema │   │  - imports FinanceDB     │
│  - _connect()     │   └──────────┬───────────────┘
│  - __enter__/__exit__│            │
└─────────┬────────┘               │
          │                        │
          ▼                        ▼
┌──────────────────────────────────────────────┐
│   src/repositories/base.py (BaseRepository)  │
│   (Canonical data access layer)              │
│   - _get_conn() → sqlite3.connect            │
│   - DEFAULT_DB_PATH (duplicated)             │
│   - PRAGMA journal_mode=WAL                  │
│   - PRAGMA foreign_keys=ON                   │
└──────────┬───────────────────┬──────────────┘
           │                   │
           ▼                   ▼
  ┌──────────────────┐  ┌──────────────────┐
  │  25 Repository   │  │  src/health.py    │
  │  subclasses      │  │  /ready endpoint  │
  └──────────────────┘  └──────────────────┘
```

**Dependency violations:**
- `src/common/database.py:9` imports `FinanceDB` from `src.db` — **allowed** (it's a thin wrapper in `common/`, not a router/engine) but redundant since `BaseRepository` handles connections independently
- `src/services/financial_intelligence_service.py:11` imports `DB_PATH` from `src.common` — **duplication** of path resolution logic that already exists in `BaseRepository`

---

## Stage 3 — Endpoint Verification

### 3.1 Endpoint Inventory

| Metric | Count |
|---|---|
| Total router files (excluding `__init__.py`) | 28 |
| Registered in `api.py` | 26 |
| Not registered (dead/unregistered) | 2 |
| Total endpoints (`@router.get/post/put/patch/delete`) | 115 |

### 3.2 Router → Service → Repository → Database Chain

#### Routers WITH proper service layer: 21 routers

| Router | Service | Repository(ies) | DB Access |
|---|---|---|---|
| `accounts.py` | `AccountService` | `AccountRepository`, `AccountBalanceRepository`, `AccountLinkRepository` | `BaseRepository._get_conn()` |
| `audit.py` | `AuditService` | `ledger_audit_engine` → (engine-level DB access) | `FinanceDB` context manager |
| `behaviour.py` | `BehaviourService` | `AccountRepository`, `BehaviourRepository`, `CreditCardRepository` | `BaseRepository._get_conn()` |
| `behaviour_workspace.py` | `BehaviourWorkspaceService` | `CreditCardRepository`, `LoanRepository` | `BaseRepository._get_conn()` |
| `cards_statements.py` | `StatementService` | `StatementRepository` | `BaseRepository._get_conn()` |
| `cashflow.py` | `CashflowService` | `CashflowRepository`, `TransactionRepository` | `BaseRepository._get_conn()` |
| `cashflow_workspace.py` | `CashflowWorkspaceService` | (wraps `CashflowService`) | Indirect |
| `credit_cards.py` | `CreditCardService` | `CreditCardRepository`, `CreditCardStatementRepository` | `BaseRepository._get_conn()` |
| `credit_cards_workspace.py` | `CreditCardsWorkspaceService` | `CreditCardRepository`, `CreditCardStatementRepository` | `BaseRepository._get_conn()` |
| `dashboard.py` | `DashboardService` | `ReconciliationRepository`, `TransactionRepository` | `BaseRepository._get_conn()` |
| `financial_events.py` | `FinancialEventsService` | `FinancialEventRepository` | `BaseRepository._get_conn()` |
| `forecast.py` | `ForecastService` | `CreditCardRepository`, `InvestmentRepository`, `LoanRepository` | `BaseRepository._get_conn()` |
| `investments_workspace.py` | `InvestmentsWorkspaceService` | `InvestmentRepository` | `BaseRepository._get_conn()` |
| `loans.py` | `LoanService` + `LoanAnalysisService` + `LoanSimulationService` | `LoanRepository`, `LoanPaymentRepository` | `BaseRepository._get_conn()` |
| `loans_workspace.py` | `LoansWorkspaceService` | `LoanRepository` | `BaseRepository._get_conn()` |
| `managed_accounts.py` | `AccountService` | `AccountRepository` | `BaseRepository._get_conn()` |
| `networth.py` | `NetWorthService` | `NetWorthRepository` | `BaseRepository._get_conn()` |
| `networth_workspace.py` | `NetWorthWorkspaceService` | `AccountRepository`, `CreditCardStatementRepository`, `InvestmentRepository` | `BaseRepository._get_conn()` |
| `reconciliation.py` | `ReconciliationService` | `ReconciliationRepository` | `BaseRepository._get_conn()` |
| `reconciliation_workspace.py` | `ReconciliationWorkspaceService` | `ReconciliationRepository` | `BaseRepository._get_conn()` |
| `transactions.py` | `TransactionService` | `TransactionRepository` | `BaseRepository._get_conn()` |

#### Routers BYPASSING service layer: 5 routers ⚠️

| Router | Direct Repository Import | Service Bypassed |
|---|---|---|
| `src/routers/banks.py:5` | `BankRepository` | `BankService` (does not exist) |
| `src/routers/export.py:9` | `TransactionRepository` | `ExportService` (does not exist) |
| `src/routers/investments.py:9` | `InvestmentRepository` | `InvestmentsService` (singular does not exist) |
| `src/routers/members.py:8` | `MemberRepository` | `MemberService` (does not exist) |
| `src/routers/import_router.py:15` | `StatementRepository`, `TransactionRepository` | `ImportService` / `StatementService` (partial bypass) |

**Additional bypass:** `src/routers/import_router.py:19` imports `behavior_engine` directly — bypassing the service layer for cache invalidation.

### 3.3 Service → Repository Chain (no bypasses)

**Finding:** All active services use repository classes for data access. No services perform raw SQL directly.

**Evidence:** `grep -rln "import sqlite3\|sqlite3.connect" src/services/` → 0 results

### 3.4 Repository → Database Chain (no bypasses)

**Finding:** All repositories use `BaseRepository._get_conn()` — no direct `sqlite3.connect()` calls outside the base layer.

### 3.5 DTO Compliance

**5 endpoints with `response_model=`:**

| File | Line | Endpoint | response_model |
|---|---|---|---|
| `src/routers/dashboard.py:11` | `/summary` | `DashboardSummaryDTO` |
| `src/routers/financial_events.py:12` | `POST /` | `int` |
| `src/routers/financial_events.py:59` | `GET /` | `list` |
| `src/routers/financial_events.py:79` | `/{event_id}` | `dict` |
| `src/routers/transactions.py:12` | `/transactions` | `list[dict[str, Any]]` |

**Return type distribution (115 endpoints):**

| Return Type | Count | DTO-compliant? |
|---|---|---|
| `dict[str, Any]` | 42 | ❌ |
| `list[dict[str, Any]]` | 10 | ❌ |
| `dict[str, int]` | 3 | ❌ |
| `dict[str, str]` | 2 | ❌ |
| `list[str]` | 1 | ❌ |
| Typed DTOs | 5 | ✅ |
| **Total untyped (dict/list)** | **58** | ❌ |
| **Total typed** | **5** | ✅ |
| **No return annotation** | **52** | ❌ |

**Finding:** 3 routers import Pydantic models from `src/models/` instead of using DTOs:
- `src/routers/accounts.py:17-28` — `AccountCreateRequest`, `AccountLinkRequest`, `AccountLinkResponse`, `InstitutionInfo`
- `src/routers/credit_cards.py:16-23` — `EmiConversionRequest`, `EmiConversionResponse`, `ForeclosureRequest`, `ForeclosureResponse`
- `src/routers/loans.py:13-20` — `LoanCreateRequest`, `LoanUpdateRequest`, `LoanPaymentCreate`, loan simulation models

### 3.6 Mapper Usage

**Finding:** All 5 mappers are completely unwired.

**Evidence:** `grep -rn "from src.core.mappers" src/ --include="*.py"` → **0 results**

**Impact:** The Router → Service → Repository → **Mapper** → DTO chain is broken for all endpoints. Even the 3 routers using DTOs do so by manually constructing response dicts (e.g., `CashflowSummaryDTO` built manually in `cashflow_service.py`, not via a mapper).

---

## Stage 4 — Frontend Contract Audit

### 4.1 OpenAPI Schema Generation

**Finding:** FastAPI uses **default OpenAPI schema generation**. No custom `openapi` override in `api.py`.

**Evidence:** `grep -nE "openapi|schema|docs" src/api.py` → only `API Docs: http://localhost:8000/docs` (comment at line 9)

FastAPI generates the OpenAPI schema automatically from:
- Route paths
- Pydantic response_model (if declared)
- Pydantic request body models

### 4.2 Contract Gaps

| Gap | Count | Impact |
|---|---|---|
| Endpoints without `response_model=` | 110 of 115 | OpenAPI schema shows `unknown` response type |
| Endpoints returning `dict[str, Any]` | 42 | OpenAPI shows `object` — no field contracts |
| Endpoints returning `list[dict[str, Any]]` | 10 | OpenAPI shows `array[object]` — no item schema |
| Endpoints returning untyped (inferred) | 52 | OpenAPI schema depends on runtime Pydantic model inference |
| Mappers not used | 5/5 | No consistent DTO↔domain mapping → contract drift risk |
| DTOs imported by routers | 3 of 13 DTO modules | 10 DTO modules have no consumers → dead contracts |

### 4.3 Frontend Contract Verification

**Frontend contract artifacts found:**
- `frontend/api-schema.json` — OpenAPI-derived schema (auto-generated)
- `frontend/__tests__/api-contracts/` — contract test directory

**Contract risks:**

1. **`dict[str, Any]` responses (42 endpoints):** Frontend receives untyped objects — any field name change in router/service breaks frontend silently. OpenAPI shows `{[key: str]: any}`.

2. **Missing `response_model` (110 endpoints):** FastAPI cannot auto-generate response schemas. Frontend `api-schema.json` likely has placeholder/empty schemas for these endpoints.

3. **`src/models` used as response models (3 routers):** `AccountCreateRequest`, `EmiConversionRequest`, etc. from `src/models/` are used directly in router signatures. These are Pydantic models, so FastAPI DOES generate schemas — but they mix request and response semantics, creating tight coupling.

4. **Dead routers with DTOs (`accounts_router.py`):** This router is the ONLY router using `AccountsDTO` and `AccountDetailDTO` — but it's not registered in `api.py`. These DTOs exist in the OpenAPI contract but are unreachable.

5. **No mapper verification:** Mappers would enforce stable field-by-field mapping. Without them, domain model field changes propagate directly to responses.

### 4.4 Stable Contract Assessment

| Endpoint Group | Contract Stable? | Reason |
|---|---|---|
| `dashboard.py` (`/summary`) | ❌ | Uses `DashboardSummaryDTO` but built manually (no mapper) |
| `cashflow.py` | ❌ | Uses `CashflowSummaryDTO` but no `response_model` annotation |
| `accounts.py` | ❌ | Uses `src/models` directly, returns `dict[str, Any]` |
| `credit_cards.py` | ❌ | Uses `src/models` directly, returns `dict[str, Any]` |
| `loans.py` | ❌ | Uses `src/models` directly, returns `dict[str, Any]` |
| All other endpoints | ❌ | Return `dict[str, Any]` or untyped |
| `financial_events.py` | ⚠️ Partial | Has `response_model` but uses `int`/`list`/`dict` (generic types, not typed DTOs) |
| `transactions.py` | ⚠️ Partial | Has `response_model=list[dict[str, Any]]` (typed as dict, not DTO) |

**Overall:** No endpoint has a stable, mapper-enforced DTO contract. The frontend contract is **entirely unstable** for production use.

---

## Stage 5 — Database Integrity

### 5.1 Foreign Key Integrity

**Status:** FK enforcement enabled via `PRAGMA foreign_keys=ON` (in both `db.py:811` and `base.py:31`)

| Check | Status | Evidence |
|---|---|---|
| FK enforcement enabled | ✅ Yes | `PRAGMA foreign_keys=ON` at `db.py:811`, `base.py:31` |
| FK verification | ✅ Yes | `_verify_schema()` at `db.py:975-988` checks `PRAGMA foreign_keys` and `PRAGMA foreign_key_check` |
| FK violations check | ✅ Yes | `db.py:1026` — `PRAGMA foreign_key_check` |
| CASCADE rules | ⚠️ Partial | Only 1 of 17 FKs has `ON DELETE CASCADE` (`reconciliation_audit_log`) |
| FK consistency | ⚠️ Partial | Some FK columns use `INTEGER` (e.g., `loan_id INTEGER NOT NULL REFERENCES loans(id)`) while parent PKs are `INTEGER PRIMARY KEY AUTOINCREMENT` — OK. But some FKs reference `TEXT` columns (e.g., `credit_cards.account_id TEXT REFERENCES accounts(id)` where `accounts.id` is `INTEGER PRIMARY KEY`) — **type mismatch** |

### 5.2 Index Integrity

| Check | Status | Details |
|---|---|---|
| Transaction indexes | ✅ Yes | 7 indexes on `transactions` (date, category, statement_id, type, date_iso, composite, hash) |
| Loan indexes | ✅ Yes | 6 indexes on loan tables (payments, prepayments, rate_changes, amortization) |
| Missing indexes | ⚠️ | No indexes on `accounts`, `credit_cards`, `investments`, `financial_events`, `loans` (base table) |
| Unique constraint index | ✅ Yes | `idx_transaction_hash` protects against duplicate imports |

### 5.3 Unique Constraints

**13 inline UNIQUE constraints** verified (see Stage 2.9 table). Notable:
- `transactions`: `UNIQUE(statement_id, date, description, amount_paise, sequence_num)` — prevents duplicate transaction imports
- `transaction_classifications`: `UNIQUE(transaction_id, classification)` — prevents duplicate classifications

### 5.4 Money Storage (Paise Convention)

**Status:** ✅ **Verified correct**

All monetary columns use `INTEGER` with `_paise` suffix:
- `amount_paise`, `balance_paise`, `principal_paise`, `outstanding_paise`, `emi_paise`, `buy_price_paise`, `confidence_bps`
- Stored generated columns `credit` and `debit` derive from `amount_paise` (lines 148–149)
- `_parse_amount_paise()` at `src/db.py:680` handles conversion from CSV input

### 5.5 NULL Handling

**Status:** ⚠️ Inconsistent

| Column | Table | NULL? | Pattern |
|---|---|---|---|
| `description` | transactions | nullable (no NOT NULL) | Optional field — OK |
| `category` | transactions | nullable | Optional — OK |
| `loan_id` | credit_card_statements | **nullable FK** | ⚠️ Should be NOT NULL |
| `credit_card_id` | credit_card_statements | nullable | ⚠️ Optional link |
| `recurring_id` | transactions | nullable | OK (optional) |
| `is_transfer` | transactions | `DEFAULT 0` (nullable) | ⚠️ Should be NOT NULL |

**Finding:** Several FK columns are nullable where they should require a parent record. This can lead to orphaned rows.

### 5.6 Transaction Management

| Layer | commit() | rollback() | Pattern |
|---|---|---|---|
| `FinanceDB.__exit__` | ✅ Line 1055 | ✅ Line 1057 | Context manager (schema ops) |
| `BaseRepository` | ⚠️ Per-method | ❌ None | Each CRUD method calls `conn.commit()` independently |
| `_create_tables` | ✅ Line 864 | — | Single transaction |
| `_run_migrations` | ✅ Line 973 | — | Single transaction |
| `_verify_schema` | ✅ Line 1040 | — | Single transaction |

**Finding:** No transaction grouping in `BaseRepository`. Each repository method opens a connection, executes, and commits independently. Multi-step operations (e.g., transfer between accounts) are **not atomic** at the repository layer — atomicity depends on `FinanceDB.__enter__/__exit__` context manager wrapping.

### 5.7 Migration Consistency

| Check | Status | Details |
|---|---|---|
| Migration scripts exist | ✅ Yes | 7 scripts in `backend/scripts/` (migration_002–007) |
| Migration execution | ✅ Yes | `FinanceDB._run_migrations()` at `db.py:866` |
| Migration idempotency | ✅ Yes | Scripts use `INSERT OR IGNORE` / `CREATE TABLE IF NOT EXISTS` patterns |
| Migration gap (001) | ⚠️ | No `migration_001_` — likely the initial schema is inline in `_create_tables()` |
| `_verify_schema()` | ✅ Yes | Checks table existence and column structure at `db.py:975` |

### 5.8 Repository Assumptions

| Repository | Table(s) Accessed | Assumed Schema |
|---|---|---|
| `TransactionRepository` | `transactions` | `amount_paise INTEGER NOT NULL` — ✅ matches paise convention |
| `AccountRepository` | `accounts` | `balance_paise INTEGER NOT NULL DEFAULT 0` — ✅ |
| `LoanRepository` | `loans` | `principal_paise`, `outstanding_paise`, `emi_paise` — ✅ |
| `CreditCardRepository` | `credit_cards` | References `accounts(id)` as `TEXT` — ⚠️ type mismatch |

---

## Stage 6 — Modular Database Recovery Design

### 6.1 Current State Analysis

**FinanceDB methods (`src/db.py:769`):**

| Method | Visibility | Responsibility |
|---|---|---|
| `__init__(self, db_path=None)` | Public | Path resolution, schema+data init |
| `__enter__(self)` | Public | Context manager — opens connection |
| `__exit__(...)` | Public | Commits/rolls back, closes connection |
| `_connect(self)` | Private | Creates `sqlite3.connect()` with PRAGMAs |
| `_create_tables(self)` | Private | DDL — 29 tables via `_ALL_DDL_TABLES` |
| `_run_migrations(self)` | Private | Executes 7 migration scripts |
| `_verify_schema(self)` | Private | PRAGMA checks for integrity |
| `_get_conn(self)` | Private | Alternative connection factory (lines 1062+) |
| `_parse_date_to_ymd()` | Module | Date parsing utility |
| `_parse_amount_paise()` | Module | Paise conversion utility |
| `_row_to_dict()` | Module | Row-to-dict converter |
| `_ALL_DDL_TABLES` | Module | 29 CREATE TABLE statements |
| `_DDL_INDEXES` | Module | 15 CREATE INDEX statements |
| `_DDL_TRIGGERS` | Module | 2 triggers (transaction immutability) |

**BaseRepository methods (`src/repositories/base.py:15`):**

| Method | Visibility | Responsibility |
|---|---|---|
| `__init__(self, db_path=None)` | Public | Path resolution (`DEFAULT_DB_PATH`) |
| `_get_conn(self)` | Protected | Creates `sqlite3.connect()` with PRAGMAs, returns context manager |
| `_execute(self, query, params)` | Protected | Query execution abstraction |
| `_fetch_one(self, query, params)` | Protected | Single-row fetch |
| `_fetch_all(self, query, params)` | Protected | Multi-row fetch |

**Note:** `BaseRepository` and `FinanceDB` **both** implement `_get_conn()`/`_connect()` independently with identical PRAGMA setup — duplicated logic.

### 6.2 FinanceDB Instantiation Sites

| Site | File | Purpose |
|---|---|---|
| `tests/conftest.py:46` | `db = FinanceDB(db_path=str(db_path))` | Test fixture (per-test DB) |
| `src/api.py` | (startup event) | Production DB initialization |
| `src/diagnose_db.py` | (script) | Development diagnostics |
| `backend/scripts/migration_*.py` | (7 scripts) | Migration runners |
| `src/engines/behaviour_engine/core.py` | (indirect via FinanceDB context) | Engine-level schema access |

### 6.3 Proposed Modular Architecture (Design Only — No Implementation)

```
src/db/                          # NEW package (replaces src/db.py)
├── __init__.py                 # Public API exports
├── config.py                   # ← owns DB_PATH, FINANCE_DB_PATH, all path logic
├── connection.py               # ← sqlite3.connect() + PRAGMA setup (canonical _get_conn)
├── session.py                  # ← Connection context manager (replaces FinanceDB.__enter__/__exit__)
├── transactions.py             # ← Transaction context manager (BEGIN/COMMIT/ROLLBACK)
├── bootstrap.py                # ← Database creation if not exists
├── schema.py                   # ← All 29 CREATE TABLE DDL + 15 indexes + 2 triggers
├── migration.py                # ← _run_migrations() — executes migration_002–007
├── health.py                   # ← Connection health check (replaces src/health.py)
├── verify.py                   # ← _verify_schema() — PRAGMA integrity checks
├── compatibility.py            # ← Legacy get_db() and DB_PATH re-exports (deprecated)
└── _legacy.py                  # ← FinanceDB backward-compat wrapper (temporary)
```

### 6.4 Dependency Graph (Proposed)

```
┌─────────────────────────────────────────────┐
│  src/config.py  (settings)                  │
│  ┌──► src/db/config.py                       │
└─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────┐
│  src/db/config.py                           │
│  (DB_PATH, FINANCE_DB_PATH)                 │
└──────────┬──────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────┐
│  src/db/connection.py                       │
│  (_get_conn — canonical connect+PRAGMA)     │
├────────────┬─────────────┬──────────────────┤
│            │             │                  │
▼            ▼             ▼                  ▼
src/db/      src/db/      src/db/            src/db/
session.py   transactions.py  bootstrap.py   schema.py
▲            ▲             │                  │
│            │             ├──► migration.py  │
│            │             │                  │
│            │             └──► verify.py     │
│            │                               │
│            │                               │
│            ▼                               │
│  src/db/compatibility.py                   │
│  (legacy get_db(), DB_PATH re-export)       │
│                                             │
│  src/db/_legacy.py                          │
│  (FinanceDB backward-compat wrapper)        │
└─────────────────────────────────────────────┘

Consumers:
  src/repositories/base.py  → imports _get_conn from src/db/connection.py
  src/api.py  → imports bootstrap + health from src/db/
  src/health.py  → import health from src/db/health.py (or deprecate)
  tests/conftest.py  → uses src/db/bootstrap + src/db/config
```

### 6.5 Module Responsibilities (Design Spec)

| Module | Owns | Reads | Writes | Creates | Should Own |
|---|---|---|---|---|---|
| `db/config.py` | `DB_PATH`, `FINANCE_DB_PATH` | `os.environ` | — | `settings` | Single source of DB path |
| `db/connection.py` | `sqlite3.connect()` + PRAGMAs | `db/config.py` | — | `Connection` | Canonical `_get_conn` — replaces 3 duplicates |
| `db/session.py` | Context manager lifecycle | `db/connection.py` | `commit/rollback` | Session | Replace `FinanceDB.__enter__/__exit__` |
| `db/transactions.py` | Transaction boundaries | `db/session.py` | `BEGIN/COMMIT/ROLLBACK` | Transaction | Per-call atomicity |
| `db/bootstrap.py` | DB initialization | `db/connection.py`, `db/schema.py` | `_create_tables` | Initial DB | First-run DB creation |
| `db/schema.py` | 29 CREATE TABLE, 15 indexes, 2 triggers | — | DDL | Tables | Replace inline DDL in `db.py` |
| `db/migration.py` | Migration execution | `db/schema.py`, `db/connection.py` | Schema changes | Migrations | Replace `_run_migrations()` |
| `db/health.py` | Health check | `db/connection.py` | — | Probe | Replace `src/health.py` connectivity |
| `db/verify.py` | Schema verification | `PRAGMA table_info`, `PRAGMA foreign_key_check` | — | Report | Replace `_verify_schema()` |
| `db/compatibility.py` | Legacy `get_db()`, `DB_PATH` | `db/config.py` | — | — | DEPRECATED — mark for removal |
| `db/_legacy.py` | `FinanceDB` wrapper | All above | — | — | TEMPORARY — remove after migration |

---

## Stage 7 — Program 5.3 Execution Plan

The following phases are ordered by **risk** (lowest first). Each task includes: Reason, Risk, Files Affected, Dependencies, Rollback Difficulty, Estimated Complexity.

### Phase 1: Dead Code Removal (Lowest Risk)

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 1.1 | Remove `accounts_service.py` | SUPERSEDED by `account_service.py`; only consumer (`accounts_router.py`) is also dead | LOW | Delete `src/services/accounts_service.py`; remove from `src/services/__init__.py` | Must remove `accounts_router.py` first (Phase 1.2) | Easy — `git checkout` | 1 |
| 1.2 | Remove `accounts_router.py` | INCOMPLETE — never registered in `api.py`; collides with active `accounts.py` routes | LOW | Delete `src/routers/accounts_router.py`; remove from `src/routers/__init__.py` | None | Easy — `git checkout` | 1 |
| 1.3 | Remove `api_common.py` | LEGACY COMPATIBILITY — re-exports `DB_PATH` with 0 consumers | LOW | Delete `src/api_common.py` | None | Easy — `git checkout` | 1 |
| 1.4 | Remove `behavior_service.py` | SUPERSEDED — American spelling duplicate; 0 production refs | LOW | Delete `src/services/behavior_service.py`; remove from `src/services/__init__.py` | None | Easy — `git checkout` | 1 |

**Phase 1 Rollback:** Easy — all deletions can be restored via `git checkout -- <file>`.

### Phase 2: Router Registration Decision

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 2.1 | Register `financial_intelligence.py` in `api.py` | INCOMPLETE — service is active (used by orchestrator); router was never registered | MEDIUM | Add `app.include_router(financial_intelligence.router)` to `src/api.py`; add to `src/routers/__init__.py` | Verify all 7 endpoints have proper service wiring | Easy — remove line from `api.py` | 2 |
| 2.2 | OR: Remove `financial_intelligence.py` | If endpoints are not part of current roadmap | MEDIUM | Same as reverse of 2.1 | Confirm no frontend depends on these endpoints | Easy — `git checkout` | 2 |

**Decision required before Phase 2:** Determine whether `financial_intelligence` endpoints are part of the Program 6 roadmap. Evidence: `tests/capability/forecasting/test_capability.py` imports `financial_intelligence` engine — suggests it IS intended for production.

### Phase 3: Legacy Engine Consolidation

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 3.1 | Migrate `dashboard_service.py:7` from `behavior_engine` to `behaviour_engine` | Active code depends on legacy engine; `behaviour_engine` package is the current architecture | HIGH | `src/services/dashboard_service.py` — change import + call sites | Verify `behaviour_engine` package exposes equivalent functions | Medium — restore old import | 3 |
| 3.2 | Migrate `import_router.py:19` from `behavior_engine` to `behaviour_engine` | Router bypasses service + uses legacy engine | MEDIUM | `src/routers/import_router.py` — change import | `behaviour_engine` exposes `invalidate_cache` | Easy — restore import | 2 |
| 3.3 | Remove `behavior_engine.py` | SUPERSEDED by `behaviour_engine/` package after migration | MEDIUM | Delete `src/engines/behavior_engine.py` | Phases 3.1, 3.2 must be complete | Medium — `git checkout` | 2 |
| 3.4 | Update `behaviour_engine/core.py` bridge | Remove legacy imports after `behavior_engine.py` removal | LOW | `src/engines/behaviour_engine/core.py` | Phase 3.3 | Easy — `git checkout` | 2 |

### Phase 4: Service Layer Compliance

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 4.1 | Create `BankService` class | `banks.py` router bypasses service layer with direct `BankRepository` access | MEDIUM | New: `src/services/bank_service.py`; modify: `src/services/__init__.py`, `src/routers/banks.py` | None | Easy — `git checkout` new file, restore router import | 3 |
| 4.2 | Create `ExportService` class | `export.py` router bypasses service layer with direct `TransactionRepository` access | MEDIUM | New: `src/services/export_service.py`; modify: `src/services/__init__.py`, `src/routers/export.py` | None | Easy | 3 |
| 4.3 | Create `InvestmentService` class | `investments.py` router bypasses service layer with direct `InvestmentRepository` access | MEDIUM | New: `src/services/investment_service.py`; modify: `src/services/__init__.py`, `src/routers/investments.py` | None | Easy | 3 |
| 4.4 | Create `MemberService` class | `members.py` router bypasses service layer with direct `MemberRepository` access | MEDIUM | New: `src/services/member_service.py`; modify: `src/services/__init__.py`, `src/routers/members.py` | None | Easy | 3 |
| 4.5 | Refactor `import_router.py` to use services | Router bypasses service layer + imports legacy engine directly | HIGH | Modify: `src/routers/import_router.py` — route repo/engine access through services | Phases 3.2, 4.1–4.4 patterns | Medium | 4 |

### Phase 5: Database Path Consolidation

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 5.1 | Centralize `DB_PATH` in `BaseRepository` | Path resolution duplicated in 3 locations (`common/database.py:16`, `base.py:12`, `services/base.py:23`) | MEDIUM | `src/repositories/base.py` (source of truth); update `src/services/financial_intelligence_service.py:11` to use `BaseRepository.DEFAULT_DB_PATH` | None | Easy — `git checkout` | 2 |
| 5.2 | Remove `DB_PATH` from `src/common/database.py` | Legacy compatibility shim | MEDIUM | `src/common/database.py` | Phase 5.1 | Easy | 2 |
| 5.3 | Remove `get_db()` from `src/common/database.py` | Deprecated function with 0 production consumers | LOW | `src/common/database.py` | Phase 5.2 | Easy | 1 |

### Phase 6: DTO & Mapper Restoration (Program 6)

| # | Task | Reason | Risk | Files Affected | Dependencies | Rollback | Complexity |
|---|---|---|---|---|---|---|---|
| 6.1 | Implement all 5 mappers | All mappers are dead code; DTOs exist but have no mapping layer | HIGH | Implement: `account_mapper.py`, `analytics_mapper.py`, `dashboard_mapper.py`, `statement_mapper.py`, `transaction_mapper.py` | Requires complete DTO definitions | Medium | 4 |
| 6.2 | Add `response_model=` to all 110 untyped endpoints | OpenAPI contract instability; frontend cannot rely on schemas | HIGH | All 26 active router files | Phase 4 (service layer) + Phase 6.1 (mappers) | Medium — remove annotations | 5 |
| 6.3 | Migrate 3 routers from `src/models` to `src/core/dtos` | `accounts.py`, `credit_cards.py`, `loans.py` use domain models as response types instead of DTOs | MEDIUM | `src/routers/accounts.py`, `src/routers/credit_cards.py`, `src/routers/loans.py` | Phase 6.1, 6.2 | Medium | 3 |

### 7.1 Module Classification Reference

| Module | Classification | Replaces/Replaced By | Roadmap Status |
|---|---|---|---|
| `behavior_service.py` | SUPERSEDED | `behaviour_service.py` | No |
| `behavior_engine.py` | LEGACY COMPATIBILITY | `behaviour_engine/` package | Bridge until migration |
| `accounts_service.py` | SUPERSEDED | `account_service.py` | No |
| `accounts_router.py` | INCOMPLETE | `accounts.py` | Never registered |
| `financial_intelligence.py` | INCOMPLETE | (self) — router not yet registered | Service IS on roadmap (orchestrator) |
| `alert_repository.py` | DORMANT | (future) | `behaviour_alerts` table exists in schema |
| `pattern_repository.py` | DORMANT | (future) | Used by `behaviour_service.py` (active) |
| `liquidity_pattern_repository.py` | DORMANT | (future) | Used by `transaction_intelligence_service.py` (active) |
| `institution_repository.py` | DORMANT | (future) | `institutions` table exists; not wired to service |
| `api_common.py` | LEGACY COMPATIBILITY | (removed) | 0 consumers |
| `routers/health.py` | LEGACY COMPATIBILITY | `src/health.py` | Re-export shim |
| `common/database.py` | LEGACY COMPATIBILITY | `repositories/base.py` | `get_db()` deprecated |
| All 5 mappers | EXPERIMENTAL | (new layer) | DTOs exist but not wired |
| `financial_events_service.py` | ACTIVE | — | Used by `financial_events.py` router |

### 7.2 Phase Dependencies Graph

```
Phase 1 (Dead code removal)
    │
    ├──► Phase 2 (Router registration decision)
    │
    ├──► Phase 3 (Legacy engine consolidation)
    │       └──► Phase 4 (Service layer compliance)
    │               └──► Phase 6 (DTO & mapper restoration)
    │
    └──► Phase 5 (DB path consolidation)
                └──► Phase 6 (DTO & mapper restoration)

Phase 6 depends on ALL prior phases.
```

### 7.3 Freeze Readiness Verdict

| Category | Status | Details |
|---|---|---|
| Database ownership | ⚠️ NOT READY | 3 entry points; DB_PATH triplicated; legacy shim active |
| Repository layer | ⚠️ NOT READY | 1 dead repo; 5 routers bypass services; 3 repos dormant |
| Service layer | ⚠️ NOT READY | 1 dead service; 1 legacy engine dependency; 4 missing services |
| Router layer | ⚠️ NOT READY | 2 incomplete routers; 5 bypass service layer; 1 dead router |
| DTO compliance | ❌ NOT READY | 110/115 endpoints untyped; 0 mappers used; 10/13 DTOs orphaned |
| Import hygiene | ⚠️ NOT READY | Legacy bridges; dead re-exports; duplicate path logic |
| Database integrity | ⚠️ NOT READY | FK type mismatches; nullable FK columns; no multi-statement transactions |

**Overall verdict:** ❌ **NOT READY FOR FREEZE** — 6 phases of remediation required. Estimated total complexity: 30 (on scale of 1–5 per task, ~20 tasks). Phases 1–3 required before backend can be considered architecturally stable for Program 6.

---

## Appendix A: Evidence Commands Used

All findings verified via:
- CGC MCP subagents (5 parallel investigations using `find_code`, `execute_cypher_query`, `analyze_code_relationships`)
- `grep -rn` across `src/` and `tests/` for import/reference tracing
- `find` for file inventory
- `git log` for commit history analysis
- `grep -c` for registration verification

**Key grep commands:**
```bash
# FinanceDB/get_db imports outside repositories/
grep -rn "from src.db import\|from src.common.database import\|get_db()" src/ --include="*.py"

# Services with raw sqlite3
grep -rln "import sqlite3\|sqlite3.connect" src/services/ --include="*.py"

# Router bypass detection
grep -rn "from src.repositories" src/routers/ --include="*.py"

# DTO imports in routers
grep -rn "from src.core.dtos" src/routers/ --include="*.py"

# Mapper usage
grep -rn "from src.core.mappers" src/ --include="*.py"

# Router registration
grep -n "include_router" src/api.py
```

## Appendix B: File Change Log

| File | Action | Lines |
|---|---|---|
| `docs/reports/audits/PROGRAM_5.3_BACKEND_STABILIZATION_AUDIT.md` | Created (new) | This report |

**No source files modified. No files moved. No renames performed.**

---

**End of Report**
