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

## Change Intelligence Framework (CIF) — Completed

- **CIF Tool**: Created `backend/tools/change_intelligence.py`
  - Analyzes changed files via git diff or CLI arguments
  - Builds in-memory graph from capability-registry.yaml
  - Classifies risk levels (LOW/MEDIUM/HIGH/CRITICAL)
  - Computes weighted risk scores for multi-file changes
  - Generates change-report.md, change-report.json, and test-plan.md
- **Meta Tests**: Created `backend/tests/meta/test_change_intelligence.py`
  - Validates report generation and JSON schema
  - Verifies risk/confidence values are valid
  - Tests UNKNOWN capability handling for untracked files
- **Pipeline**: Updated `scripts/verify-local.sh`
  - Added CIF stage after coverage integrity

## Selective Verification Framework (SVF) — Completed

- **SVF Tool**: Created `backend/tools/selective_verify.py`
  - Executes only tests impacted by changed files
  - Auto-regenerates stale change-report.json
  - Supports --plan, --run, --json, --full flags
  - Generates selective-plan.md, selective-summary.json, verification-matrix.md, selective-history.json
- **Meta Tests**: Created `backend/tests/meta/test_selective_verify.py` (8 tests passing)
  - Validates plan generation and duplicate removal
  - Tests invalid path handling and JSON parsing
  - Verifies verification matrix output
- **Pipeline**: Updated `scripts/verify-local.sh`
  - Added VERIFY_MODE=selective environment variable support
  - Full verification remains default behavior

## Verification Flow

```
Developer changes code
    ↓
verify-fast
    ↓
Coverage Scanner
    ↓
Change Intelligence → change-report.json
    ├── What changed?
    ├── What's affected?
    ├── How risky is it?
    └── What should be tested? (SVF uses this)
    ↓
[VERIFY_MODE=full] Full pipeline: Architecture → Capabilities → Properties → Golden → Adaptive
[VERIFY_MODE=selective] Selective: Only impacted test suites
```

## Status: COMPLETED ✓

All CIF/SVF meta tests passing. Risk scoring uses weighted sums (LOW=1, MEDIUM=2, HIGH=4, CRITICAL=8).
Orphan modules detected: 10 routers, 6 services, 15 engines, 10 repositories, 1 property test, 11 invariants.