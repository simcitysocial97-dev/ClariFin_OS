# Program M — Baseline & Consumer Inventory (Phase M0)

**Date:** 2026-08-08
**Baseline commit:** `0c8410c3` (HEAD)
**Scope:** Retire `backend/src/db.py` and `backend/src/common/database.py` compatibility layer.
**Canonical replacement:** `backend/src/core/db/` (`get_db_path`, `get_connection`, `create_all`, `run_migrations`, `verify_schema`, `db_transaction`).

---

## Compatibility layer files

| File | Role | Docstring status |
| ---- | ---- | ---------------- |
| `backend/src/db.py` | `FinanceDB` class — backward-compatible wrapper; re-exports `_parse_amount_paise` from `common.calculations`. | marked `.. deprecated::` |
| `backend/src/common/database.py` | `get_db()` — deprecated shim returning `FinanceDB()`; docstring states "zero production consumers". | marked `.. deprecated::` |

---

## Consumer inventory (repository-wide, verified independently of Program L counts)

Searched: `from db import`, `import db`, `src.db`, `from src.db`, `FinanceDB`, `get_db`, `src.common.get_db`, `common.database`.

### ACTIVE EXECUTABLE CONSUMERS (must migrate before deletion)

| # | Consumer | Import | Usage | Replacement |
| - | -------- | ------ | ----- | ----------- |
| 1 | `backend/src/common/database.py` | `from src.db import FinanceDB` (lazy, L30) + TYPE_CHECKING (L22) | `get_db()` returns `FinanceDB()` | DELETE entire module; remove re-export from `common/__init__.py` |
| 2 | `backend/src/common/__init__.py` | `from .database import get_db` (L9); `"get_db"` in `__all__` (L24) | Re-exports deprecated `get_db` | Remove the `get_db` import + `__all__` entry |
| 3 | `tools/generators/generate_synthetic_data.py` | `from db import FinanceDB` (L32) | ONLY in `clear_database()` L161: `FinanceDB(str(db_path))` to ensure schema exists | `from src.core.db.schema import create_all, run_migrations, verify_schema`; call `create_all(str(db_path))` (which also runs migrations+verify) |
| 4 | `backend/tests/unit/repositories/test_db.py` | `from db import _parse_amount_paise` (L12) | Resolves to `src.db` because `db.py` re-exports `_parse_amount_paise` | `from src.common.calculations import _parse_amount_paise` (canonical definition) |

### NON-CONSUMERS (documentation / strings / legacy references — excluded)

| Reference | File | Why excluded |
| --------- | ---- | ------------ |
| `FinanceDB` string | `tests/fixtures/benchmark_fixtures.py` (L21-23) | Docstring only; states it now calls `create_all`/`run_migrations`/`verify_schema` directly |
| `src.db.FinanceDB` / `FinanceDB` string | `tests/fixtures/database.py` (L13, L43) | Docstring only; "no longer depends on the `src.db.FinanceDB` compatibility" |
| `FinanceDB` string | `tests/fixtures/seed.py` (L74, L77), `client.py` (L20) | Docstring/type-hint prose only |
| `FinanceDB` string | `routers/accounts.py`, `behaviour.py`, `credit_cards.py`, `financial_intelligence.py` (L6) | Comment only: "no FinanceDB import" |
| `FinanceDB` | `tools/development/mutation_discovery.py` (L77-78) | String literal in MUTATION_TARGETS list, not an import |
| `FinanceDB` | `backend/scripts/scan_test_anti_patterns.py` (L7,11,146,147,153,155,259-268) | AST pattern scanner source, not an import |
| `core/db/config` `get_db_path` etc. | multiple `src/**` modules | These import the CANONICAL `src.core.db`, not the compatibility layer — expected |

---

## Replacement-path mapping

| Deprecated API | Canonical equivalent | Behavior preserved |
| -------------- | -------------------- | ------------------ |
| `FinanceDB(db_path)` (construct → create_all + run_migrations + verify_schema) | `create_all(db_path)` | `FinanceDB.__init__` calls exactly `create_all`, `run_migrations`, `verify_schema` in sequence; `create_all` is idempotent (CREATE IF NOT EXISTS) |
| `get_db()` → `FinanceDB()` | (removed — no production consumer) | N/A |
| `db.py` re-export `_parse_amount_paise` | `src.common.calculations._parse_amount_paise` | Same function object, identical behavior |

---

## Gate M0 decision

- Undocumented active consumer **discovered**: `tests/unit/repositories/test_db.py` (relied on `db.py`'s `_parse_amount_paise` re-export). This is an executable import, not merely a string reference.
- Per STOP condition, this is reported. It is NOT a blocker: it is migrated (not deleted) to the canonical `src.common.calculations` location, preserving test behavior.
- No external/public compatibility contract beyond the above was found.
- No canonical `core/db` capability is missing: schema init, connection, transaction, path resolution, verification are all present.

**Gate M0: PASS** (with one additional required migration: `test_db.py` import path). Proceed to M1.
