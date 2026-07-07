# ClariFin_OS — Backend Architecture & Flow Audit Report

> **Status**: Read-only audit. No source files were modified.
> **Date**: 2026-07-07
> **Scope**: backend/ structure, server entry point, API flow, DB layer, engines, money flow, DTO/mapper adoption, and AI/Cline environment.
> **Aggregates**: prior discovery batches + deep-dive flow trace + AI rules review (/home/vasantha/Documents/Cline/Rules/) + root package.json + frontend/package.json/tsconfig/next.config/eslint.config.

---

## 1 PROJECT TREE (backend/src only, LOC per file, __pycache__ excluded)

```
backend/src/  (15,438 LOC total across 54 .py files)
├── api.py                        2256  <- Application + Controller + Service + Orchestrator (49 routes)
├── db.py                         1755  <- Monolithic FinanceDB super-repository (~59 methods)
├── statement_extractor.py        1368  <- PDF statement extraction
├── metadata_extractor.py          850  <- Statement metadata (due date, totals)
├── csv_importer.py                695  <- CSV import pipeline
├── extraction/
│   ├── hybrid_extractor.py        687
│   ├── camelot_extractor.py       275
│   └── __init__.py                  0
├── structural/
│   └── layout_analyzer.py         661
├── engines/  (2,827 LOC - pure-function domain layer)
│   ├── behavior_engine.py         974  <- largest engine; caching via cachetools.TTLCache
│   ├── reconciliation_engine.py   400
│   ├── insight_generator.py       394
│   ├── balance_engine.py          379
│   ├── nudge_engine.py            287
│   ├── ledger_audit_engine.py     197
│   ├── loan_engine.py             177  <- only engine using paise ints correctly
│   └── __init__.py                 19
├── categorizer.py                 344
├── validator.py                   360
├── ingest.py                      383
├── table_extractor.py             290
├── transaction_parser.py          136
├── column_mapper.py               136
├── config.py                      160  <- pydantic-settings Settings
├── main.py                        164  <- PDF extraction BENCHMARK HARNESS (NOT the server)
├── errors.py                      252  <- defined but NOT wired as global handler
├── health.py                      118
├── startup.py                      79
├── logger.py                      109
├── core/
│   ├── domain/
│   │   └── money.py               315  <- Money (integer paise, immutable) - CANONICAL but bypassed
│   │   └── __init__.py             28
│   ├── dtos/  (5 DTOs - ORPHANED, never imported by api/db)
│   │   ├── dashboard_dto.py       102
│   │   ├── transaction_dto.py      96
│   │   ├── analytics_dto.py        92
│   │   ├── statement_dto.py        83
│   │   ├── account_dto.py          62
│   │   └── __init__.py             26
│   ├── mappers/  (5 mappers - ORPHANED, only self-test imports)
│   │   ├── transaction_mapper.py  172
│   │   ├── account_mapper.py      135
│   │   ├── dashboard_mapper.py    130
│   │   ├── statement_mapper.py    119
│   │   ├── analytics_mapper.py    110
│   │   └── __init__.py             23
│   ├── __init__.py                 40
│   ├── models/        (EMPTY scaffold)
│   ├── repositories/  (EMPTY scaffold)
│   ├── services/      (EMPTY scaffold)
│   └── db/            (EMPTY scaffold)
├── db/
│   └── repos/         (EMPTY - only __pycache__)  <- intended repository layer, never built
├── routers/           (EMPTY - only __pycache__)  <- intended router layer, never built
├── app/               (EMPTY - only __pycache__)
├── audits/            (EMPTY)
├── reports/           (EMPTY)
├── utils/             (EMPTY)
└── (no models/, services/, parsers/ at src level - they do not exist)
```

**Key structural facts**
- Two god-files (api.py 2256 + db.py 1755 = 4011 LOC, 26% of backend) hold nearly all business logic.
- routers/, core/services/, core/repositories/, core/models/, db/repos/ are EMPTY scaffolds - the refactor was mentally started but never executed.
- core/dtos/ + core/mappers/ exist (10 files, ~849 LOC) but are dead code relative to the live path.
- backend/venv/ is committed into the repo (should be gitignored).
- Stale artifact: __pycache__/auto_heal_engine.cpython-312.pyc implies a deleted auto_heal_engine.py source.

---

## 2 SERVER ENTRY POINT

