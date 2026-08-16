# Test Infrastructure Canonicalization — Migration Notes

## Program T0

## Summary

Refactored the backend test harness from a monolithic `tests/conftest.py` into a
modular `tests/fixtures/` package with 7 focused plugins. Introduced a session-
scoped schema snapshot that is file-copied per test instead of re-running DDL +
migrations on every test function. Removed the autouse database seeding fixture
and replaced it with an explicit `seeded_db` fixture. Eliminated secondary
sqlite3 connections and per-test PRAGMA schema inspection.

## Files Added

| Path | Purpose |
|------|---------|
| `tests/fixtures/__init__.py` | Package marker |
| `tests/fixtures/pytest_config.py` | Custom pytest marker registration |
| `tests/fixtures/hypothesis.py` | Hypothesis profiles + `hypothesis_settings` fixture |
| `tests/fixtures/database.py` | `_pristine_db_template`, `finance_db`, `db_path`, `temp_db` |
| `tests/fixtures/seed.py` | `seeded_db` (explicit seeding, no autouse) |
| `tests/fixtures/client.py` | `test_client`, `client` (API test clients) |
| `tests/fixtures/builders.py` | `make_transaction`, `make_reconciliation_match` |
| `tests/fixtures/factories.py` | Domain builder class re-exports |
| `tests/fixtures/benchmark_fixtures.py` | Performance benchmark script |

## Files Modified

| Path | Change |
|------|--------|
| `tests/conftest.py` | Reduced to thin `pytest_plugins` loader + backward-compat re-exports |
| `pyproject.toml` | (no changes) |

## Files Unchanged

- `tests/properties/conftest.py` — strategies and `hypothesis_settings` fixture preserved
- `tests/capability/conftest.py` — unchanged
- `tests/contract/conftest.py` — unchanged
- `tests/__init__.py` — unchanged
- `tests/domain/builders/*` — unchanged

## Behavior Changes

### 1. Autouse Seeding Removed

**Before:**
```python
@pytest.fixture(autouse=True)
def seed_test_database(finance_db):
    # Ran for EVERY test, opened a secondary sqlite3 connection,
    # performed PRAGMA table_info inspection, printed debug output.
```

**After:**
```python
@pytest.fixture(scope="function")
def seeded_db(finance_db):
    # Explicit opt-in. Uses canonical connection. No PRAGMA inspection.
    # No debug prints.
```

Tests that need baseline data must now request `seeded_db` explicitly.
The `client` and `test_client` fixtures already depend on `seeded_db`, so
all contract and e2e tests continue to receive seeded data automatically.

### 2. Schema Snapshot (Pristine Template)

**Before:**
- Every `finance_db` fixture called `FinanceDB()` which ran:
  - `create_all()` — ~3.3s
  - `run_migrations()` — ~1.0s
  - `verify_schema()` — ~0.004s
  - Total: **~4.4s per test**

**After:**
- One session-scoped `_pristine_db_template` runs full init once: **~4.4s**
- Each `finance_db` copies the template (~0.001s) + runs `FinanceDB()` on copy (~0.15s)
- Total per test: **~0.15s** (26x faster)

### 3. Secondary Connection Elimination

**Before:**
```python
conn = sqlite3.connect(db_path)  # secondary connection
cursor.execute("PRAGMA table_info(account_balance_history)")
cursor.execute("PRAGMA table_info(account_links)")
```

**After:**
```python
with get_connection_context(db_path) as conn:
    conn.execute("INSERT ...")
# Single canonical connection. No PRAGMA inspection.
```

### 4. Debug Prints Removed

Removed `print("DEBUG account_balance_history columns:", history_cols)` and
similar debug statements from the seed logic.

## Fixture Dependency Graph

```
_pristine_db_template (session) ──► finance_db (function) ──► db_path
                                     └──► seeded_db (function) ──► test_client ──► client
                                     └──► temp_db (function)
```

## Backward Compatibility

| Old Import Path | New Source | Status |
|-----------------|-----------|--------|
| `from tests.conftest import make_transaction` | `tests.fixtures.builders` | Preserved via re-export |
| `from tests.conftest import make_reconciliation_match` | `tests.fixtures.builders` | Preserved via re-export |
| `from tests.conftest import AccountBuilder` | `tests.fixtures.factories` | Preserved via re-export |
| `from tests.conftest import TransactionBuilder` | `tests.fixtures.factories` | Preserved via re-export |
| `from tests.properties.conftest import cash_summary_strategy` | `tests.properties.conftest` | Unchanged |
| `fixture: finance_db` | `tests.fixtures.database` | Preserved |
| `fixture: db_path` | `tests.fixtures.database` | Preserved |
| `fixture: temp_db` | `tests.fixtures.database` | Preserved |
| `fixture: test_client` | `tests.fixtures.client` | Preserved |
| `fixture: client` | `tests.fixtures.client` | Preserved |
| `fixture: hypothesis_settings` | `tests.fixtures.hypothesis` | Preserved |
| `markers: capability, contract, property, ...` | `tests.fixtures.pytest_config` | Preserved |

## pytest-xdist Compatibility

- Session-scoped `_pristine_db_template` creates one template per xdist worker.
- Function-scoped fixtures copy the template to unique temp paths per test.
- No shared mutable state between workers.
- File copy is atomic and thread-safe for distinct files.

## Performance Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Fresh DB init per test | 4.4s | 0.15s | 26x faster |
| Seed inserts | 0.13s (with secondary conn + PRAGMA) | 0.13s (canonical) | Same |
| Estimated 1200-test suite | ~88 min | ~3.5 min | **96% faster** |

## Zero-Regression Verification

- Unit tests: pass (189 core tests in 0.44s)
- Invariant tests: pass (3 tests in 0.30s)
- Behaviour engine tests: pass (197 tests in 0.98s)
- Reconciliation engine tests: pass (15 tests in 76.78s)
- Service tests: pass (15 tests in 109.29s)
- Contract/e2e tests: pre-existing failure (`ModuleNotFoundError: No module named 'backend'` in `src/routers/accounts.py` — production bug, not related to this refactor)

## Known Limitations

1. **Contract tests are broken by a pre-existing production bug.** The FastAPI app fails to import because `src/routers/accounts.py` contains `from backend.src.engines.account_engine import AccountEngine`. This is outside the scope of the test infrastructure refactor.
2. **PytestAssertRewriteWarning** is emitted for `tests.fixtures.factories` because the root conftest.py imports from it before pytest's plugin system loads it. This is harmless.
3. The `properties/conftest.py` hypothesis profiles (`fast`, `normal`, `deep`) are separate from the global profiles (`dev`, `ci`) registered in `hypothesis.py`. This preserves existing behavior.
