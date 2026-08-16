# Backend `src/` File Classification — Program H

**Status:** CLASSIFICATION ONLY — nothing deleted, moved, or renamed.

## Classification legend

| Code | Meaning |
|---|---|
| **A** | Canonical and healthy — no action |
| **B** | Canonical but misplaced — potential future relocation |
| **C** | Compatibility layer — preserve until migration completes |
| **D** | Legacy but referenced — cannot delete; needs migration plan |
| **E** | Legacy and unreferenced — future archival candidate; **DO NOT remove now** |
| **F** | Duplicate active implementation — needs ownership decision |
| **G** | Generated/cache/local artifact — hygiene candidate; **DO NOT delete now** |
| **H** | Unknown — requires further evidence |

---

## 1. Top-Level Modules (Phase H2)

Every `backend/src/*.py` file, with ownership determined by evidence.

### `api.py` — **A**
- **Responsibility:** FastAPI application composition root.
- **Imports:** `config`, `errors`, `health`, 28 router modules.
- **Imported by:** uvicorn entrypoint; `tests/fixtures/client.py`.
- **Composition root?** **YES** — sole app assembly point.
- **Location justified?** Yes. Composition root belongs at package root.
- **Canonical replacement:** none.

### `config.py` — **A**
- **Responsibility:** Env-driven `Settings` + `validate_startup()`.
- **Imported by:** 6 src modules, 1 test module.
- **Notable:** `database_path` correctly **delegates** to `core/db/config.get_db_path` rather than duplicating resolution.
- **Location justified?** Yes — cross-cutting infrastructure.

### `errors.py` — **A**
- **Responsibility:** `register_error_handlers(app)` — API error contract.
- **Imported by:** 8 src modules, 2 test modules.
- **Location justified?** Yes — cross-cutting.

### `logger.py` — **A**
- **Responsibility:** `log_info` / `log_error` structured logging.
- **Imported by:** 4 src modules, 0 tests.
- **Location justified?** Yes — cross-cutting infrastructure.

### `health.py` — **A** (with duplicate-surface note)
- **Responsibility:** `/health` and `/ready` endpoints; `register_health_routes(app)`.
- **Imported by:** `api.py` (line 21, actually registered) **and** `routers/health.py` (pure re-export).
- **Observation:** the router surface is duplicated — see `routers/health.py` below. Only `src.health` is registered by `api.py`.
- **Location justified?** Arguably **B** — it is a router that lives outside `routers/`. Recorded as an observation, not a defect.

### `startup.py` — **A**
- **Responsibility:** Startup validation (config, directories, DB connectivity).
- **Imports:** `config`, `core.db.connection`, `logger`.
- **Location justified?** Yes — application lifecycle.

### `db.py` — **C (Compatibility layer)**
- **Responsibility:** `FinanceDB` backward-compatible wrapper.
- **Self-declared:** `.. deprecated:: New code should import from src.core.db directly`.
- **Delegates entirely to:** `core.db.config`, `core.db.connection`, `core.db.schema`.
- **Production consumers:** **ZERO** (only `common/database.py`, itself deprecated).
- **Test consumers:** 4 — `tests/fixtures/{database,client,seed,benchmark_fixtures}.py`.
- **Verdict:** **MUST BE PRESERVED.** Removing it breaks the test fixture layer. Requires a fixture migration plan first.

### `ingest.py` — **B / F**
- **Responsibility:** CLI PDF ingestion pipeline (`ingest_pdf`, `ingest_directory`, `main()`).
- **Imports:** `extraction.{categorizer,hybrid_extractor,metadata_extractor,statement_extractor}`, `repositories.{statement,transaction}_repository`.
- **Imported by:** `tests/integration/e2e/test_upload_pipeline.py` only.
- **Has `__main__` block:** yes — it is an executable CLI entrypoint.
- **Duplicate concern:** `services/import_service.py` composes the *same* extraction modules for the API path. Two ingestion compositions coexist.
- **Verdict:** **Valuable, executed, test-covered.** Not removable. Candidate for future relocation to a `cli/` surface (**B**) and for shared-pipeline extraction with `import_service` (**F**).

