# TESTING_ARCHITECTURE_BASELINE.md

> Generated: 2026-07-24
> Mode: READ ONLY — Architecture Assessment
> Scope: Complete testing ecosystem across backend/, frontend/, memory-bank/

---

## 1. Test Inventory

### 1.1 Backend Test Categories

| # | Category | Files | Purpose | Freq | Dependencies | Owner | Maintenance Cost | Redundancy |
|---|----------|-------|---------|------|-------------|-------|-----------------|------------|
| 1 | **Unit** | test_db.py, test_amortization.py, test_boundary.py | Pure function tests (paise parsing, math) | Every commit | None (no DB) | Core | Low | None |
| 2 | **Repository** | 9 files (test_account_balance_repository.py, test_account_link_repository.py, test_alert_repository.py, test_audit_repository.py, test_behaviour_repository.py, test_household_repository.py, test_institution_repository.py, test_pattern_repository.py, test_repository_smoke.py) | SQL CRUD verification | Every commit | FinanceDB, sqlite3, tempfile | Data | **High** (each reinvents DB setup) | **HIGH** — capability tests cover same CRUD |
| 3 | **Service** | 3 files (test_account_service.py, test_behaviour_service.py, test_services.py) | Business logic orchestration | Every commit | Mock repositories | Core | **High** (brittle mocks) | **HIGH** — capability tests cover same flows |
| 4 | **Router/API** | 4 files (test_account_router.py, test_behaviour_router.py, test_loan_routers.py, test_routers.py) | HTTP endpoint verification | Every commit | TestClient, FinanceDB | API | Medium | **HIGH** — contract tests cover same endpoints |
| 5 | **Engine** | 12 files (test_account_engine.py, test_behavior_engine.py, test_behaviour_engine_account.py, test_behaviour_engine_debt.py, test_behaviour_engine_income.py, test_behaviour_engine_integration.py, test_behaviour_engine_metrics.py, test_behaviour_engine_patterns.py, test_behaviour_engine_profile.py, test_behaviour_engine_wellness.py, test_credit_card_engine.py, test_recommendation_engine.py) | Business logic unit tests | Every commit | Engine modules | Core | Medium (duplication across files) | **MEDIUM** — behaviour engine split across 8 files |
| 6 | **Loan Engine** | 3 files (test_loan_engine_comprehensive.py, test_loan_engine_coverage.py, test_loan_engine_financial_correctness.py) + test_loan_engine_performance.py | Loan calculation verification | Every commit | Loan engine modules | Core | Medium | **HIGH** — 3 files for one engine |
| 7 | **Integration** | 2 files (test_audit_minimal.py, test_behaviour_engine_integration.py, test_reconciliation.py) | Cross-component end-to-end | Every commit | FinanceDB, multiple repos | Core | Medium | **MEDIUM** — overlaps with capability tests |
| 8 | **Determinism** | 2 files (test_determinism.py, test_reconciliation_determinism.py) | Replay stability, order independence | Every commit | balance_engine, repos | Core | Low | **MEDIUM** — overlaps with integration tests |
| 9 | **Smoke** | 1 file (test_repository_smoke.py) | Quick repository verification | Every commit | FinanceDB, repos | Data | Low | **HIGH** — redundant with repository tests |
| 10 | **Migration** | 2 files (test_migration_confidence_bps.py, test_migration_household.py) | Migration script correctness | One-time | Migration scripts | Data | Low (can delete after) | None |
| 11 | **Performance** | 1 file (test_loan_engine_performance.py) | Loan engine speed | Nightly | Loan engine | Core | Low (will rot) | None |
| 12 | **Architecture** | 1 file (architecture/test_layer_boundaries.py) | Import boundary enforcement | Every commit | — | Meta | Low | None |
| 13 | **Capability** | 11 files (capabilities/*/test_capability.py) | End-to-end business flow | Every commit | conftest.py, builders, golden datasets | Capability | Medium | **VERY HIGH** — the overlap hub |
| 14 | **Contract** | 5 files (contracts/routers/test_*.py) | OpenAPI contract compliance | Every commit | conftest.py, TestClient, app | API | Medium | **HIGH** — same endpoints as router tests |
| 15 | **Property** | 10 files (properties/*/test_*.py) | Invariant verification via Hypothesis | CI (150 ex) / Nightly (1000 ex) | conftest.py, producers | Core | Medium | **MEDIUM** — some overlap with invariants/ |
| 16 | **Invariant** | 3 files (invariants/test_*.py) + 10 domain/invariants/*.py | Domain rule verification | Every commit | Domain invariant modules | Core | Medium | **HIGH** — properties/ duplicates some invariants |
| 17 | **Golden Dataset** | 1 file (golden/test_regression.py) + 10+ dataset files | Scenario regression | Every commit | JSON datasets | Core | Medium | **MEDIUM** — overlaps with capability tests |
| 18 | **Meta** | 6 files (meta/test_*.py) | Tooling infrastructure verification | Every commit | backend/tools/*, memory-bank/generated/* | Meta | Medium | None (unique) |
| 19 | **Boundary** | 1 file (test_boundary.py) | Edge case verification | Every commit | — | Core | Low | None |

### 1.2 Frontend Test Categories

| # | Category | Files | Purpose | Freq | Dependencies | Owner | Maintenance Cost | Redundancy |
|---|----------|-------|---------|------|-------------|-------|-----------------|------------|
| 1 | **Contract (Vitest)** | 11 files (__tests__/api-contracts/*.contract.test.ts) | API contract compliance | Every commit | Vitest | Frontend | Medium | **MEDIUM** — partial backend overlap |
| 2 | **Playwright E2E** | 4 files (playwright/tests/*.spec.ts) | Browser e2e | Every commit | Playwright | Frontend | Medium | **HIGH** — duplicated in tests/specs/ |
| 3 | **E2E Specs** | 11 files (tests/specs/*.spec.ts) | Browser e2e (duplicate) | Every commit | Playwright? | Frontend | **High** | **VERY HIGH** — duplicates playwright/tests/ |
| 4 | **Visual Regression** | 1 file (tests/specs/visual-regression.spec.ts) | UI snapshot testing | Every commit | Playwright | Frontend | Medium | None |
| 5 | **App-level** | 1 file (tests/app.test.ts) | Application smoke | Every commit | Vitest | Frontend | Low | None |
| 6 | **CSS Integrity** | 1 file (tests/specs/css-integrity.spec.ts) | CSS class validation | Every commit | Playwright | Frontend | Low | None |
| 7 | **Health Check** | 1 file (tests/specs/health-check.spec.ts) | Service availability | Every commit | Playwright | Frontend | Low | None |
| 8 | **Performance** | 1 file (tests/specs/performance.spec.ts) | Page load timing | Nightly | Playwright | Frontend | Low (will rot) | None |

### 1.3 Test Infrastructure

| Component | Configuration | Notes |
|-----------|--------------|-------|
| Backend runner | pytest (via pyproject.toml) | No pytest config found in pyproject.toml |
| Frontend unit runner | Vitest (vitest.config.ts, vitest.setup.ts) | No component tests actually use this |
| Frontend e2e runner | Playwright (playwright.config.ts + playwright.config.m9.ts) | Dual configs — likely stale |
| Coverage | Not explicitly configured | No .coveragerc or pytest-cov config found |
| CI | verify-fast.sh | Runs ruff + mypy, no explicit test execution |

---

## 2. Duplicate Coverage Matrix

### 2.1 Backend — Same Behavior, Multiple Layers

| Business Flow | Root-Level | Service | Router | Contract | Capability | Property | Invariant | Golden | Total Files |
|--------------|-----------|---------|--------|----------|------------|----------|-----------|--------|-------------|
| **Loan CRUD + Schedule** | test_loan_engine_comprehensive.py, test_loan_engine_coverage.py, test_loan_engine_financial_correctness.py | test_services.py (partial) | test_loan_routers.py | contracts/routers/test_loans.py | capabilities/debt_management/test_capability.py | properties/lending/test_engine_properties.py | invariants/test_loan.py, domain/invariants/loan.py | golden/datasets/salary_plus_loan.json | **10** |
| **Behaviour Engine** | test_behavior_engine.py, test_behaviour_engine_account.py, test_behaviour_engine_debt.py, test_behaviour_engine_income.py, test_behaviour_engine_integration.py, test_behaviour_engine_metrics.py, test_behaviour_engine_patterns.py, test_behaviour_engine_profile.py, test_behaviour_engine_wellness.py | test_behaviour_service.py, test_services.py (partial) | test_behaviour_router.py | — | capabilities/pattern_analysis/test_capability.py | properties/behaviour/test_engine_properties.py | domain/invariants/behaviour.py | — | **13** |
| **Cashflow** | — | test_services.py (partial) | — | contracts/routers/test_cashflow.py | capabilities/household_cashflow/test_capability.py | properties/cashflow/test_engine_properties.py | invariants/test_cashflow.py, domain/invariants/cashflow.py | golden/datasets/normal_household.json, family_household.json | **7** |
| **Credit Cards** | test_credit_card_engine.py | — | — | contracts/routers/test_credit_cards.py | capabilities/credit_cards/test_capability.py | properties/credit_cards/test_engine_properties.py | domain/invariants/credit.py | golden/datasets/credit_card_revolver.json, cc_statement_scenario.json | **6** |
| **Reconciliation** | test_reconciliation.py, test_reconciliation_determinism.py | test_services.py (partial) | test_routers.py (partial) | — | capabilities/reconciliation/test_capability.py | — | — | — | **4** |
| **Forecasting** | — | — | — | contracts/routers/test_forecasting.py | capabilities/forecasting/test_capability.py | properties/forecasting/test_engine_properties.py | domain/invariants/forecast.py | — | **4** |
| **Account Management** | test_account_engine.py | test_account_service.py | test_account_router.py | contracts/routers/test_accounts.py | capabilities/account_management/test_capability.py | — | domain/invariants/account.py | — | **5** |

### 2.2 Backend — Repository Tests Duplicated by Capability Tests

Every `test_*_repository.py` file has overlapping coverage in `capabilities/*/test_capability.py` because capability tests exercise the full stack including repositories.

| Repository File | Duplicated By |
|----------------|--------------|
| test_account_balance_repository.py | capabilities/account_management/test_capability.py |
| test_account_link_repository.py | capabilities/account_management/test_capability.py |
| test_alert_repository.py | capabilities/financial_events/test_capability.py |
| test_audit_repository.py | capabilities/reconciliation/test_capability.py |
| test_behaviour_repository.py | capabilities/pattern_analysis/test_capability.py |
| test_household_repository.py | capabilities/household_cashflow/test_capability.py |
| test_institution_repository.py | capabilities/account_management/test_capability.py |
| test_pattern_repository.py | capabilities/pattern_analysis/test_capability.py |

### 2.3 Frontend — E2E Duplication

| Scenario | tests/specs/ | playwright/tests/ |
|----------|-------------|-------------------|
| Dashboard | tests/specs/dashboard.spec.ts | playwright/tests/dashboard.spec.ts |
| Navigation | tests/specs/navigation.spec.ts | playwright/tests/navigation.spec.ts |
| Transactions | tests/specs/transactions.spec.ts | playwright/tests/transactions.spec.ts |
| Accounts | — | playwright/tests/accounts.spec.ts |

### 2.4 Fixture Duplication

| Artifact | Locations | Count |
|----------|-----------|-------|
| `make_transaction` helper (copy-pasted) | test_behaviour_engine_patterns.py, test_behaviour_engine_wellness.py, test_behaviour_engine_profile.py | 3+ |
| `create_test_db` / `temp_db` fixture pattern | Every root-level test file | 35 |
| `_create_*_table` helper (inline SQL) | test_account_balance_repository.py, test_account_link_repository.py | 2 |
| Golden dataset as `.py` + `.json` pairs | credit_card_revolver, high_debt_household, irregular_income, normal_household, salary_plus_loan | 5 pairs |
| Frontend test fixtures | tests/fixtures/test-fixtures.ts + mocks/ + test-data/ | 3 locations |

### 2.5 Invariant Duplication

| Invariant | domain/invariants/ | invariants/ | properties/ |
|-----------|-------------------|-------------|-------------|
| Cashflow | cashflow.py | test_cashflow.py | test_cashflow.py, cashflow/test_engine_properties.py |
| Loan | loan.py | test_loan.py | test_loan.py, lending/test_engine_properties.py |
| Money | money.py | test_money.py | test_money_invariants.py |

---

## 3. Missing Coverage

### 3.1 Statement Upload Pipeline — CRITICAL GAP

The statement upload flow (csv_importer.py → statement_extractor.py → column_mapper.py → ingest.py) has **zero dedicated tests**. No test file exercises:
- CSV parsing with various formats
- Column mapping configuration
- Statement extraction from PDF
- Metadata extraction
- The full upload → parse → store pipeline

**Risk**: This is the primary data entry point. A bug here corrupts all downstream analytics.

### 3.2 Orchestration — CRITICAL GAP

The `backend/src/orchestration/` package has **zero test coverage**. No test file imports any orchestration module.

**Risk**: Orchestration is the central nervous system. Failures here cascade across all capabilities.

### 3.3 Financial Intelligence — HIGH GAP

The financial intelligence engine has only contract tests (test_forecasting.py contract). No engine-level tests validate:
- Cashflow forecast calculations
- Liquidity forecast logic
- Credit forecast accuracy
- Outlook generation

### 3.4 Dashboard API — HIGH GAP

Dashboard has:
- Frontend e2e tests (dashboard.spec.ts in both test dirs)
- No backend dashboard API tests
- No dashboard service unit tests

### 3.5 Recommendations — MEDIUM GAP

`test_recommendation_engine.py` exists but no property/invariant/golden tests validate recommendation correctness.

### 3.6 Investments — ZERO COVERAGE

No test files reference any investment-related modules. Full gap.

### 3.7 Transaction Intelligence — MEDIUM GAP

`capabilities/transaction_intelligence/test_capability.py` exists but `properties/transaction_intelligence/` has only `__init__.py` — no property tests for transaction categorization, pattern detection, or anomaly detection.

### 3.8 Cross-Capability Interactions — CRITICAL GAP

No test verifies interactions between capabilities, e.g.:
- Statement upload → reconciliation
- Credit card usage → behaviour profile
- Loan schedule → cashflow forecast
- Transaction data → dashboard summary

### 3.9 Database Migrations — LOW GAP

`test_migration_*.py` covers 2 migration scripts. 5 other migration scripts (migration_002 through migration_006) have no tests.

### 3.10 Money Invariants — ADEQUATE

`domain/invariants/money.py` + `test_money_invariants.py` + `properties/test_money_invariants.py` provide good coverage. However, these invariants are not enforced in production code — only tested in isolation.

### 3.11 Frontend-Backend Integration — CRITICAL GAP

No test validates that the frontend actually works with the backend in a realistic deployment. Contract tests validate the API schema, but:
- No end-to-end test with a real backend
- No test for error handling scenarios (500, timeout, network failure)
- No test for data format compatibility between frontend types and backend responses

---

## 4. Folder Architecture Review

### 4.1 Backend Tests

**Question**: Should backend tests remain inside `backend/tests/`?

**Answer**: ✅ YES. They are tightly coupled to backend source code, share the same Python environment, and test backend-specific modules. Moving them outside would:
- Break `sys.path.insert(0, ...)` imports (currently required)
- Complicate CI/CD (need separate Python env)
- Reduce developer ergonomics (can't run `pytest` from backend directory)

### 4.2 Frontend Tests

**Question**: Should frontend tests remain inside `frontend/tests/`?

**Answer**: ✅ YES, with a caveat. The `tests/specs/` directory duplicates `playwright/tests/`. One location should be eliminated. The `__tests__/` directory for contract tests is correctly placed within the frontend project.

### 4.3 Memory Bank

**Question**: Should memory-bank contain testing assets?

**Answer**: ❌ NO. The memory bank is for AI session context preservation only. Currently it contains:

| File | Status | Recommended Location |
|------|--------|-------------------|
| `memory-bank/generated/change-report.md` | ❌ MISPLACED | `backend/tests/generated/reports/` |
| `memory-bank/generated/change-report.json` | ❌ MISPLACED | `backend/tests/generated/reports/` |
| `memory-bank/generated/test-plan.md` | ❌ MISPLACED | `backend/tests/generated/reports/` |
| `memory-bank/generated/mutation-registry.json` | ❌ MISPLACED | `backend/tests/generated/` |
| `memory-bank/generated/validation-manifest.json` | ❌ MISPLACED | `backend/tests/generated/` |
| `memory-bank/capabilities/*.yaml` | ⚠️ BORDERLINE | These are capability manifests, not test artifacts. OK to keep if used for test discovery. |

### 4.4 Generated Validation Data

**Question**: Should generated validation data remain inside memory-bank?

**Answer**: ❌ NO. All generated test artifacts belong in `backend/tests/generated/` or a CI artifacts bucket. Rationale:
- Memory bank persists across sessions; generated data is transient
- Generated data can be large (JSON reports, mutation registries)
- CI/CD should not write to memory-bank
- Separation of concerns: context vs. artifacts

### 4.5 Ideal Locations

| Artifact Type | Current Location | Ideal Location | Rationale |
|--------------|-----------------|---------------|-----------|
| Generated reports | memory-bank/generated/ | backend/tests/generated/reports/ | Test outputs belong with tests |
| Snapshots | contracts/snapshots/ (referenced) | backend/tests/contracts/snapshots/ (if exists) | Keep with contract tests |
| Golden datasets | backend/tests/golden/datasets/ | ✅ Correct | Co-located with golden tests |
| Coverage artifacts | Not stored | backend/tests/generated/coverage/ | CI artifacts |
| Mutation reports | memory-bank/generated/ | backend/tests/generated/mutation/ | Test outputs |
| Temporary outputs | /tmp/ (via tempfile) | ✅ Correct (but should use tmp_path fixture) | Use pytest-native tmp_path |
| Test cache | .pytest_cache/ | ✅ Correct | Standard pytest behavior |
| Playwright snapshots | Not visible | frontend/playwright/snapshots/ | Follows Playwright convention |

---

## 5. Memory Bank Review

### 5.1 Files That Belong

| File | Justification |
|------|--------------|
| projectbrief.md | Core project context |
| activeContext.md | Session state machine |
| architecture.md | System architecture reference |
| capability-index.md | Capability metadata |
| capability-registry.yaml | Capability definitions |
| capability-status.json | Capability maturity tracking |
| cline-workflow.md | AI workflow instructions |
| database-map.md | Database schema documentation |
| dependency-map.md | Module dependency documentation |
| domain-invariants.md | Domain rule documentation |
| engine-contracts.md | Engine interface contracts |
| engine-map.md | Engine module map |
| engine-maturity.md | Engine maturity scoring |
| qea-rules.md | AI behavior rules |
| service-map.md | Service layer map |
| test-coverage.md | Coverage tracking (if summary only) |
| testing-strategy.md | Testing methodology |
| validation-architecture.md | Validation framework docs |
| validation-review.md | Validation audit results |

### 5.2 Files That Should Be Relocated (Phase 7)

| File | Violation | Destination |
|------|-----------|-------------|
| `memory-bank/generated/change-report.md` | Generated test artifact | `backend/tests/generated/reports/` |
| `memory-bank/generated/change-report.json` | Generated test artifact | `backend/tests/generated/reports/` |
| `memory-bank/generated/test-plan.md` | Generated test artifact | `backend/tests/generated/reports/` |
| `memory-bank/generated/mutation-registry.json` | Generated test artifact | `backend/tests/generated/` |
| `memory-bank/generated/validation-manifest.json` | Generated test artifact | `backend/tests/generated/` |

### 5.3 Files Requiring Investigation

| File | Concern |
|------|---------|
| `memory-bank/capabilities/*.yaml` | If > 50 files, these may bloat memory bank. Consider if all are actively referenced. |

---

## 6. Enterprise Testing Assessment

| Criterion | Score (1-10) | Justification |
|-----------|-------------|---------------|
| **Maintainability** | **4/10** | 35 root-level files with duplicated boilerplate. 3 fixture locations. 2 Playwright configs. Copy-pasted helpers. High coupling to implementation details. |
| **Scalability** | **5/10** | Adding a new capability requires writing tests in 3-4 layers (engine, service, router, capability). Not sustainable as codebase grows. |
| **Execution Speed** | **6/10** | Individual tests are fast (no network, in-memory DB). But 80+ backend files + 30 frontend files = slow full suite. No parallel execution configured. |
| **Isolation** | **5/10** | Root-level tests use tempfile (manual cleanup). Contract tests use shared `app` (no DB isolation). Capability tests have shared conftest but no DB isolation. |
| **Determinism** | **7/10** | Determinism tests explicitly verify replay stability. Property tests have Hypothesis profiles. But many tests depend on `datetime.now()`, which can produce flaky results. |
| **Reliability** | **5/10** | Contract tests accepting `(200, 500)` are unreliable (pass even when broken). Mock-based tests break when constructors change. `sys.path.insert` breaks in different working directories. |
| **Debuggability** | **4/10** | Failed tests use `tempfile` (no way to inspect DB). Contract tests don't validate response bodies. No structured test logging. |
| **CI Friendliness** | **6/10** | `verify-fast.sh` runs ruff + mypy but doesn't run tests. No CI config found. Property tests can be slow (1000 examples) without CI profile. |
| **Developer Onboarding** | **3/10** | New developer must learn: 3 import patterns, 2 fixture patterns, 3 test frameworks (pytest, Vitest, Playwright), 2 Playwright configs, sys.path manipulation. |
| **Long-term Evolution** | **4/10** | Tests are tightly coupled to implementation (mocks, raw SQL, exact JSON). Internal refactoring will break tests. No architecturally-evident testing patterns. |
| **Overall** | **4.9/10** | Below enterprise standard. Immediate consolidation needed to reduce maintenance burden. |

---

## 7. Test Adaptability (Coupling Analysis)

### 7.1 Tests Coupled to Implementation

| Coupling Type | Example Files | Risk Level | Recommended Mitigation |
|--------------|---------------|------------|----------------------|
| **Mock-based (constructor coupling)** | test_account_service.py, test_behaviour_service.py | CRITICAL | Replace with integration tests using real repositories |
| **Raw SQL fixtures** | All root-level test_*_repository.py files | HIGH | Use domain builders instead of inline INSERT statements |
| **sys.path.insert(0, ...)** | All root-level files + contracts/conftest.py + capabilities/conftest.py | HIGH | Install package with `pip install -e .` or set PYTHONPATH in pytest config |
| **tempfile.mkstemp + os.unlink** | 35 root-level files | MEDIUM | Use pytest's built-in `tmp_path` fixture |
| **Exact JSON assertions** | test_routers.py, contract tests | MEDIUM | Use structural matching (e.g., `assert_schema` helpers) |
| **datetime.now() in assertions** | test_behaviour_engine_patterns.py | MEDIUM | Use freezegun or pass dates as parameters |

### 7.2 Tests Coupled to Folder Structure

| File | Coupling | Risk |
|------|----------|------|
| meta/test_*.py (4x parent.parent.parent.parent) | PROJECT_ROOT = 4 levels up | Breaks if test file moves |
| capabilities/conftest.py (3x parent) | Capability manifest path | Breaks if directory structure changes |
| Domain invariants / properties overlap | Tests import from domain/invariants/ AND properties/ | Architecture drift over time |

### 7.3 Tests Coupled to DTO Internals

| File | Coupling |
|------|----------|
| test_behaviour_router.py | Asserts specific JSON fields in response |
| test_loan_routers.py | Asserts `rate_bps` field exists |
| test_services.py | Asserts `hasattr(result, "behavior_score")` |

### 7.4 Tests Coupled to Endpoint Names

| File | Endpoint | Risk |
|------|----------|------|
| test_routers.py | `/api/transactions` (old path) | May already be broken if migrated to `/api/v1/transactions` |
| test_behaviour_router.py | `/api/v1/behaviour/profile` | Coupled to exact URL path structure |

### 7.5 Tests Coupled to UI / CSS

| File | Coupling |
|------|----------|
| frontend/tests/specs/css-integrity.spec.ts | CSS class names |
| frontend/tests/specs/visual-regression.spec.ts | Pixel-level UI layout |

---

## 8. Error Analysis

### 8.1 Classification Framework

Based on code patterns (not run results), the following error categories exist:

| Category | Code | Description | Estimated Count | Effort to Fix |
|----------|------|-------------|----------------|---------------|
| **A — Real Code Defects** | N/A | Cannot determine without running tests | Unknown | High |
| **B — Broken Tests** | B1 | `tempfile.mkstemp` leak on assertion failure | 35 files | Low |
| **B — Broken Tests** | B2 | `datetime.now()` flakiness across date boundaries | 3+ files | Low |
| **C — Outdated Tests** | C1 | `test_routers.py` tests `/api/` instead of `/api/v1/` | 1 file | High (may be testing dead code) |
| **C — Outdated Tests** | C2 | `test_services.py` imports `BehaviorService` (old name) | 1 file | Medium |
| **D — Architecture Drift** | D1 | Mix of `from db import FinanceDB` and `from src.db import FinanceDB` | 20+ files | Medium |
| **D — Architecture Drift** | D2 | Mix of `from engines.X import Y` and `from src.engines.X import Y` | 10+ files | Medium |
| **E — Import/Path Problems** | E1 | `sys.path.insert(0, ...)` with varying parent depths (2, 3, 4) | 35 files | Low |
| **E — Import/Path Problems** | E2 | Meta tests use `Path(__file__).parent.parent.parent.parent` (brittle) | 6 files | Low |
| **F — Configuration Issues** | F1 | Two Playwright configs (playwright.config.ts + playwright.config.m9.ts) | 2 files | Low |
| **F — Configuration Issues** | F2 | `vitest.setup.ts` exists but no component tests use it | 1 file | Low |
| **G — Generated Code Issues** | G1 | `memory-bank/generated/*` may be stale | 5+ files | Medium |
| **H — False Positives** | H1 | Contract tests accepting `status_code in (200, 500)` | 5+ tests | Low |

### 8.2 Estimated Error Reduction After Consolidation

| Phase | Category | Errors Eliminated | Cumulative |
|-------|----------|-------------------|------------|
| Phase 2 (merge engine tests) | D1, D2 | ~30% | 30% |
| Phase 3 (standardize imports) | E1, E2 | ~20% | 50% |
| Phase 4 (eliminate duplicates) | C1, C2 | ~15% | 65% |
| Phase 5 (upgrade contracts) | H1 | ~5% | 70% |
| Phase 7 (memory bank cleanup) | G1 | ~5% | 75% |

---

## 9. Coverage Quality

### 9.1 Over-Tested Code

| Module | Test Files | Redundancy Ratio | Value per Test |
|--------|-----------|-----------------|---------------|
| Loan Engine | 10 test files across all layers | 10:1 | **Low** — 3 engine files could be 1 |
| Behaviour Engine | 13 test files across all layers | 13:1 | **Low** — 8 root-level files could be 1 |
| Account Repository | 4 test files (balance, link, engine, router) | 4:1 | **Low** — 3 are covered by capability tests |

### 9.2 Under-Tested Code (Critical)

| Module | Gap | Severity |
|--------|-----|----------|
| `backend/src/orchestration/` | **Zero tests** | CRITICAL |
| `backend/src/extraction/` | **Zero tests** | CRITICAL |
| `backend/src/csv_importer.py` | No dedicated tests | CRITICAL |
| `backend/src/statement_extractor.py` | No dedicated tests | CRITICAL |
| `backend/src/ingest.py` | No dedicated tests | CRITICAL |
| `backend/src/core/` | No tests found | HIGH |
| `backend/src/audits/` | No tests found | HIGH |
| `backend/src/routers/dashboard.py` | No tests (frontend e2e only) | MEDIUM |
| Investment modules | **Zero tests** | MEDIUM |

### 9.3 Tests Providing Little Long-Term Value

| Test | Why |
|------|-----|
| Root-level `test_*_repository.py` (all 9) | Capability tests cover same CRUD operations with higher confidence |
| `test_repository_smoke.py` | Redundant with repository tests |
| `test_loan_engine_performance.py` | Will rot; performance testing needs dedicated infrastructure |
| `test_migration_confidence_bps.py` | One-time migration verification |
| `test_migration_household.py` | One-time migration verification |
| Contract tests accepting `(200, 500)` | Provide false confidence; must be upgraded or removed |

### 9.4 Tests Providing Highest Confidence

| Test | Why |
|------|-----|
| `test_db.py` (paise parsing) | Tests fundamental money invariant with edge cases |
| `test_determinism.py` | Tests replay stability — critical for financial correctness |
| `properties/*` | Hypothesis tests verify invariants across hundreds of generated inputs |
| `domain/invariants/*` | Explicit domain rule documentation and verification |
| `golden/test_regression.py` | End-to-end scenario regression with known-correct datasets |

### 9.5 Mutation Testing Value

| Module | Value | Suggested Approach |
|--------|-------|-------------------|
| `db.py` (_parse_amount_paise) | HIGH | Arithmetic mutations (change + to -, use float instead of Decimal) |
| Loan amortization | HIGH | Arithmetic, off-by-one, boundary condition mutations |
| Cashflow engine | MEDIUM | Comparison mutations (>, >=, <, <=) |
| Behaviour engine | LOW | Too many if/else paths; focus on profile classification logic |
| Recommendation engine | MEDIUM | Threshold mutations (change FOIR limit) |

### 9.6 Property Testing Opportunities

| Current Approach | Better Approach | Module |
|-----------------|----------------|--------|
| Example-based loan schedule tests | Property: "sum of principal payments = original principal" | Loan engine |
| Example-based cashflow tests | Property: "total inflows - outflows = net change" | Cashflow engine |
| Example-based wellness score | Property: "wellness score is monotonic with savings rate" | Behaviour engine |
| Example-based balance computation | Property: "running balance = opening + sum(deposits) - sum(withdrawals)" | Balance engine |
| Example-based reconciliation | Property: "confidence is monotonic with amount match" | Reconciliation engine |

---

## 10. Phased Implementation Roadmap

### Phase 1: Foundation (Week 1) — No test behavior changes

**Goal**: Create shared infrastructure that all tests can use.

**Steps**:
1. Create `backend/tests/conftest.py` with:
   - `finance_db` fixture using `tmp_path` (replaces 35 `tempfile.mkstemp` calls)
   - `test_client` fixture with isolated DB
   - `transaction_builder` helper (replaces 3+ `make_transaction` copies)
2. Move `domain/builders/` → `backend/tests/builders/`
3. Move `domain/generators/` → `backend/tests/generators/`

**Validation**: All existing tests pass.

**Risk**: None (no existing code modified).

---

### Phase 2: Consolidate Root-Level Tests (Week 2)

**Goal**: Reduce 35 root-level files to ~20 by merging duplicates.

**Steps**:
1. Merge `test_loan_engine_comprehensive.py` + `test_loan_engine_coverage.py` + `test_loan_engine_financial_correctness.py` → `backend/tests/engines/test_loan_engine.py`
2. Merge 8 behaviour engine files → `backend/tests/engines/test_behaviour_engine.py`
3. Merge `test_account_engine.py` + related → `backend/tests/engines/test_account_engine.py`
4. Merge `test_credit_card_engine.py` → `backend/tests/engines/test_credit_card_engine.py`
5. Delete `test_repository_smoke.py` (redundant)
6. Merge `invariants/` (3 files) with `domain/invariants/` (10 files) → single `invariants/` directory

**Validation**: Run full pytest suite. No deleted files. All behavior preserved. Count root-level files — target ≤ 20.

**Risk**: Low. Merged files keep all original assertions.

---

### Phase 3: Standardize Imports (Week 3)

**Goal**: Zero `sys.path.insert(0, ...)` calls.

**Steps**:
1. Add `[tool.setuptools.packages.find]` to `pyproject.toml`
2. Run `pip install -e .` in backend for all developers
3. Remove all `sys.path.insert(0, ...)` from test files
4. Fix all imports to use `from src.xxx import YYY` consistently
5. Standardize `from db import FinanceDB` → `from src.db import FinanceDB` (if applicable)

**Validation**: `pytest` runs from any working directory. All imports resolve without path manipulation.

**Risk**: Low. Mechanical find-and-replace.

---

### Phase 4: Eliminate Duplicate Coverage (Week 3-4)

**Goal**: Remove redundant test layers. Each behavior tested in exactly one layer.

**Steps**:
1. **Repository layer**: Remove `test_*_repository.py` files that duplicate capability tests. Keep only repository tests that test complex queries (filters, joins, aggregations).
2. **Router layer**: Remove router tests that duplicate contract tests. Keep only router tests for middleware, authentication, or error handling not covered by contracts.
3. **Service layer with mocks**: Convert `test_account_service.py` (mocked) to integration test with real DB. Keep `test_behaviour_service.py` (complex orchestration) but reduce mock scope.
4. **Frontend**: Choose one e2e location (`playwright/tests/` or `tests/specs/`). Delete the other. Recommend keeping `playwright/tests/` (standard Playwright convention).
5. **Invariant overlap**: Merge `invariants/` + `domain/invariants/` + `properties/` partial overlaps into unique invariants only.

**Validation**: All tests pass. Test count reduced by ~30%. No behavior lost.

**Risk**: Medium. Must verify duplicate removal doesn't remove unique edge cases.

---

### Phase 5: Upgrade Contract Tests (Week 4)

**Goal**: Contract tests provide real OpenAPI schema validation, not just status code checks.

**Steps**:
1. Generate or maintain OpenAPI schema from FastAPI routes
2. Add schema validation to contract tests (e.g., `assert response matches OpenAPI schema`)
3. Replace `assert status_code in (200, 500)` with specific expected responses
4. Add response body structure validation

**Validation**: Contract tests fail when API contract is violated, not just when endpoints crash.

**Risk**: Low. Adding assertions, not removing.

---

### Phase 6: Property Test Expansion (Week 5)

**Goal**: Add property-based tests for all critical financial logic.

**Steps**:
1. Add property tests for loan amortization (sum of principal = original)
2. Add property tests for cashflow (inflows - outflows = net)
3. Add property tests for balance computation (monotonic invariants)
4. Add property tests for reconciliation (confidence scoring)
5. Add property tests for wellness score (range invariants)

**Validation**: Hypothesis runs pass with 150 examples (CI profile). Invariants hold across generated inputs.

**Risk**: Low. Adding new tests, not modifying existing.

---

### Phase 7: Memory Bank Cleanup (Week 5)

**Goal**: Memory bank contains only AI session context.

**Steps**:
1. Create `backend/tests/generated/` directory
2. Move `memory-bank/generated/*` → `backend/tests/generated/`
3. Update meta tests to reference new paths
4. Add `backend/tests/generated/` to `.gitignore`

**Validation**: Meta tests still pass. No files left in `memory-bank/generated/`.

**Risk**: Low. File move only.

---

### Phase 8: Frontend Unification (Week 6)

**Goal**: Single test runner, no duplication, component-level tests.

**Steps**:
1. Delete one of the duplicate e2e directories (`tests/specs/` or `playwright/tests/`)
2. Delete stale `playwright.config.m9.ts`
3. Add component-level unit tests for key frontend components
4. Standardize fixture location (use `mocks/` as single source)
5. Configure Vitest for component testing with proper setup

**Validation**: Frontend tests pass. Coverage includes component level.

**Risk**: Medium. Requires frontend refactoring expertise.

---

### Phase 9: Coverage Expansion (Week 6-8)

**Goal**: 90% coverage for critical financial logic, zero critical gaps.

**Steps**:
1. **Statement upload**: Add tests for csv_importer, statement_extractor, column_mapper, ingest
2. **Orchestration**: Add tests for all orchestration workflows
3. **Financial intelligence**: Add engine-level tests for forecasting
4. **Dashboard**: Add backend dashboard API tests
5. **Investments**: Add basic smoke tests for investment modules
6. **Transaction intelligence**: Add property tests for categorization and anomaly detection
7. **Cross-capability**: Add integration tests for capability interactions

**Validation**: Coverage report shows ≥90% for critical modules. No untested production code paths.

**Risk**: Medium. Requires understanding of complex business logic.

---

### Phase 10: CI/CD Integration (Week 8)

**Goal**: Tests run automatically on every commit with appropriate profiles.

**Steps**:
1. Configure CI to run:
   - **Fast track** (every commit): Unit + Repository + Service + Router + Contract + Capability (20 examples)
   - **Full track** (PR merge): All backend + frontend + property (150 examples)
   - **Nightly**: Property (1000 examples) + Performance
2. Add coverage reporting to CI
3. Add test result publishing

**Validation**: CI pipeline runs all tests. Coverage reports available.

**Risk**: Low. Standard CI configuration.

---

## Appendix A: File Count Summary

| Directory | Files | Status After Migration |
|-----------|-------|----------------------|
| `backend/tests/` (root) | 35 | ~15 (merge 8 behaviour → 1, 3 loan → 1, delete smoke + migration) |
| `backend/tests/architecture/` | 1 | 1 (keep) |
| `backend/tests/calibration/` | 0 | 0 |
| `backend/tests/capabilities/` | 11 | 11 (keep — single source of truth for e2e) |
| `backend/tests/contracts/` | 7 | 7 (keep — upgrade assertions) |
| `backend/tests/domain/` | 10 | 0 (move builders/ + generators/ + invariants/ to top-level) |
| `backend/tests/golden/` | 12 | 12 (keep — deduplicate .py/.json pairs) |
| `backend/tests/invariants/` | 3 | ~8 (merge with domain/invariants/) |
| `backend/tests/meta/` | 6 | 6 (keep — update paths) |
| `backend/tests/properties/` | 12 | 12 (keep — deduplicate invariant overlap) |
| `backend/tests/engines/` | 0 | ~5 (new — merged from root-level) |
| `backend/tests/builders/` | 0 | ~5 (new — moved from domain/builders/) |
| `backend/tests/generators/` | 0 | ~1 (new — moved from domain/generators/) |
| `backend/tests/generated/` | 0 | ~5 (new — moved from memory-bank/generated/) |
| `backend/tests/services/` | 0 | ~1 (optional — if service integration tests extracted) |
| **Total Backend** | **~80** | **~60** |
| `frontend/tests/` | 15 | ~8 (delete specs/ duplicates, keep utils + fixtures) |
| `frontend/__tests__/` | 11 | 11 (keep) |
| `frontend/playwright/` | 6 | 6 (keep as single e2e source) |
| **Total Frontend** | **~32** | **~25** |
| `memory-bank/generated/` | 5 | 0 (move to backend/tests/generated/) |
| **Grand Total** | **~117** | **~85** |
| **Reduction** | | **~27%** |
