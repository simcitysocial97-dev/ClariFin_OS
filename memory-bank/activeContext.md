# Active Context

## Architecture Validation Created
- **Memory Bank**: Created `architecture.md`, `service-map.md`, `dependency-map.md`, `database-map.md`, `testing-strategy.md`
- **Architecture Tests**: Created `tests/architecture/test_layer_boundaries.py` (10 tests) + `README.md`
- **Violations Found**: 
  - `engines/balance_engine.py`, `ledger_audit_engine.py`, `reconciliation_engine.py` import sqlite3 (forbidden)

## Invariants Testing Created
- **Invariants**: Created `tests/invariants/test_money.py`, `test_cashflow.py`, `test_loan.py`
  - `test_money.py`: `assert_all_paise_integers()` - validates integer paise
  - `test_cashflow.py`: `assert_surplus_balances()` - income - expense == surplus
  - `test_loan.py`: `assert_schedule_valid()` - principal decreases, final balance == 0

## Adaptive Test Selection Configured
- **pytest-testmon**: Already installed (v2.2.0)
- **verify-local.sh**: Updated with adaptive selection fallback logic
- **When testmon runs**: When `.testmondata` exists and pytest-testmon importable
- **When full suite runs**: Fallback when testmon unavailable or cache missing

## Golden Dataset Regression Framework Created
- Created `tests/golden/datasets/` with 4 JSON scenario files
- Created `tests/golden/test_regression.py` with semantic comparison
- `_normalize_for_comparison()` ignores timestamps/IDs for stable assertions

## Enterprise CI Pipeline Created (8 stages)
- `.github/workflows/quality-gate.yml` created:
  1. **fast**: ruff + pyright static analysis
  2. **architecture**: layer boundary tests (parallel with properties)
  3. **properties**: hypothesis property tests (parallel with architecture)
  4. **integration**: docker + API validation
  5. **contract**: schemathesis against OpenAPI
  6. **golden**: golden dataset validation
  7. **snapshot**: golden dataset change detection
  8. **mutation**: mutmut on engines/ only
- Mutation testing: verifies properties catch wrong logic by introducing mutations
## ADF Framework Completed
- Created `tests/domain/` structure with invariants, generators, builders
- Created 6 invariant modules: `tests/domain/invariants/*.py`
- Created Hypothesis strategies in `tests/properties/conftest.py`
- Written 26 property tests covering Cashflow, Loan, Forecast, Credit engines
- All tests pass ✅ | ruff check ✅ | mypy check ✅

## Next Steps
