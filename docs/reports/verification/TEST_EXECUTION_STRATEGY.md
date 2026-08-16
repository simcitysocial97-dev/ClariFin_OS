# Test Execution Strategy — ClariFin_OS

## Overview

Deterministic test execution in 4 layers. Each layer provides progressively
broader coverage. Run layers sequentially during development; run only Layer 4
before merge or in CI.

**Principle:** Database issues first → Repository issues second → Business logic issues third.

**Do not modify architecture. Do not reorganize folders. Do not suppress failures.**

---

## Layer 1 — Smoke

**Purpose:** Fast feedback on imports, startup, database initialization, and basic repositories.

**Command:**
```bash
cd backend && python -m pytest tests/unit/repositories/test_db.py tests/unit/test_money.py tests/unit/test_errors.py -q --tb=short --timeout=30
```

**Target runtime:** Under 2 minutes.

**What it covers:**
- Python import paths resolve correctly
- FastAPI app starts without errors
- Database initialization (`FinanceDB.__init__`) succeeds
- Basic repository CRUD operations work
- Core model instantiation works
- Schema verification passes

---

## Layer 2 — Database Contract

**Purpose:** Verify schema correctness, repository correctness, and API contracts.

**Command:**
```bash
cd backend && python -m pytest tests/unit/repositories tests/contract --tb=short --timeout=60 -q
```

**Target runtime:** Under 15 minutes (with parallel execution `-n auto`).

**What it covers:**
- Database schema matches DDL (`_verify_schema()`)
- Repository SQL queries return correct columns
- Repository methods handle edge cases (empty results, not found)
- API contract tests validate OpenAPI schema compliance
- Model serialization matches database contracts
- Foreign key constraints are satisfied

**Test files:**
- `tests/unit/repositories/test_*.py` — 10 repository test files
- `tests/contract/generated/test_*.py` — 26 generated contract test files
- `tests/contract/conftest.py` — contract test fixtures

---

## Layer 3 — Engine Verification

**Purpose:** Verify calculations, invariants, and mathematical correctness.

**Command:**
```bash
cd backend && python -m pytest tests/unit/engines tests/properties --tb=short --timeout=60 -q
```

**Target runtime:** Under 30 minutes (with parallel execution `-n auto`).

**What it covers:**
- Engine calculation correctness (EMI, amortization, cashflow)
- Financial invariants (paise integrity, balance consistency)
- Property-based tests (Hypothesis) for mathematical properties
- Edge cases in financial formulas
- Determinism of calculations

**Test files:**
- `tests/unit/engines/*/` — Engine unit tests
- `tests/properties/*/` — Property-based tests (Hypothesis)

---

## Layer 4 — Full Verification

**Purpose:** Complete verification before merge or in CI.

**Command:**
```bash
cd backend && python -m pytest --tb=short --timeout=120 -q
```

**Target runtime:** Under 60 minutes (with `-n auto` parallel execution).

**What it covers:**
- All of Layers 1-3
- Capability tests (`tests/capability/`)
- Invariant tests (`tests/invariants/`)
- Golden dataset tests (`tests/golden/`)
- Architecture boundary tests (`tests/architecture/`)
- Meta/registry tests (`tests/meta/`)
- Migration tests (`tests/migrations/`)
- Integration tests (`tests/integration/`)
- Audit tests (`tests/audits/`)

**CI equivalent:**
```bash
# quality.yml — fast gate (every push)
ruff check . && black --check . && pytest tests/unit/ && pytest tests/architecture/ && pytest tests/meta/

# backend.yml — full suite (PR to main/develop)
python -m runtime.ci_targets --property | xargs pytest
python -m runtime.ci_targets --contract | xargs pytest
python -m runtime.ci_targets --capability | xargs pytest
pytest tests/integration/
python -m runtime.ci_targets --invariant | xargs pytest
pytest tests/migrations/
python -m runtime.ci_targets --all | xargs pytest --cov=. --cov-report=json:tests/generated/coverage.json
```

---

## Failure Classification

Every failing test must be classified into one of four categories:

### Category A — Infrastructure Failure
**Examples:** import errors, fixtures, database initialization, missing schema
**Fix:** Immediately — fix the root cause in source code
**Priority:** Highest

### Category B — Data Contract Failure
**Examples:** repository returns wrong fields, model mismatch, incorrect serialization
**Fix:** At repository/model boundary — modify the authoritative source
**Priority:** High

### Category C — Business Logic Failure
**Examples:** wrong calculations, incorrect financial rules
**Fix:** Domain code — modify the engine or service
**Priority:** Medium

### Category D — Test Expectation Failure
**Examples:** stale generated tests, outdated assumptions
**Fix:** Fix generator/specification, NOT application code
**Priority:** High (prevents false failures)

---

## Execution Order for Fixes

1. **Database/schema failures** (Category A) — fix `src/db.py` DDL
2. **Repository failures** (Category B) — fix `src/repositories/`
3. **Model serialization failures** (Category B) — fix `src/models/`
4. **Service failures** (Category B/C) — fix `src/services/`
5. **Engine/business failures** (Category C) — fix `src/engines/`
6. **Stale generated tests** (Category D) — fix generator, regenerate

**For every fix:**
- Identify root cause
- Modify authoritative source
- Add regression test
- Avoid suppression (no `skip`, no `xfail`, no weakened assertions)

---

## Current Status (Phase 2.5 Complete)

### Fixed (Phase 2.5)
- Category A: 9 infrastructure failures fixed
- Category B: 8 data contract failures fixed
- Category C: 3 business logic failures fixed
- Category D: 4 test expectation failures fixed

### Remaining
- Category C: 52 property test failures in `credit_card_engine` and `loan_engine`
  - These are legitimate engine bugs found by Hypothesis
  - Require domain expertise to fix billing date arithmetic, EMI rounding, foreclosure calculations, etc.
  - Not blockers for verification stabilization

### Next Phase Recommendation
Proceed to **Phase 3 — Engine Correctness** to systematically fix the remaining Category C failures in credit card and loan engines.
