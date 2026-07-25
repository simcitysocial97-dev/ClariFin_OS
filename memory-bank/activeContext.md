# Active Context

## Current Focus
Testing infrastructure cleanup and consolidation (Milestones 1-5)

## Recent Changes
- **Phase 5: Directory Restructuring complete**
  - Renamed: `properties` → `property`, `contracts` → `contract`, `capabilities` → `capability`
  - Moved engine tests to `tests/unit/engines/<domain>/`
  - Moved repositories/services to `tests/unit/`
  - Moved orchestration/pipeline to `tests/integration/`
  - Unified invariant definitions and tests under `tests/invariant/`
  - Moved golden dataset Python loaders to `tests/golden/builders/`
  - Added `client` fixture alias, fixed all broken imports and golden builder paths
  - Added missing test files: contract routers, property tests, invariant stubs, golden datasets, domain builders, unit investment tests
  - Updated `test_coverage_integrity.py` with path fallbacks for renamed directories
  - **967 tests collected successfully** (882 passing; remaining failures are pre-existing service-level issues)

## Next Immediate Steps
- Update capability manifests in `memory-bank/capabilities/*.yaml` to reference new test paths
- Run full suite and fix remaining failures
- Quality stabilization: run ruff, mypy, pyright
