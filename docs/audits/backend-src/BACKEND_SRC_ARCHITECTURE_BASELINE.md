# Backend `src/` Architecture Baseline — Program H

**Status:** AUDIT ONLY — no deletions, no moves, no renames, no source mutation
**Generated:** 2026-08-08
**Branch:** `feature/program-12-platform-certification`
**Scope:** `backend/src/**` (secondary evidence: `backend/tests/**`, runtime provider metadata, gitignore/CI config)

---

## 1. Filesystem Hygiene Baseline (Phase H1)

Measured directly from the working tree.

| Metric | Count |
|---|---|
| Directories under `backend/src` | 50 |
| Total files under `backend/src` | 483 |
| Python source files (excl. `__pycache__`) | 244 |
| Python source **tracked by git** | 243 |
| Total lines of Python source | 45,910 |
| `.pyc` files | 249 |
| `__pycache__/` directories | 25 |
| `.mypy_cache/` (20K) | 1 |
| Local database artifacts (`.db`) | 1 |

### Classification of every non-source item

| Path | Class | Tracked | Note |
|---|---|---|---|
| `backend/src/**/__pycache__/` (25 dirs, 249 `.pyc`) | **5 — Python cache** | No (ignored) | Ignored via `backend/.gitignore:2-3` |
| `backend/src/.mypy_cache/` (+ `CACHEDIR.TAG`, `.gitignore`, `missing_stubs`) | **6 — Tool cache** | No (ignored) | Ignored via `backend/.gitignore:7`. Note: tool cache written *inside* the source tree. |
| `backend/src/data/finance.db` | **7 — Local database artifact** | **YES (tracked, 0 bytes)** | See CI risks — tracked despite `*.db` ignore rules. |
| `backend/src/data/__init__.py` | **10 — Unknown / ignored source** | **NO (ignored)** | Ignored by `backend/.gitignore:13:data/`. See CI risks. |
| `backend/src/utils/__init__.py` | **2 — Package initializer** | Yes | 0 bytes, zero importers. Empty namespace package. |

**Directory-level classification (all 50 accounted for):**

- **Production Python source (17 package dirs):** `common`, `core`, `core/db`, `core/domain`, `core/dtos`, `core/mappers`, `engines`, `engines/{account,behaviour,credit_card,loan,recommendation,transaction_intelligence,financial_events,financial_intelligence}_*`, `extraction`, `models`, `orchestration`, `repositories`, `routers`, `services`, `structural`
- **Empty/vestigial package dirs (2):** `utils`, `data`
- **Cache dirs (26):** 25 × `__pycache__`, 1 × `.mypy_cache` (+`3.12` subdir, empty)

No hygiene artifact was removed. All are recorded as **Class G** in the classification report.

---

## 2. Current Architecture (Phase H10 — actual, not invented)

```text
backend/src
├── api.py                  application composition root (FastAPI, 28 routers, 119 routes)
├── startup.py              application startup validation
├── health.py               operational endpoints (/health, /ready)
├── config.py               configuration (env-driven Settings)
├── errors.py               error handler registration
├── logger.py               logging infrastructure
├── ingest.py               CLI ingestion entrypoint (parallel to import_service)
├── db.py                   COMPATIBILITY shim -> core/db (FinanceDB)
│
├── core/                   canonical shared kernel
│   ├── db/                 CANONICAL database authority
│   ├── domain/             Money value object
│   ├── dtos/               15 API contract DTOs
│   └── mappers/            14 domain->DTO mappers
│
├── models/                 22 persistence/domain models
├── repositories/           27 repositories (data access)
├── services/               32 services (business orchestration, incl. 7 workspace services)
├── routers/                29 routers (HTTP surface, incl. 8 workspace routers)
│
├── engines/                13 computation engines (8 packages + 4 single-file)
├── extraction/             11 modules — PDF/CSV extraction + parsing
├── structural/             layout_analyzer (used by hybrid_extractor)
├── orchestration/          statement_orchestrator (post-import fan-out)
├── common/                 shared helpers + DEPRECATED database.py shim
│
├── utils/                  EMPTY package (0 importers)
├── data/                   local DB artifact dir (partially git-ignored)
└── [artifacts]             __pycache__, .mypy_cache, finance.db
```

### Layer dependency reality (edge counts from AST analysis)

The dominant flow is **correct and healthy**:

```text
routers ──28──> services ──54──> repositories ──> core.db / models
   │               │
   │               └──23──> engines
   └──8──> core.dtos ──> core.mappers ──> core.domain
```

Full edge table is in `BACKEND_SRC_DEPENDENCY_MAP.md`.

---

## 3. Canonical Authorities Established (evidence-based)

| Concern | Canonical authority | Evidence |
|---|---|---|
| **Database** | `src/core/db/` | 16 production modules import it; 43 import statements; self-declared "Single source of truth"; `db.py` + `common/database.py` both carry `.. deprecated::` markers pointing to it |
| **DB path resolution** | `src/core/db/config.get_db_path` | Documented resolution order; `config.py`, `db.py`, `common/database.py` all delegate to it |
| **Schema/DDL** | `src/core/db/schema.py` (918 LOC) | Docstring: "Extracted from `db.py` (FinanceDB god-file)" |
| **Composition root** | `src/api.py` | Sole FastAPI assembly point; registers 28 routers -> 119 routes |
| **Engine registry** | `runtime/generated/architecture-provider.json` | Declares 13 engines — **but is stale, see below** |

---

## 4. Intended Canonical Architecture (only where already established)

Established by the canonical provider (`architecture-provider.json`, `architecture-provider-v1`) and existing architecture tests:

