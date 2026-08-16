# Program M — Final Evidence Report

**Date:** 2026-08-08
**Final commit:** `ab3046f6`
**Baseline commit:** `0c8410c3`
**Canonical provider:** `backend/src/core/db/`

---

## 1. Removed Files

- `backend/src/db.py` — `FinanceDB` compatibility wrapper + `_parse_amount_paise` re-export.
- `backend/src/common/database.py` — `get_db()` deprecated shim.

Both were tracked source; now deleted and no longer tracked.

---

## 2. Migrated Consumers (before → after)

| Consumer | Before | After | Behavior preserved |
| -------- | ------ | ----- | ------------------ |
| `backend/src/common/database.py` | `from src.db import FinanceDB` (`get_db` shim) | **DELETED**; re-export removed | yes |
| `backend/src/common/__init__.py` | `from .database import get_db` | re-export removed; package retained (calculations/enrichment/formatting/parsing) | yes |
| `tools/generators/generate_synthetic_data.py` | `from db import FinanceDB`; `FinanceDB(str(db_path))` | `from src.core.db.schema import create_all`; `create_all(str(db_path))` | yes (idempotent: create_all+run_migrations+verify_schema = `FinanceDB.__init__`) |
| `backend/tests/unit/repositories/test_db.py` | `from db import _parse_amount_paise` | `from src.common.calculations import _parse_amount_paise` (canonical) | yes (same function) |
| `backend/tests/fixtures/database.py` | `from src.db import FinanceDB` (Program K, uncommitted) | committed Program K migration: `src.core.db.connection/schema`, `TestDatabase` handle | yes |

> Note: Program K's `fixtures/database.py` migration was present in the working tree but
> had never been committed. Including it in the retirement commit was required so the
> committed tree does not import the now-deleted `src.db` module. This is the necessary
> companion to the retirement, not an unrelated change.

---

## 3. Remaining Compatibility References

**Zero executable references** to `src.db`, `FinanceDB`, `get_db` (shim), `common.database`,
`from db import`, or `import db` remain in code.

Remaining references are documentation/string-only (excluded by design):
- `tests/fixtures/benchmark_fixtures.py`, `seed.py`, `client.py` (docstrings)
- `routers/{accounts,behaviour,credit_cards,financial_intelligence}.py` (comments)
- `tools/development/mutation_discovery.py` (string literal in target list)
- `backend/scripts/scan_test_anti_patterns.py` (AST scanner source)
- `backend/src/core/db/schema.py` (historical docstring)

---

## 4. Canonical Database Ownership

`backend/src/core/db/` is now the **sole production database implementation**:
- `config.py` — path resolution + PRAGMA settings
- `connection.py` — `get_connection`, `get_connection_context`
- `schema.py` — `create_all`, `run_migrations`, `verify_schema` (30-table schema)
- `transaction.py` — `db_transaction`
- `health.py` — connectivity / schema health

No other production module provides database initialization or connection logic.

---

## 5. Regression Results (per gate)

| Gate | Result | Detail |
| ---- | ------ | ------ |
| 1 — Import integrity | **PASS** | 224 production `src.*` modules import clean |
| 2 — Architecture / Meta | **PASS** | 111 passed (architecture 50 + meta 61) |
| 3 — `run_fast_checks.sh backend` | **PASS** | ruff ✓, black ✓, unit 760 ✓, architecture 50 ✓, meta 61 ✓; exit 0 |
| 4 — `runtime/verify.py quick` | **PASS** | from repo root: Passed 1 / Failed 0, 67.9s |
| 5 — `runtime/verify.py backend` | **PRE-EXISTING FAILURES ONLY** | `run_backend_verification.sh` failed 5× — all in `tests/properties` (loan_engine + financial_events Hypothesis). Confirmed none import the deleted layer. |
| 6 — Clean checkout | **PASS** | worktree at `ab3046f6`: retired modules absent, `core/db` + `src/data/__init__.py` present, 217 `src` modules import, 116 arch/meta/test_db tests pass |

> Gate 4 note: `verify.py quick` initially reported a stale cache "FAIL" when executed from
> `backend/` (the orchestrator runs `run_fast_checks.sh` with CWD `backend/`, where the
> script's internal `cd backend` fails). Run from the repo root it executes the real step
> and PASSES. The failure was a CWD artifact, not a regression.

---

## 6. Pre-existing Failures (NOT attributed to Program M)

The following property/Hypothesis tests fail independently of this program (they test
pure engine math and do not use the deleted compatibility layer):

- `tests/properties/loan_engine/test_floating_rate_properties.py` (2)
- `tests/properties/loan_engine/test_foreclosure_properties.py` (1)
- `tests/properties/loan_engine/test_metrics_properties.py` (2)
- `tests/properties/loan_engine/test_prepayment_properties.py` (1)
- `tests/properties/financial_events/test_lineage_properties.py` (1)

These match the previously documented Hypothesis `loan_engine` failures. No test was
weakened, loosened, or suppressed to make any gate pass.

---

## 7. Git Cleanliness

- Tracked compat files: **none** (both removed).
- No `.pyc`, `.mypy_cache`, or local DB artifact tracked.
- No unrelated modifications included in the Program M commit (`ab3046f6`).
- `git check-ignore` confirms source files are not ignored.

---

## 8. Clean-Checkout Result

A git worktree built from `ab3046f6` proves:
- `backend/src/db.py` — **absent** (confirmed by `ls`).
- `backend/src/common/database.py` — **absent**.
- `backend/src/core/db/__init__.py` — **present**.
- `backend/src/data/__init__.py` — **present** (Program K rename).
- Full `src` import integrity — **217 modules, 0 failures**.
- `tests/unit/repositories/test_db.py` + `tests/architecture` + `tests/meta` — **116 passed**.
- Migrated generator imports cleanly (`create_all` resolves to `src.core.db.schema`).

**The repository works correctly without the retired compatibility modules.**

---

## Program M Status: COMPLETE

All success criteria satisfied. `FinanceDB` and `get_db` compatibility surfaces are
retired; `backend/src/core/db/` is the sole canonical database implementation; no runtime
verification rules, tests, or behaviors were changed; no suppressions introduced; no
unrelated files reorganized.