### `__init__.py` — **A** (0 bytes, package marker)

---

## 2. Database Infrastructure (Phase H3)

| Path | Class | Production consumers | Test consumers | Verdict |
|---|---|---|---|---|
| `core/db/__init__.py` | **A** | canonical | — | Single source of truth |
| `core/db/config.py` | **A** | `config.py`, `db.py`, `common/database.py`, `core/db/*` | yes | Canonical path resolution |
| `core/db/connection.py` | **A** | `startup`, `health`, 3 engines, repos, services | yes | Canonical connection factory |
| `core/db/schema.py` (918 LOC) | **A** | `db.py`, `core/db` | yes | Canonical DDL/migrations/verify |
| `core/db/transaction.py` | **A** | `core/db/__init__` | yes | Atomic transaction CM |
| `core/db/health.py` | **A** | `core/db` | yes | Connectivity/schema health |
| `db.py` | **C** | **0** | 4 fixtures | Compatibility shim — preserve |
| `common/database.py` | **C** | **0** | 0 | Deprecated shim; still re-exported by `common/__init__.py` |

**Canonical database authority: `src/core/db/` — established by evidence** (16 importing modules, 43 import statements, explicit deprecation pointers from both alternatives).

`common/database.py` self-documents: *"`get_db()` is deprecated with zero production consumers."* Verified accurate — the only reference is the re-export in `common/__init__.py:9`.

---

## 3. Engines (Phase H4)

Filesystem truth: **13 engines** = 8 packages + 4 single-file, plus `engines/__init__.py` facade.

| Engine | Style | Class | src consumers | test files | Notes |
|---|---|---|---|---|---|
| `account_engine/` | package | **A** | 1 | 2 | Pure |
| `behaviour_engine/` | package (18 modules) | **A** | 3 | 8 | Canonical; absorbed insights + nudges |
| `credit_card_engine/` | package | **A** | 1 | 6 | Pure |
| `loan_engine/` | package | **A** | 8 | 9 | Most-consumed engine |
| `financial_events/` | package | **A** | 1 | 5 | Pure |
| `financial_intelligence/` | package | **A** | 1 | 1 | Pure |
| `recommendation_engine/` | package | **A** | 2 | 2 | Pure |
| `transaction_intelligence/` | package (3 detectors) | **A** | 1 | 1 | Pure |
| `balance_engine.py` | single file | **D** | 1 | 1 | 4 × function-local `core.db` import — impure |
| `ledger_audit_engine.py` | single file | **D** | 1 | 1 | 2 × function-local `core.db` import — impure |
| `reconciliation_engine.py` | single file | **D** | 1 | 4 | 2 × function-local `core.db` import — impure |
| `cashflow_engine.py` | single file | **D** | **0** | 2 + 4 meta | See below |
| `engines/__init__.py` | facade | **A** | — | — | Re-exports `balance_engine` only |

### `cashflow_engine.py` — **D (Legacy but referenced), NOT E**

This is the module most likely to be mistaken for dead code. It is **not**.

- **Direct production importers:** 0
- **Test references:** `tests/properties/cashflow/test_engine_properties.py` (4 call sites), `tests/capability/household_cashflow/test_capability.py` (explicit capability test asserting importability + valid results)
- **Meta/tooling references:** used as the canonical fixture path in `tests/meta/test_selective_verify.py` (5×), `test_change_intelligence.py`, `test_validation_orchestrator.py`
- **Capability registry:** backs the named capability `household_cashflow`
- **Currently executed:** yes, under test
- **Verdict:** Deleting this would break the capability suite **and** the selective-verification meta tests. Classified **D**. Requires a service consumer or an explicit capability decision — not removal.

### Historical/legacy artifact probe

