# Active Context

## Current Focus
Testing infrastructure cleanup and consolidation (Milestones 1-5)

## Recent Changes
- Created root `backend/tests/conftest.py` with shared `finance_db`, `db_path`, `test_client` fixtures and `make_transaction` helper
- Added `[tool.pytest.ini_options]` to `pyproject.toml` with `pythonpath = ["src"]`, markers, and warning filters
- Fixed module name collision: renamed `invariants/test_cashflow.py` to `invariants/test_cashflow_invariants.py`
- Consolidated 3 loan engine test files (`test_loan_engine_comprehensive.py`, `test_loan_engine_coverage.py`, `test_loan_engine_financial_correctness.py`) → `engines/test_loan_engine.py` (59 tests preserved)
- Deleted `test_repository_smoke.py` (redundant with capability tests) and `test_loan_engine_performance.py` (will rot)
- Moved migration tests to `tests/migrations/` directory
- Moved generated artifacts from `memory-bank/generated/` to `backend/tests/generated/` (reports/ subdir)
- Updated meta tests to reference new paths in `backend/tests/generated/`

## Next Immediate Steps
- Consolidate behaviour engine tests (8 root-level files → `engines/test_behaviour_engine.py`)
- Remove remaining duplicate repository/service/router tests (9 files)
- Frontend test cleanup (consolidate `tests/specs/` and `playwright/tests/`)
- Quality stabilization: run full suite, fix lint/type errors