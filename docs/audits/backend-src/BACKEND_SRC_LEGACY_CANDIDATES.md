# Backend `src/` Legacy Candidates — Program H

**NOTHING IN THIS DOCUMENT MAY BE DELETED, MOVED, OR RENAMED AS PART OF PROGRAM H.**

Every entry below carries the full Phase H9 evidence record. A candidate is **not** a defect.

Evidence fields per item: path · classification · direct imports · test refs · runtime/provider refs · registry refs · API refs · executed? · tested? · canonical replacement · migration risk · recommended future action.

---

## CANDIDATE 1 — `backend/src/db.py`

| Field | Evidence |
|---|---|
| **Classification** | **C — Compatibility layer** |
| **Direct import references (prod)** | **0.** Only `src/common/database.py:22,30` (itself deprecated) |
| **Test references** | **4** — `tests/fixtures/database.py`, `client.py`, `seed.py`, `benchmark_fixtures.py` |
| **Runtime/provider references** | None in `architecture-provider.json` |
| **Registry references** | None |
| **API references** | None — not imported by `api.py` or any router |
| **Currently executed** | **YES** — via test fixtures on every backend test run |
| **Has tests** | Indirectly (fixture infrastructure) |
| **Canonical replacement** | `src/core/db/` (`get_connection`, `get_db_path`, `schema.create_all`) — explicitly named in its own deprecation docstring |
| **Migration risk** | **MEDIUM.** `FinanceDB.__init__` performs `create_all` + `run_migrations` + `verify_schema` as one atomic sequence and supports the context-manager protocol. Fixtures depend on both behaviours. |
| **Recommended future action** | **PRESERVE.** Migrate the 4 fixtures to `core.db` first, then re-evaluate. Do not delete. |

---

## CANDIDATE 2 — `backend/src/common/database.py`

| Field | Evidence |
|---|---|
| **Classification** | **C — Compatibility layer (dormant)** |
| **Direct import references** | **1** — re-exported by `src/common/__init__.py:9` (`from .database import get_db`) and listed in `__all__` |
| **Test references** | **0** |
| **Runtime/provider references** | None |
| **Registry references** | None |
| **API references** | None |
| **Currently executed** | Module is imported (via `common/__init__`); `get_db()` itself is **never called** |
| **Has tests** | No |
| **Canonical replacement** | `src/core/db/` + repository classes |
| **Migration risk** | **LOW.** Self-documents: *"`get_db()` is deprecated with zero production consumers."* Verified accurate. Only coupling is the `common/__init__` re-export. |
| **Recommended future action** | Lowest-risk compatibility removal in the codebase — but **NOT in Program H**. Requires removing the `common/__init__` re-export in the same change. |

---

## CANDIDATE 3 — `backend/src/engines/cashflow_engine.py`

| Field | Evidence |
|---|---|
| **Classification** | **D — Legacy but referenced** (explicitly **NOT E**) |
| **Direct import references (prod)** | **0** |
| **Test references** | `tests/properties/cashflow/test_engine_properties.py` (4 call sites); `tests/capability/household_cashflow/test_capability.py` (2 tests asserting import + valid result) |
| **Runtime/provider references** | **Registry lists only `cashflow_engine.py.parked` (a path that no longer exists).** The live `.py` is **unregistered** |
| **Registry references** | Backs named capability `household_cashflow`; used as canonical fixture path in `tests/meta/test_selective_verify.py` (5×), `test_change_intelligence.py`, `test_validation_orchestrator.py` |
| **API references** | None |
| **Currently executed** | **YES** — under property + capability tests |
| **Has tests** | **YES** — dedicated property and capability suites |
| **Canonical replacement** | None. `services/cashflow_service.py` exists but does **not** import this engine |
| **Migration risk** | **HIGH if removed.** Deleting breaks the `household_cashflow` capability suite **and** 3 meta-verification test modules that hardcode this path as a change-detection fixture |
| **Recommended future action** | **PRESERVE.** Decide ownership: either wire into `cashflow_service` or formally record as a parked capability. Also regenerate the provider registry so it reflects the live `.py` rather than the phantom `.parked`. |

