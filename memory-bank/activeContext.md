# Active Context

## Capability Validation Framework (CVF) — Completed

- **Memory Bank**: Created `capabilities/` directory with 11 YAML manifests
  - household_cashflow, debt_management, credit_cards, financial_health, forecasting
  - transaction_intelligence, reconciliation, financial_events, recommendations
  - account_management, pattern_analysis
- **Registry**: Created canonical `capability-registry.yaml`
- **Index**: Generated `capability-index.md` with coverage table
- **Capability Smoke Tests**: Created 11 capability directories under `tests/capabilities/`
  - Each directory contains `capability.yaml` and `test_capability.py`
  - 3 tests per capability: import/bootstrap, minimal execution, invariant validation
  - All tests reuse existing builders, golden datasets, and invariant functions
- **Test Pipeline**: Updated `scripts/verify-local.sh` to include capability smoke tests
  - New stage: `pytest tests/capabilities` runs after architecture, before properties
- **Coverage**: 11 capabilities, each with 3 smoke tests, golden datasets, invariants
- **Total Artifacts**: 11 YAML manifests + 11 test files + registry + index

## Status: COMPLETED ✓

All 23 capability smoke tests passing. Fixed mypy and ruff issues in CVF files.
Pre-existing test failures in test_services.py (missing credit_cards table - schema issue).
CVF is ready for use - new capabilities can follow the established pattern.