| Question | Finding |
|---|---|
| What file launches FastAPI? | backend/src/api.py defines app = FastAPI(...) at line 333. Launched via uvicorn api:app. |
| Is there a create_app() factory? | No. The app is a module-level singleton built inline (CORS middleware added at import time). No factory / no lifespan DI container. |
| Is DB injected globally or per-request? | Per-request, but re-instantiated every call. get_db() (api.py:352) returns FinanceDB(db_path=DB_PATH) - a brand-new connection object on every route invocation. |
| How is dependency injection handled? | Manual, not FastAPI Depends. Each route calls db = get_db() locally. No Annotated[FinanceDB, Depends()] pattern. No DI framework. |

CRITICAL RUNTIME DEFECT (contradicts AI Rule 0):
Root package.json start:all runs:
    cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000
Two bugs:
1. main:app is wrong - main.py is the PDF-extraction harness with no FastAPI instance -> AttributeError: module 'main' has no attribute 'app'. The app is in api.py.
2. .venv path is wrong - cd backend && source .venv/... expects backend/.venv/, which does not exist. Real venvs: root .venv/ (used by AI rules as ../.venv/bin/python3) and backend/venv/.

Consequence: The AI-rules-mandated npm run start:all (0) cannot bring the API up. The OpenAPI contract generation (frontend gen:types -> http://localhost:8000/openapi.json) is therefore unreachable, breaking Rule 7.

---

## 3 API FLOW TRACE

### 3a. POST /api/upload (api.py:1143) - full flow
```
HTTP POST /api/upload (file: UploadFile, member: str=Form("Self"))
  -> db = get_db()                         # new FinanceDB()
  -> save PDF to UPLOAD_DIR
  -> db.get_duplicate_check_by_filename()  # db.py
  -> StatementExtractor(save_path).extract()  # statement_extractor.py (NOT an engine)
  -> for txn: categorize(desc, float(amount))  # categorizer.py - float parsing inline
  -> db.insert_statement(...)              # db.py
  -> db.insert_transactions(stmt_id, txns) # db.py (float amount -> ROUND(*100) paise)
  -> MetadataExtractor(...).extract()      # metadata_extractor.py
  -> db.update_statement_metadata(...)    # db.py
  -> VALIDATION: sums float amounts, diff vs total_due (float math)
  -> db.update_validation_status(...)      # db.py
  -> invalidate_behavior_cache()           # behavior_engine cache
  -> return { "success": True, "bank":..., "transaction_count":..., "validation_status":..., "metadata":..., "log":[...] }
```
- Calls in db.py: get_duplicate_check_by_filename, insert_statement, insert_transactions, update_statement_metadata, update_validation_status.
- Calls in engines/: None directly - but calls invalidate_behavior_cache() (behavior_engine) and the non-engine extractors (StatementExtractor, MetadataExtractor, categorize).
- Constructs raw dicts? Yes - response is a hand-built dict; no DTO.
- Uses DTOs? No.

### 3b. POST /api/reconciliations/create (api.py:1511) - full flow
```
HTTP POST /api/reconciliations/create (Query params: debit_txn_id, credit_txn_id,
        debit_account_id, credit_account_id, amount: float, date_diff_days,
        match_confidence: float, match_type)
  -> db = get_db()
  -> db.insert_reconciliation(amount=amount, ...)   # db.py - amount passed as FLOAT rupees
  -> return {"success": True, "inserted": inserted}
```
- Calls in db.py: insert_reconciliation (stores amount - reconciliation table stores the float amount column, not paise).
- Calls in engines/: None.
- Constructs raw dicts? Yes. DTOs? No.

### Canonical trace shape
```
HTTP -> Route (api.py) -> db.py (FinanceDB) -> [extractors/categorizer] -> db.py -> Response(dict)
                                   \ engines/ (balance, behavior, reconciliation, etc.) -> db.py -> Response
```
Engines are invoked only by specific analytic routes (behavior/score/insights, dashboard/summary, accounts/balance, reconciliations/scan), not by the write paths (upload, import, CRUD).

---

## 4 DB.PY USAGE

| Question | Finding |
|---|---|
| Is FinanceDB instantiated once globally? | No - instantiated per-request via get_db() (~20 call sites). No singleton / no connection pool. |
| Is it thread-safe? | No. Each instance opens its own sqlite3.Connection. Under Uvicorn's threaded/async worker, concurrent requests each create separate connections; SQLite handles serial access but there is no locking strategy, no WAL mode confirmed, no pool. Write races possible under load. |
| Does it use SQLite? | Yes - raw sqlite3 (no ORM/SQLAlchemy). |
| Are connections reused? | Partially. FinanceDB supports context-manager (__enter__/__exit__) and a _conn member, but get_db() returns a fresh instance each call, so reuse is per-call only. |
| Does it use transactions? | Yes - commit() on context exit / explicit commits; rollback() on exception. Immutability enforced via BEFORE UPDATE/DELETE SQLite triggers on transactions. |

Domains handled by the single FinanceDB class (violates SRP):
Statements, Transactions, Categories, Banks, Members, Import mappings, Reconciliation, Accounts, Loans, Investments, Net worth, Audit, Validation.

---

## 5 ENGINES ROLE CLARITY

All 7 engines are stateless, DB-coupled pure-function modules. They do NOT import db.py (confirmed: no 'from db import' in engines/). Each opens its own sqlite3 connection from a db_path: str argument.

| Engine | Layer | DB-coupled? | Stateless? | Returns |
|---|---|---|---|---|
| balance_engine | Domain/DB | Yes (opens conn) | Yes | dict / list[dict] (uses _format_paise -> rupee string) |
| behavior_engine | Domain/DB | Yes | Yes (TTLCache for profile) | dict[str, Any] |
| insight_generator | Pure domain | No (takes profile dict) | Yes | list[dict] / str |
| ledger_audit_engine | Domain/DB | Yes | Yes | dict[str, Any] (audit report) |
| loan_engine | Pure domain | No (takes ints) | Yes | int / dict (paise-correct) |
| nudge_engine | Pure domain | No (takes profile) | Yes | dict / str |
| reconciliation_engine | Domain/DB | Yes | Yes | list[dict] / str |

Return type: All engines return plain dict / list[dict] - never domain models or DTOs. The boundary is clean at the engine level; the coupling problem is entirely in api.py/db.py.

---

## 6 MONEY FLOW

| Location | Type used | Notes |
|---|---|---|
| core/domain/money.py | Money (int paise) | Canonical, immutable, rejects floats. Only used by core/mappers/*. |
| db._parse_amount() (line 154) | returns float | float(s) after stripping Rs/,; silently returns 0.0 on failure (data-loss risk). |
| db.insert_transactions (line 539) | float -> int(round(amount*100)) | Derives amount_paise from float; stored in INTEGER amount_paise AND REAL amount. Float remains source of truth for filters (t.amount >= ?). |
| api.py handlers | float everywhere | format_inr(amount: float), amount = float(txn.get("amount") or 0), amount_paise = int(round(amount*100)). |
| api.reconciliations/create | amount: float Query | Passed straight to db.insert_reconciliation as float rupees. |
| loan_engine | int paise | Correct - compute_emi(principal_paise: int, ...). |
| Frontend expectation | floats / numbers | frontend/types/*.ts model amounts as numbers; api-generated.ts (from OpenAPI) would mirror the float Query/dict shapes. No paise contract on the wire. |

Verdict: The Money discipline is defined but not enforced on the hot path. Floats flow DB -> API -> wire -> frontend. This is the most critical technical debt for a personal-finance system where precision must be absolute (Rule 5 violation in practice).

---

## 7 DTO / MAPPER USAGE

- core/dtos/ used anywhere? No. grep for 'from.*dtos import' in api.py and db.py -> none.
- core/mappers/ used anywhere? No in api.py/db.py. Only core/mappers/* import Money and self-reference; they are exercised by nothing in the live request path.
- Were they planned for a refactor? Yes - clearly. The presence of 5 DTOs + 5 mappers + empty routers/, core/services/, core/repositories/, db/repos/ confirms an intended layered architecture (Controller -> Router -> Service -> Repository -> DTO/Mapper -> Domain) that was started then bypassed under deadline pressure. The DTO layer is currently dead code; recoverable but must be intentional.

---

## 8 CLINE / CURSOR ENVIRONMENT

| Practice | Status in this repo |
|---|---|
| Auto-fix loops | Yes - AI Rule 3 mandates pausing on validation failure and looping until clean. lint-staged + husky enforce eslint --fix --max-warnings 0 + tsc --noEmit pre-commit. |
| Strict linting | Yes - ruff (backend, pyproject.toml select E/W/F/I/B/C4/UP/N) + ESLint (frontend, max-warnings 0). BUT api.py/db.py are in mypy ignore_errors = true overrides -> untyped, unchecked. |
| Type checking (mypy) | Configured (disallow_untyped_defs = true globally) but disabled for api, db, engines.*, categorizer, etc. via overrides. Frontend tsc --noEmit strict mode IS enforced. |
| Test-driven refactors? | Partial - 5 backend tests (determinism, reconciliation x2, behavior, audit) but no route/integration tests for api.py and no CRUD tests for db.py. Frontend has Vitest + Playwright. |
| AI context limits hitting often? | Yes, structurally. God-files (4011 LOC) + untyped overrides force fragmentary reads. Rule 8/9 explicitly mandate token-budget locking + CGC graph traversal because of this. Splitting into small router/repo files is the direct remedy. |
| Architecture optimized for AI context efficiency? | Not yet - but the empty scaffolds prove the intent exists. The refactor (routers + services + repositories + DTO wiring) is exactly the optimization the rules are steering toward. |

---

## 9 CRITICAL ARCHITECTURAL SMELLS (consolidated)

### 1. api.py = Application + Controller + Service + Orchestrator
49 routes in one 2,256-LOC file. Causes: AI context explosion, merge conflicts, cognitive overload, hidden coupling, refactor paralysis.
Mitigating: No internal module imports api.py (verified) -> it can be split safely into routers/ with zero blast radius.

### 2. db.py = Super Repository
FinanceDB handles 13 domains in one 1,755-LOC class. Violates SRP, separation of domains, AI edit locality.
Mitigating: db/repos/ exists -> refactor was already mentally started.

### 3. Money Discipline Not Enforced (MOST CRITICAL TECHNICAL DEBT)
core/domain/money.py (paise, immutable) exists, but _parse_amount -> float, API returns float, DB stores float (with a parallel paise column that the queries ignore). For personal finance, precision must be absolute. Recoverable via the paise columns already present - but requires the API/DB layers to actually use Money/paise end-to-end.

### 4. DTO Layer Exists But Ignored
Enterprise architecture started, then bypassed. API builds dicts inline; DTO/mapper layer is dead code. Recoverable - wire core/mappers/* into routers and return core/dtos/*.

### 5. (NEW) Broken Runtime Entry Point
npm run start:all targets main:app (wrong module) in backend/.venv (wrong path). Violates AI Rule 0's precondition that servers be running. This is the highest-priority hotfix - nothing else in the AI workflow can run correctly until the API boots.

### 6. (NEW) Weak Error Handling
Every route wraps logic in try: except Exception: raise HTTPException(500, str(e)). Leaks internals, loses stack traces, no 4xx distinction. errors.py is defined but not registered as a global exception handler.

### 7. (NEW) Silent Migrations
All _create_tables/_run_migrations ALTER TABLE/UPDATE wrapped in except Exception: pass - masks schema-drift failures.

---

## RECOMMENDED REMEDIATION ROADMAP

**Phase 0 - Unblock runtime (hotfix, blocking):**
- Fix package.json start:all: uvicorn api:app (not main:app) + ../.venv (or standardize venv location). This satisfies AI Rule 0 and enables OpenAPI contract gen (Rule 7).

**Phase 1 - Money hardening (hotfix, critical):**
- Make _parse_amount return int paise (or Money); have api.py serialize paise to the wire; update frontend types. Replace float filters (t.amount) with amount_paise.
- Register errors.py as a global ExceptionMiddleware; replace blanket 500s with typed 4xx/5xx.

**Phase 2 - Layered refactor (systematic, AI-context-optimizing):**
- Extract routers/ from api.py by domain (transactions, statements, accounts, loans, investments, reconciliation, behavior, audit, import, dashboard, health).
- Extract core/repositories/ from FinanceDB (one repo per domain); keep db.py as the connection/schema owner.
- Introduce core/services/ as the orchestration layer (currently inline in routes).
- Wire core/mappers/* + core/dtos/* into routers; delete inline dict construction.
- Re-enable mypy for api/db/engines incrementally as they are split.

**Phase 3 - Hygiene:**
- Remove committed backend/venv/ from git; add to .gitignore.
- Add route/integration tests for api.py and CRUD tests for repositories.
- Replace inline except: pass migrations with logged, observable migration steps.

---

*End of report. Read-only; no source modified.*
