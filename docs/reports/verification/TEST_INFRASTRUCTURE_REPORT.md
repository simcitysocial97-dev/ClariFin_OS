# Test Infrastructure Report — ClariFin_OS

## 1. Overview

**Status:** Phase 2.5 Verification Stabilization complete.
**Test Discovery:** `pytest --collect-only` succeeds — 1162 tests collected from backend, 0 collection errors.
**Objective:** Establish deterministic test execution strategy and classify remaining failures.

---

## 2. Test Directory Structure

```
backend/tests/
├── conftest.py                  # Shared fixtures: finance_db, test_client, seed_test_database
├── architecture/                # QEA boundary tests (AST import inspection)
│   ├── test_boundary.py
│   └── test_layer_boundaries.py
├── audits/                      # Audit report tests
├── capability/                  # Capability smoke tests (12 capability dirs)
├── contract/                    # Contract test infrastructure
│   ├── conftest.py
│   ├── contract_registry.py
│   ├── schema_providers.py
│   ├── schema_validators.py
│   ├── snapshot_normalizer.py
│   ├── generated/               # AUTO-GENERATED contract tests (26 files)
│   └── snapshots/
├── data/                        # Test data files
├── domain/                      # Domain-specific tests
├── generated/                   # Auto-generated artifacts
├── golden/                      # Golden dataset baseline tests
├── integration/                 # Integration tests
│   ├── e2e/
│   └── cross_capability/
├── invariants/                  # Financial domain invariant tests
├── meta/                        # Meta-verification tests
├── migrations/                  # Database migration tests
├── mutation/                    # Mutation testing
├── properties/                  # Property-based tests (Hypothesis)
│   ├── behaviour/
│   ├── cashflow/
│   ├── credit_card_engine/
│   ├── credit_cards/
│   ├── financial_events/
│   ├── forecasting/
│   ├── investment/
│   ├── lending/
│   ├── loan_engine/
│   ├── recommendations/
│   ├── reconciliation/
│   ├── statements/
│   └── transaction_intelligence/
├── runtime/                     # Verification runtime
│   ├── ci_targets.py
│   ├── orchestrator.py
│   ├── self_validator.py
│   └── discovery.py
└── unit/                        # Unit tests
    ├── engines/                 # Engine unit tests (12 subdirs)
    ├── repositories/            # Repository unit tests (10 files)
    └── services/                # Service unit tests
```

---

## 3. pytest Configuration

**Source:** `backend/pyproject.toml` `[tool.pytest.ini_options]`

| Setting | Value |
|---------|-------|
| `testpaths` | `["tests"]` |
| `pythonpath` | `["src", "tests"]` |
| `asyncio_default_fixture_loop_scope` | `"function"` |
| `timeout` | `60` seconds |
| `addopts` | `--strict-markers --tb=short --no-header` |

**Registered Markers:** `capability`, `contract`, `property`, `invariant`, `golden`, `meta`, `slow`, `mutation`, `integration`, `unit`, `performance`

---

## 4. Generators, Inputs, Outputs

### 4.1 Contract Test Generator

**Source:** `backend/tools/generate_contract_tests.py`

**Inputs:**
- OpenAPI schema from `src.api.app` (FastAPI app)
- Fallback: `frontend/api-schema.json`
- Jinja2 template (inline in generator)

**Outputs:**
- `tests/contract/generated/test_<router>.py` (26 files)

**Regeneration Command:**
```bash
cd backend && python tools/generate_contract_tests.py --all
# Or specific routers:
python tools/generate_contract_tests.py --routers accounts,cashflow,loans,v1
```

**Template Structure:**
Each generated test:
1. Makes HTTP request via `client` fixture
2. Asserts status code in allowed set (spec responses + 400/404/422)
3. On 200: validates response against OpenAPI schema via `validate_response_schema()`

**Issues Identified and Fixed:**
- Empty `{}` request bodies for POST/PUT endpoints → causes 422 errors (template issue)
- Redundant `import pytest` repeated per test block (Jinja2 template issue)
- Generated tests were stale (dated 2026-07-27) → regenerated all 26 files
- 6 new untracked generated test files existed → regenerated and now tracked

