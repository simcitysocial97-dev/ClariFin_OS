# Testing Strategy

## Current Test Categories

### Backend Tests (backend/tests/)

| Category | Files | Focus |
|----------|-------|-------|
| **Smoke Tests** | `test_repository_smoke.py` | Basic repository connectivity |
| **Engine Tests** | `test_*.py` (loan_engine, behaviour_engine, etc.) | Pure function verification |
| **Integration Tests** | `test_*_integration.py` | Cross-layer workflows |
| **E2E Tests** | `test_*_e2e.py` | End-to-end flows |
| **Determinism Tests** | `test_determinism.py`, `test_reconciliation_determinism.py` | Same input = same output |
| **Boundary Tests** | `test_boundary.py` | Edge case handling |

### Frontend Tests (frontend/)

| Category | Location | Tool |
|----------|----------|------|
| **Unit Tests** | `frontend/__tests__/` | Vitest |
| **E2E Tests** | `frontend/tests/` | Playwright |

## Existing Test Commands

| Environment | Command |
|-------------|---------|
| Backend Lint | `cd backend && ./venv/bin/python3 -m ruff check .` |
| Backend Type | `cd backend && ./venv/bin/python3 -m mypy .` |
| Backend Test | `cd backend && ./venv/bin/python3 -m pytest tests/ -q --tb=short --maxfail=3` |
| Frontend Type | `cd frontend && npm run type-check` |
| Frontend Lint | `cd frontend && npm run lint` |
| Frontend Test | `cd frontend && npm test -- --run` |
| Frontend Build | `cd frontend && npm run build` |

## Test Coverage Goals

| Layer | Coverage Target |
|-------|-----------------|
| Engines | Property tests for all pure functions |
| Services | Contract tests for orchestration |
| Routers | Integration tests with mock data |
| Repositories | Smoke tests + edge cases |

### Property Tests (New)
- Created `tests/properties/test_money_invariants.py` (15 tests)
- Tests money invariants without hypothesis dependency

### Invariants Tests (New)
- Created `tests/invariants/test_money.py`, `test_cashflow.py`, `test_loan.py`
- Reusable assertion functions for domain invariants

### Adaptive Test Selection
- **pytest-testmon**: Installed (v2.2.0)
- **When testmon runs**: `.testmondata` file exists + pytest-testmon importable
- **When full suite runs**: Fallback when testmon unavailable or cache missing
- **Timing**: 
  - Full suite (3 tests): ~1.67s
  - With testmon cache (1 test impacted): ~0.76s (9 deselected)

## Future Migration Plan

### Phase 1: Engine Tests → Property Tests
- Convert example-based tests to property-based using `hypothesis`
- Focus: `reconciliation_engine`, `loan_engine`, `cashflow_engine`
- Benefit: Exhaustive input domain testing

### Phase 2: Router Tests → Contract Tests
- Replace router mocks with contract tests
- Use `pytest`'s `parametrize` for API contract verification
- Focus on request/response shape validation

### Mutation Testing (CI)
- **Tool**: mutmut (configured in `.github/workflows/quality-gate.yml`)
- **Scope**: `backend/src/engines/` only (pure calculation logic)
- **Purpose**: Verify properties detect wrong logic by introducing mutations

### CI Pipeline (`.github/workflows/quality-gate.yml`)
- **8 stages**: fast → [architecture, properties] → integration → [contract, golden] → snapshot → mutation
- **Parallel**: architecture + properties run in parallel after fast
- **Artifacts**: failure logs uploaded per stage (7-day retention)

### Phase 4: Financial Correctness Tests
- Add assertions for monetary invariants
- Verify: income-expense=surplus
- Verify: loan principal monotonically decreases
- Verify: forecast confidence 0-1
- Verify: all amounts in paise, never float

## Test File Inventory

### Key Test Files (by Layer)

**Repositories:**
- `test_account_balance_repository.py`
- `test_account_repository.py`
- `test_loan_repository.py`
- `test_transaction_repository.py`
- `test_reconciliation_repository.py`

**Engines:**
- `test_loan_engine_comprehensive.py`
- `test_loan_engine_coverage.py`
- `test_loan_engine_financial_correctness.py`
- `test_reconciliation.py`
- `test_behaviour_engine_*.py` (7 files)
- `test_cashflow_engine.py`
- `test_credit_card_engine.py`

**Services:**
- `test_account_service.py`
- `test_loan_service.py`
- `test_reconciliation_service.py`
- `test_behaviour_service.py`

**Integration:**
- `test_financial_events.py`
- `test_financial_intelligence_integration.py`
- `test_behaviour_credit_signals_e2e.py`

## Test Anti-Patterns to Avoid

| Anti-Pattern | Replacement |
|--------------|-------------|
| `as any` in TypeScript | Proper type narrowing |
| `@ts-ignore` / `@ts-nocheck` | Fix the underlying issue |
| Float for currency | Integer paise everywhere |
| Mock-heavy tests | Contract tests with real shapes |
| Large fixture trees | Golden dataset constants