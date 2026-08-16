# Program K — Test Fixture Migration off Legacy `FinanceDB`

**Status: GATE PASSED**
**Date:** 2026-08-08
**Scope:** `backend/tests/fixtures/` only. No `backend/src` production source modified. No legacy module deleted.

---

## K.1 — Consumer Location & Classification

Repository-wide search for `from src.db import`, `import src.db`, `FinanceDB(`.

| Classification | Location | Count | Action |
|---|---|---|---|
| **Compatibility layer** | `src/db.py` (defines `FinanceDB`) | 4 self-refs | **PRESERVED — untouched** |
| **Compatibility layer** | `src/common/database.py` (lazy import) | 2 | **PRESERVED — untouched** |
| **Production** | — | **0** | none |
| **Docstring text only** | `src/routers/{accounts,behaviour,credit_cards,financial_intelligence}.py`, `src/core/db/schema.py` | 5 | none — prose, not imports |
| **Test fixture (real import)** | `tests/fixtures/database.py` | 1 | **MIGRATED** |
| **Test fixture (real import)** | `tests/fixtures/benchmark_fixtures.py` | 1 | **MIGRATED** |
| **Test fixture (docstring only)** | `tests/fixtures/client.py` | 1 | docstring updated; already typed `Any` |
| **Test fixture (docstring only)** | `tests/fixtures/seed.py` | 3 | docstring updated; already typed `Any` |
| **Documentation** | `docs/**` (historical audits) | ~60 | none — point-in-time records |

**Refinement of the Program H finding:** of the four fixture consumers, only **two** carried a real Python import. `client.py` and `seed.py` referenced `FinanceDB` solely in docstrings and consume the object through the already-generic `Any` type, accessing only `.db_path`.

---

## K.2 — Fixture Requirements Analysis

I measured what the suite actually consumes from the fixture object before replacing anything:

```
$ grep -rn "finance_db\." tests/
      2 finance_db.db_path        # <-- the ONLY attribute accessed
$ grep -rn "with finance_db" tests/
      (no results)                # <-- never used as a context manager
```

| Requirement | Needed? | Evidence |
|---|---|---|
| Schema initialization | **No (per-test)** | The session template already ran `create_all` + `run_migrations` + `verify_schema` |
| Migrations | **No (per-test)** | Same — carried in the copied template |
| Seeded data | Separate concern | Handled by `seed.py` via `get_connection_context` |
| Connection lifecycle | Retained defensively | Not currently used, but preserved |
| Transaction/context-manager behaviour | Retained defensively | Not currently used, but preserved |
| `db_path` attribute | **Yes** | The only attribute read by any test |

### Key finding — redundant work per test

`FinanceDB.__init__` unconditionally runs `create_all` → `run_migrations` → `verify_schema`. The fixture called it **on a file already copied from the fully-initialized pristine template**, so this DDL work was repeated for every single test, partially defeating the Program T0 template optimization.

**Proof the copy is sufficient** (run before making the change):
```
template tables: 30
copy tables    : 30
IDENTICAL SCHEMA AFTER COPY: True
verify_schema(copy) passed: True
```

---

## K.3 / K.4 — Migration, One Fixture at a Time

### Fixture 1 — `tests/fixtures/database.py`

| | |
|---|---|
| **Old dependency** | `from src.db import FinanceDB` → `FinanceDB(db_path=...)` |
| **New dependency** | `from src.core.db.connection import get_connection` + local `TestDatabase` handle |

Introduced a `TestDatabase` class **inside the existing fixture module** (no new framework, no second fixture system) that preserves the consumed surface:

- `db_path` attribute — the only attribute any test reads
- `_connect()` / `_get_conn()` via the canonical `get_connection` factory
- `__enter__` / `__exit__` with commit-on-success / rollback-on-error — behaviourally identical to `FinanceDB`

**Why this is semantically safe:**
1. Only `.db_path` is read anywhere in the suite — verified by exhaustive grep.
2. The context-manager and connection semantics were carried over verbatim, so any future use behaves identically.
3. Per-test DDL was dropped **only after proving** the copied template yields a byte-identical 30-table schema that passes `verify_schema`.
4. `get_connection` is the same factory `FinanceDB._connect()` delegated to — the PRAGMA/WAL configuration is unchanged.
5. The session template still uses `core.db.schema` exactly as before; that path was already canonical.

**Tests executed:**