---

## CANDIDATE 4 — Impure single-file engines (3 files)

`engines/balance_engine.py` · `engines/ledger_audit_engine.py` · `engines/reconciliation_engine.py`

| Field | Evidence |
|---|---|
| **Classification** | **D — Legacy but referenced** |
| **Direct import references** | `balance_engine` ← `engines/__init__.py` facade; `ledger_audit_engine` ← `audit_service`; `reconciliation_engine` ← `reconciliation_service` |
| **Test references** | 1 / 1 / 4 test files respectively |
| **Runtime/provider references** | All 3 registered as `style=single_file` engines in `architecture-provider.json` — **provider-required** |
| **Registry references** | Present in the (now stale) sqlite3 whitelist in `tests/architecture/test_layer_boundaries.py` |
| **API references** | Indirect via `audit` and `reconciliation` routers |
| **Currently executed** | **YES** — production paths |
| **Has tests** | **YES** |
| **Canonical replacement** | None. The *pattern* replacement is repository injection (as used by package engines) |
| **Migration risk** | **MEDIUM–HIGH.** 8 function-local `core.db.connection` imports. Converting to injected repositories changes call signatures used by services and tests |
| **Recommended future action** | **PRESERVE.** Plan a purity migration: introduce repository parameters, keep signatures backward-compatible, migrate one engine per program. |

---

## CANDIDATE 5 — `backend/src/utils/`

| Field | Evidence |
|---|---|
| **Classification** | **E — Legacy and unreferenced** |
| **Direct import references** | **0.** `grep -rn "src\.utils"` across `src/` and `tests/` returns **zero** hits |
| **Test references** | **0** |
| **Runtime/provider references** | None |
| **Registry references** | None |
| **API references** | None |
| **Currently executed** | Only as an empty package import if walked |
| **Has tests** | No |
| **Contents** | Single `__init__.py`, **0 bytes** |
| **Canonical replacement** | `src/common/` serves the shared-helper role |
| **Migration risk** | **VERY LOW** — no code references it |
| **Recommended future action** | Archival candidate. **DO NOT remove in Program H.** Confirm no external tooling globs `src/utils` before any future action. |

---

## CANDIDATE 6 — `backend/src/data/` (`__init__.py` + `finance.db`)

| Field | Evidence |
|---|---|
| **Classification** | **G — Local artifact** (+ **H** for `__init__.py` intent) |
| **Direct import references** | **0.** Nothing imports `src.data` |
| **Test references** | **0** |
| **Runtime/provider references** | None. Runtime DB path resolves to CWD-relative `data/finance.db` via `core/db/config.py`, **not** to `backend/src/data/` |
| **Currently executed** | No |
| **Git state** | `finance.db` is **TRACKED** (0 bytes); `__init__.py` is **IGNORED** by `backend/.gitignore:13:data/` |
| **Migration risk** | **LOW**, but see CI risks — the split tracked/ignored state is itself the hazard |
| **Recommended future action** | Hygiene program: untrack the 0-byte `finance.db`, and decide whether `src/data/` should exist at all. **Not in Program H.** |

---

## CANDIDATE 7 — Duplicate active implementations (Class F)

### 7a. `core/dtos/account_dto.py` ↔ `core/dtos/accounts_dto.py`

| Field | Evidence |
|---|---|
| **Classification** | **F — Duplicate active implementation** |
| **`account_dto` consumers** | `core/dtos/__init__.py`, `core/__init__.py`, `core/mappers/account_mapper.py` |
| **`accounts_dto` consumers** | `core/dtos/__init__.py`, `routers/accounts.py` |
| **Currently executed** | **BOTH** |
| **Migration risk** | **MEDIUM** — they are consumed by different layers (mapper vs router); merging changes API response shapes |
| **Recommended future action** | Ownership decision required. Neither is removable today. |

### 7b. `routers/health.py` ↔ `health.py`