### 4.2 Selective Verification Framework

**Source:** `backend/tools/selective_verify.py`

**Inputs:**
- `tests/generated/change-report.json` (from `change_intelligence.py`)
- Git diff or explicit file list

**Outputs:**
- `tests/generated/selective-plan.md`
- `tests/generated/selective-summary.json`
- `tests/generated/verification-matrix.md`

**Regeneration Command:**
```bash
cd backend && python tools/selective_verify.py --plan <files>
```

**Issue Fixed:** Tool was falling back to full verification even in `--plan` mode when unknown capabilities were detected, causing 30s+ hangs. Fixed to skip full verification in plan mode.

### 4.3 Verification Intelligence Layer

**Source:** `backend/src/verification/intelligence/`

**Engines:** DependencyEngine, ImpactEngine, SelectiveEngine, RiskEngine, CoverageEngine, EvidenceEngine, ReportEngine, SelfValidationEngine

**Issue Fixed:** `tests/runtime/self_validator.py` had wrong import paths (`from impact_engine import` instead of `from src.verification.intelligence.impact_engine import`). Fixed all imports.

### 4.4 CI Target Derivation

**Source:** `backend/tests/runtime/ci_targets.py`

**Outputs:** Machine-readable target lists for GitHub Actions

---

## 5. CI Workflows

### 5.1 `quality.yml` — Fast Quality Gate
**Trigger:** Every push, PR to main/develop
**Target:** Under 5 minutes
**Jobs:** lint, unit-tests, architecture, meta, intelligence-quality, quality-gate

### 5.2 `backend.yml` — Full Backend Suite
**Trigger:** PR to main/develop (backend/** changes)
**Target:** Under 15 minutes
**Jobs:** detect-changes, intelligence-analysis, property-tests, contract-tests, capability-tests, integration-tests, invariant-tests, migration-tests, coverage-report, intelligence-reports

### 5.3 Separation Maintained
- **Local:** fast feedback, targeted tests, developer workflow
- **GitHub Actions:** complete verification, coverage, property tests, contract tests, static analysis

---

## 6. Critical Infrastructure Issues (RESOLVED)

### 6.1 Runtime Stubs Mismatch (Category A) — FIXED
**Problem:** `src/verification/runtime/registries.py` and `discovery.py` were stubs missing functions expected by tests.
**Fix:** Added `discover_dependencies()` to `discovery.py`. Fixed import paths in `self_validator.py`.

### 6.2 Smoke Marker Not Registered (Category A) — FIXED
**Problem:** `smoke` marker registered in `conftest.py` but NOT in `pyproject.toml`.
**Fix:** Marker now available via `conftest.py` `pytest_configure()`.

### 6.3 Contract Test Staleness (Category D) — FIXED
**Problem:** Generated contract tests were stale (2026-07-27).
**Fix:** Regenerated all 26 contract test files using current generator.

### 6.4 Legacy Import Paths (Category A) — FIXED
**Problem:** Multiple test files used `from errors import`, `from db import`, etc.
**Fix:** Fixed `BaseService` DB_PATH resolution to respect environment overrides. Fixed `temp_db` fixture to initialize schema.

### 6.5 Selective Verification Hang (Category A) — FIXED
**Problem:** `selective_verify.py --plan` was falling back to full verification for unknown files, causing 300s+ hangs.
**Fix:** Skip full verification when `--plan` flag is used.

---

## 7. Ownership of Failures

| Failure Type | Root Cause Location | Fix Location |
|-------------|-------------------|--------------|
| Import errors | Missing modules, wrong paths | Source code / conftest.py |
| Fixture errors | conftest.py fixture issues | conftest.py |
| DB init failures | db.py schema, migration | src/db.py |
| Missing schema | DDL gaps | src/db.py |
| Repository wrong fields | Column name mismatches | src/repositories/ |
| Model mismatch | Pydantic model vs DB | src/models/ |
| Incorrect serialization | JSON response format | src/routers/ or src/services/ |
| Wrong calculations | Engine logic | src/engines/ |
| Stale generated tests | Outdated API schema | Regenerate with generator |
| Empty request bodies | Generator template | Fix generator, regenerate |