| Artifact | Filesystem | Residual references |
|---|---|---|
| `behavior_engine.py` | **ABSENT** | Provider registry (`PARKED_LEGACY`); `tests/architecture/test_layer_boundaries.py:43` whitelist entry; 2 test docstrings/paths |
| `insight_generator.py` | **ABSENT** | Provider registry only. Function lives in `behaviour_engine/insights.py` |
| `nudge_engine.py` | **ABSENT** | Provider registry only. Function lives in `behaviour_engine/nudges.py` |
| `cashflow_engine.py.parked` | **ABSENT** | Provider registry only; live `.py` exists instead |

**Stale whitelist observation:** `test_layer_boundaries.py` whitelists 4 engine files as "known legacy sqlite3 violations". Verified: **no file under `src/engines/` imports `sqlite3` at all** (grep returns nothing). The whitelist is entirely obsolete — including one entry for a file that no longer exists. This is a **CANDIDATE** for tightening, not a defect. Tightening it would *strengthen*, not weaken, verification — but it is out of scope for Program H.

---

## 4. Core Boundary (Phase H5)

`core/` **is** a coherent architectural layer, not a dumping ground. Evidence: clean internal dependency direction `mappers → dtos` (13 edges) and `mappers → domain` (3 edges), with no reverse edges.

| Subpackage | Class | Responsibility | Consumers | Direction |
|---|---|---|---|---|
| `core/db/` | **A** | DB infrastructure | 16 modules | inward (correct) |
| `core/domain/` (`money.py`, 318 LOC) | **A** | `Money` value object | 3 mappers | inward (correct) |
| `core/dtos/` (15 files) | **A** | API contracts | routers, services, mappers | correct |
| `core/mappers/` (14 files) | **A** | domain → DTO | routers, services | correct |

**`core/__init__.py` observation:** its docstring shows `from core.domain.money import Money` (missing the `src.` prefix). The **actual** imports below it are relative (`from .domain import Money`) and work correctly — verified by the 243/243 import check. Docstring-only inaccuracy, **not** a runtime defect.

### `core/dtos` ↔ `models` overlap

Shared domain names (both a model and a DTO exist): `account`, `behaviour`, `dashboard`, `reconciliation`, `statement`, `transaction`. This is **correct DDD separation** (persistence model vs API contract), classified **A**.

### `account_dto.py` vs `accounts_dto.py` — **F (Duplicate active implementation)**

| File | Consumers |
|---|---|
| `core/dtos/account_dto.py` (singular) | `core/dtos/__init__.py`, `core/__init__.py`, `core/mappers/account_mapper.py` |
| `core/dtos/accounts_dto.py` (plural) | `core/dtos/__init__.py`, `routers/accounts.py` |

Two live, separately-consumed DTO generations for the same domain. Both are actively imported, so neither is removable without an ownership decision. **Classified F.**

---

## 5. Models / Repositories / Services / Routers (Phase H6)

| Layer | Count | Class | Notes |
|---|---|---|---|
| `models/` | 22 | **A** | Persistence/domain models |
| `repositories/` | 27 | **A** | Data access; `base.py` centralizes `core.db` usage |
| `services/` | 32 | **A** | Incl. 7 workspace services |
| `routers/` | 29 | **A** | Incl. 8 workspace routers; 28 registered in `api.py` |

### Workspace modules — **A (not anomalies)**

7 workspace services verified to follow the canonical pattern: each imports `services.base.BaseService` and repositories (or another service), never a router, never a DB driver. Examples: `networth_workspace_service` → 4 repositories + `BaseService`; `cashflow_workspace_service` → `CashflowService`. **Legitimate composition, not duplication.**

### `routers/health.py` — **F (duplicate surface, benign)**
```python
from src.health import register_health_routes, router
```
A 4-line pure re-export. `api.py` registers `src.health` **directly**, so `routers/health.py` is imported only via `routers/__init__.py`. No double registration occurs (119 routes verified). Classified **F** — duplicate surface requiring an ownership decision, harmless today.

### Layer violations (evidence, not verdicts)