| Field | Evidence |
|---|---|
| **Classification** | **F — Duplicate surface (benign)** |
| **Content** | `routers/health.py` is a 4-line pure re-export of `src.health` |
| **Registration** | `api.py:21,46` registers `src.health` **directly**. Verified 119 routes — **no double registration** |
| **Migration risk** | **VERY LOW** |
| **Recommended future action** | Pick one location for the health surface. Harmless meanwhile. |

### 7c. `ingest.py` ↔ `services/import_service.py`

| Field | Evidence |
|---|---|
| **Classification** | **F — Duplicate composition** (not duplicate logic) |
| **Shared dependencies** | Both wire `extraction.categorizer`, `metadata_extractor`, `statement_extractor` |
| **Distinction** | `ingest.py` = CLI entrypoint (`__main__`, `main()`); `import_service.py` = API path (+ orchestrator fan-out) |
| **Test references** | `ingest.py` ← 1 e2e test; `import_service` ← API/contract tests |
| **Migration risk** | **MEDIUM** — a shared pipeline module would need to preserve both CLI reporting and API/service semantics |
| **Recommended future action** | Extract a shared ingestion pipeline; keep both entrypoints. **Do not delete either.** |

---

## CANDIDATE 8 — `backend/src/structural/`

| Field | Evidence |
|---|---|
| **Classification** | **B — Canonical but misplaced** |
| **Direct import references** | **1** — `extraction/hybrid_extractor.py:28` |
| **Test references** | 0 direct (exercised via extraction tests) |
| **Currently executed** | **YES** — in the PDF extraction path |
| **Has tests** | Indirect |
| **Migration risk** | **LOW** — single importer |
| **Recommended future action** | Consider relocating under `extraction/`. Relocation only — **never deletion**. |

---

## CANDIDATE 9 — Stale references to removed modules (documentation/config only)

These are **not** source files; they are dangling references to files that no longer exist.

| Reference site | Points at | Filesystem | Action |
|---|---|---|---|
| `architecture-provider.json` | `engines/insight_generator.py` | **ABSENT** | Regenerate provider |
| `architecture-provider.json` | `engines/nudge_engine.py` | **ABSENT** | Regenerate provider |
| `architecture-provider.json` | `engines/behavior_engine.py` | **ABSENT** | Regenerate provider |
| `architecture-provider.json` | `engines/cashflow_engine.py.parked` | **ABSENT** | Regenerate provider |
| `tests/architecture/test_layer_boundaries.py:43` | `engines/behavior_engine.py` whitelist entry | **ABSENT** | Whitelist tightening (see below) |

**Functionality relocation is confirmed, not assumed:** `insight_generator` → `engines/behaviour_engine/insights.py` (`generate_behavioral_insights`, `generate_summary_text`); `nudge_engine` → `engines/behaviour_engine/nudges.py` (`generate_nudges`, `get_top_nudge`, `get_nudge_summary`). Both are exported from `behaviour_engine/__init__.py`. **No functionality was lost.**

### Stale sqlite3 whitelist — CANDIDATE, not defect

`tests/architecture/test_layer_boundaries.py` whitelists 4 engine files as "known legacy sqlite3 violations". **Verified: zero files under `src/engines/` import `sqlite3`.** The whitelist protects nothing and includes one non-existent file.

Removing the whitelist would **strengthen** verification. Program H explicitly forbids weakening verification and forbids modifying verification rules, so this is **recorded only**. Flagged for a future program.

---

## Summary — Removal Eligibility

| Candidate | Removable in Program H? | Removable at all today? |
|---|---|---|
| `db.py` | **NO** | No — 4 test fixtures depend on it |
| `common/database.py` | **NO** | Only with the `common/__init__` re-export change |
| `cashflow_engine.py` | **NO** | **No** — capability + meta-test dependencies |
| 3 impure engines | **NO** | No — production + provider-registered |
| `utils/` | **NO** | Lowest-risk archival candidate |
| `data/finance.db` | **NO** | Hygiene program only |
| DTO/health/ingest duplicates | **NO** | No — all actively consumed |
| `structural/` | **NO** | Relocation candidate only |

**Files deleted by Program H: 0. Files moved: 0. Files renamed: 0.**
