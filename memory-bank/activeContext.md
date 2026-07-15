# Active Context

## Coverage & Traceability Framework (CTF) — Completed

- **Coverage Scanner**: Created `backend/tools/check_coverage.py`
  - Scans capability manifests and validates all referenced paths
  - Detects orphan modules and tests (53 found)
  - Generates all coverage artifacts
- **Generated Artifacts** in `memory-bank/generated/`:
  - `coverage.md` - Human-readable maturity matrix
  - `coverage.json` - Machine-readable JSON
  - `capability-registry.yaml` - Generated from manifests
  - `traceability.md` - Per-capability dependency chains
  - `change-impact.md` - What breaks if you modify a file
  - `README.md` - Documentation
- **Meta Tests**: Created `backend/tests/meta/test_coverage_integrity.py`
  - Validates generated artifacts exist and are valid
  - Verifies all referenced paths in manifests exist
- **Pipeline**: Updated `scripts/verify-local.sh`
  - verify-fast → coverage scanner → coverage integrity → architecture → capabilities → properties → golden → adaptive

## Status: COMPLETED ✓

All 9 meta tests passing. Capability manifests are the source of truth.
Orphan modules detected: 10 routers, 6 services, 15 engines, 10 repositories, 1 property test, 11 invariants.
These represent either legacy code or work-in-progress.