| Violation | Sites | Class | Assessment |
|---|---|---|---|
| `models → engines` | `models/loan_simulation.py:12` imports `engines.loan_engine.models.PrepaymentMode` | **D** | Single reverse-layer edge; a shared enum. Low risk, needs a type-location decision. |
| `engines → core.db` | 8 function-local imports in `balance_engine`, `ledger_audit_engine`, `reconciliation_engine` | **D** | Breaks engine purity. Deliberately function-local (lazy) to avoid import cycles. Requires repository-injection migration. |
| `routers → models` (DTO bypass) | `routers/{loans,credit_cards,behaviour,accounts}.py` | **D** | Predates DTO layer; ironically these routers' docstrings claim "no FinanceDB import" purity. Needs DTO migration. |

**No circular imports exist** — proven by the 243/243 successful module import sweep.

---

## 6. Extraction / Ingestion / Orchestration (Phase H7)

The pipeline **is** coherent:

```text
PDF/CSV input
   ↓  extraction/{hybrid,camelot,table,statement,metadata}_extractor  (+ structural/layout_analyzer)
   ↓  extraction/{transaction_parser, column_mapper, categorizer, validator}
   ↓  repositories/{statement,transaction}_repository
   ↓  orchestration/statement_orchestrator  → 6 services (behaviour, cashflow, dashboard, FI, loan, txn-intel)
```

| Module | Class | Notes |
|---|---|---|
| `extraction/*` (11 modules) | **A** | Coherent; `statement_extractor.py` is the largest file in `src` (1,556 LOC) — size observation only |
| `structural/layout_analyzer.py` (843 LOC) | **B** | Sole consumer is `extraction/hybrid_extractor.py`. A single-module top-level package used by exactly one caller — arguably belongs under `extraction/`. Relocation candidate only. |
| `orchestration/statement_orchestrator.py` | **A** | Correct direction (orchestration → services, 7 edges). Invoked by `import_service.py:119` via lazy import. |
| `ingest.py` | **B/F** | CLI path (see §1) |
| `services/import_service.py` | **A/F** | API path; duplicates extraction composition with `ingest.py` |

**Duplicated composition (not duplicated logic):** both `ingest.py` and `import_service.py` independently wire `categorizer` + `metadata_extractor` + `statement_extractor`. The underlying parsing logic is shared and single-sourced in `extraction/`. This is **composition duplication**, materially lower risk than logic duplication.

---

## 7. Vestigial / Artifact Items

| Path | Class | Evidence |
|---|---|---|
| `utils/__init__.py` | **E** | 0 bytes; `grep src.utils` returns **zero** hits in `src/` and `tests/`. Genuinely unreferenced empty package. **Do not remove now** (archival candidate). |
| `data/__init__.py` | **G / H** | 0 bytes; git-**ignored**; nothing imports `src.data`. Makes `data/` a Python package for no evidenced reason. |
| `data/finance.db` | **G** | 0 bytes, **tracked in git** despite `*.db` ignore rules. Not the runtime DB (runtime resolves to CWD-relative `data/finance.db`). |
| `.mypy_cache/` | **G** | Tool cache inside the source tree |
| 25 × `__pycache__/`, 249 × `.pyc` | **G** | Standard Python cache |

---

## Classification Totals

| Class | Count (notable items) |
|---|---|
| **A** — Canonical/healthy | Majority of 243 modules; all `core/*`, 8 engine packages, models, repos, services, routers, extraction |
| **B** — Canonical but misplaced | `structural/layout_analyzer.py`, `ingest.py`, (`health.py` noted) |
| **C** — Compatibility layer | `db.py`, `common/database.py` |
| **D** — Legacy but referenced | `cashflow_engine.py`, 3 impure single-file engines, `models/loan_simulation.py` edge, 4 DTO-bypassing routers |
| **E** — Legacy unreferenced | `utils/` (empty package) |
| **F** — Duplicate active | `account_dto.py`↔`accounts_dto.py`, `routers/health.py`↔`health.py`, `ingest.py`↔`import_service.py` |
| **G** — Artifacts | 25 `__pycache__`, 249 `.pyc`, `.mypy_cache/`, `data/finance.db`, `data/__init__.py` |
| **H** — Unknown | None outstanding — all items resolved to a class with evidence |