1. **Engine = architectural UNIT** (package root or designated single file). `*.py == Engine` is explicitly forbidden by provider principle.
2. **Engines must be pure** — no `sqlite3`, no `sqlalchemy`, no FastAPI, no router imports (enforced by `tests/architecture/test_layer_boundaries.py`).
3. **`core/db` is the single database infrastructure package**; `db.py`/`common/database.py` are transitional.
4. **Layering:** routers → services → repositories → database.
5. **DTO boundary:** routers should return DTOs from `core/dtos` via `core/mappers`.

---

## 5. Delta — What Remains To Be Migrated

| # | Delta | Current state | Evidence |
|---|---|---|---|
| D1 | `db.py` / `common/database.py` retirement | Both deprecated, **zero production consumers**, but 4 test fixtures still import `FinanceDB` | `tests/fixtures/{database,client,seed,benchmark_fixtures}.py` |
| D2 | Engine purity for 3 single-file engines | `balance_engine`, `ledger_audit_engine`, `reconciliation_engine` perform function-local `core.db.connection` imports (8 sites) | Architecture test whitelist exists but is now **stale** (see D3) |
| D3 | **Provider registry drift** | Provider lists 4 paths that no longer exist and misses one that does | See §6 |
| D4 | DTO adoption | Only 4 of 29 routers import `core.dtos`; 4 routers import `src.models` directly | `routers/{loans,credit_cards,behaviour,accounts}.py` |
| D5 | DTO generation overlap | `core/dtos/account_dto.py` (singular) vs `core/dtos/accounts_dto.py` (plural) — both live, different consumers | See classification report |
| D6 | Dual ingestion paths | `ingest.py` (CLI) and `services/import_service.py` (API) both compose extraction | Both import `categorizer`, `metadata_extractor`, `statement_extractor` |
| D7 | Vestigial packages | `utils/` (empty, 0 importers), `data/` (artifact dir inside source tree) | Verified by grep |

---

## 6. Provider Registry Drift (high-signal finding)

`runtime/generated/architecture-provider.json` (generated 2026-08-06) is **out of sync with the filesystem**. This is an OBSERVATION about generated metadata, not a source defect.

**Phantom paths — declared by provider, absent from disk:**

| Provider entry | Declared type | Filesystem |
|---|---|---|
| `backend/src/engines/insight_generator.py` | engine (single_file) | **MISSING** |
| `backend/src/engines/nudge_engine.py` | engine (single_file) | **MISSING** |
| `backend/src/engines/behavior_engine.py` | facade `PARKED_LEGACY` | **MISSING** |
| `backend/src/engines/cashflow_engine.py.parked` | facade `PARKED` | **MISSING** |

**Real module missing from the registry:**

| Filesystem | Provider |
|---|---|
| `backend/src/engines/cashflow_engine.py` (live, test-referenced, named capability) | **NOT REGISTERED** as an engine |

**Interpretation (evidence-based, not guessed):**
- The `behavior_engine.py` → `behaviour_engine/` migration is **complete on disk**. The historical spelling survives only in the provider registry, one architecture-test whitelist entry, and two test docstrings/filenames.
- `insight_generator` and `nudge_engine` functionality was **absorbed into `behaviour_engine/insights.py` and `behaviour_engine/nudges.py`** (both exported from `behaviour_engine/__init__.py`). The standalone modules no longer exist; the provider entries are historical residue.
- `cashflow_engine.py` appears to have been **un-parked** (restored from `.parked`) after the provider snapshot was generated (file mtime 2026-08-07 17:31 > provider 2026-08-06 17:26).

**No action taken.** Regenerating the provider is a separate program.

---

## 7. Validation Results

| Check | Result |
|---|---|
| Import validation — all 243 `src.*` modules | **PASS** (243 imported, 0 failures) |
| FastAPI composition (`src.api:app`) | **PASS** (119 routes) |
| `tests/architecture` + `tests/meta` | **PASS** (111 passed) |
| `runtime/verify.py quick` | **PASS** |
| `runtime/verify.py backend` | **FAIL — PRE-EXISTING** (3 `loan_engine` property tests) |
| `git status backend/src` | **CLEAN — no source mutation** |
| `git ls-files backend/src` | 244 tracked (243 `.py` + 1 `.db`) |

### Pre-existing failure detail

`run_backend_verification.sh` step 3 fails on 3 Hypothesis property tests:

- `tests/properties/loan_engine/test_floating_rate_properties.py::test_apply_floating_rate_change_math_accuracy`
- `tests/properties/loan_engine/test_foreclosure_properties.py::test_compute_foreclosure_amount_math_accuracy`
- `tests/properties/loan_engine/test_prepayment_properties.py::test_apply_prepayment_at_month_reduce_tenure_mode`

Example falsifying assertion: `assert 94737 <= 77695` — an interest-accrual tolerance breach found by Hypothesis fuzzing, not an import/structural fault.

**Proof these are PRE-EXISTING and unrelated to Program H:** `git status --porcelain backend/src` returns empty — this program modified zero source files. The other three suites in the same script (`contract` 161, `invariants` 26, `unit/engines` 468) all pass.

---

## 8. Constitutional Compliance

| Constraint | Status |
|---|---|
| Files deleted | **NONE** |
| Files moved | **NONE** |
| Files renamed | **NONE** |
| Production source modified | **NONE** |
| `runtime/foundation/`, `runtime/verify.py` modified | **NONE** |
| Verification logic weakened | **NONE** |
| Tests removed | **NONE** |
| Artifacts created | 5 audit documents under `docs/audits/backend-src/` |
