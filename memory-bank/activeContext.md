# Active Context

## Current Focus
Phase 3.1 — Capability Framework Hardening

## Recent Changes
- **Phase 3.1 Capability Framework Hardening (2026-07-29)**
  - **Discovery Repair**: Replaced stub `src/verification/runtime/discovery.py` with delegation to real implementation. Enhanced `tests/runtime/discovery.py`'s `discover_dependencies()` to generate all 8 required edge types (capability → engines, routers, services, repositories, unit tests, property tests, contract tests, capability tests, golden datasets, invariant tests).
  - **Self-Validator Fix**: Fixed `validate_dependency_chains()` to import from `runtime.discovery` instead of the stub module.
  - **Determinism**: Replaced timestamp-based `generated_at` with content hashes in `coVF_discover.py`, `selective_engine.py`, and `generate_contract_tests.py`. Added `tests/meta/test_determinism.py`.
  - **GitHub Actions**: Updated `backend.yml` with conditional job execution based on capability intelligence. Added determinism verification CI job.
  - **Capability Regression Tests**: Added `tests/meta/test_capability_regression.py` verifying no cross-capability leakage. Added `tests/meta/test_dependency_graph.py` validating graph completeness.
  - **Generated Artifacts**: `dependency-map.json` (197 edges, 11 capabilities, all edge types), `change-impact.json`, `selective-plan.json`.

## Next Immediate Steps
- Run full test suite to validate all changes
- Produce final capability framework health summary report