| Suite | Result |
|---|---|
| `tests/unit/repositories` | **58 passed** (23.09s vs 23.04s baseline) |
| `tests/unit/repositories + unit/services + invariants` | **129 passed** |
| `tests/contract` (exercises `seeded_db` → `test_client`) | **161 passed** in 40.6s (was 68.6s) |
| `tests/unit/repositories -n 4` (xdist locking check) | **58 passed** — no locking regression |

### Fixture 2 — `tests/fixtures/benchmark_fixtures.py`

| | |
|---|---|
| **Old dependency** | `from src.db import FinanceDB` inside `benchmark_finance_db_init()` |
| **New dependency** | `from src.core.db.schema import create_all, run_migrations, verify_schema` |

Renamed `benchmark_finance_db_init` → `benchmark_db_init` and `benchmark_finance_db_on_copy` → `benchmark_db_init_on_copy`. Also removed the now-unnecessary `contextlib_import()` helper (it existed only to close the `FinanceDB` connection object).

**Why this is semantically safe:** `FinanceDB.__init__` performed exactly `create_all` → `run_migrations` → `verify_schema`. The benchmark now calls those three functions directly, so **the quantity being measured is unchanged**. This script is a standalone measurement tool: pytest collects **0 tests** from it and no CI script references it.

**Verification — the benchmark runs and reproduces the T0 gain:**
```
Fresh init (old):        4.269s
Copy + init (new):       0.170s
Speedup per test:        25.1x
```

### Fixtures 3 & 4 — `client.py`, `seed.py`

No import changes were required (docstring references only, `Any`-typed, `.db_path`-only access). Docstring wording updated for accuracy. Both are covered by the 161 passing contract tests.

---

## K.5 — Legacy Infrastructure Preserved

| File | State |
|---|---|
| `backend/src/db.py` | **PRESENT — byte-for-byte unmodified** |
| `backend/src/common/database.py` | **PRESENT — byte-for-byte unmodified** |

```
$ grep -rn "from src\.db import" tests/
NONE  <-- all fixture consumers migrated
```

**Updated classification of `src/db.py`:**

> Compatibility infrastructure with **zero production consumers and zero remaining fixture consumers**. Its only remaining importer is `src/common/database.py`, itself a dormant deprecated shim with zero consumers.

This is a **classification change only**. Neither file was deleted, and future retirement remains a separate evidence-driven program.

---

## K.6 — Performance Validation

| Measurement | Baseline (pre-K) | After migration | Verdict |
|---|---|---|---|
| `tests/unit/repositories` | 23.04s / 58 passed | 23.09s / 58 passed | No regression |
| `tests/contract` | 68.60s / 161 passed | 40.60s / 161 passed | **Improved** |
| First-test setup (session template) | 4.32s | 4.50s | Unchanged (template build) |
| Benchmark speedup | ~26× (T0 target) | **25.1×** | **Preserved** |
| xdist `-n 4` | — | 58 passed, no hangs | No locking contention |

**Program T0 gains preserved.** No reintroduction of ~4.3s per-test `FinanceDB` initialization — in fact the redundant per-test DDL was removed. No autouse seeding, no secondary connections, no per-test schema inspection introduced.

---

## Gate Results

| Suite | Result |
|---|---|
| Fixture/repository tests | **58 passed** |
| Repositories + services + invariants | **129 passed** |
| Contract tests | **161 passed** |
| Combined affected suite | **290 passed** |
| Capability + cashflow properties | **32 passed** |
| Integration (excl. pre-existing failure) | **19 passed** |
| Architecture + meta | **111 passed** |
| xdist parallel locking check | **58 passed** |

### PRE-EXISTING failure encountered and correctly isolated

`tests/integration/e2e/test_upload_pipeline.py` — **13 failed**.

Root cause: the test imports `src.column_mapper`, but the module lives at `src.extraction.column_mapper` (`ModuleNotFoundError`).

**Proof it is PRE-EXISTING, not caused by Program K:**
```bash
git stash push tests/fixtures/database.py tests/fixtures/benchmark_fixtures.py
pytest tests/integration      # -> 13 failed, 21 passed   (IDENTICAL)
git stash pop
```
The failure count and identity are unchanged with my edits removed. These tests use **no database fixtures at all** (verified by grep). Out of scope — not modified.

The three `loan_engine` Hypothesis failures documented in Program H remain **PRE-EXISTING** and were not touched.

### Files changed (Program K)
- `backend/tests/fixtures/database.py` — migrated to `core.db`; added local `TestDatabase` handle
- `backend/tests/fixtures/benchmark_fixtures.py` — migrated to `core.db.schema`

### Files deleted: **NONE**
### `backend/src` production source modified: **NONE**
### Verification rules modified: **NONE**
