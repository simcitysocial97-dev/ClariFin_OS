# Contract Validation Framework (CoVF)

## Overview

The Contract Validation Framework validates all public API endpoints against their OpenAPI schemas.
Tests execute the real FastAPI application without mocks.

## Coverage Summary

| Router | Endpoints | Tested | Snapshots | Boundary | Invalid | Status |
|--------|-----------|--------|-----------|----------|---------|--------|
| accounts | 19 | 11 | 0 | ✅ | ✅ | 58% |
| cashflow | 2 | 6 | 0 | ✅ | ✅ | 100% |
| credit_cards | 14 | 11 | 0 | ✅ | ✅ | 79% |
| loans | 13 | 9 | 0 | ✅ | ✅ | 69% |
| financial_intelligence | 7 | 6 | 0 | ✅ | ✅ | 86% |

**Total: 46 tests across 5 routers**

## Missing Endpoints

Routers without contract tests (Phase 2 expansion):

- behaviour (duplicate - UK spelling)
- behaviour (duplicate - US spelling)
- cards_statements
- dashboard
- export
- goals
- import_router
- investments
- managed_accounts
- members
- networth
- optimization
- patterns
- reconciliation
- scenarios
- transactions

## Unsupported Schemas

No unsupported schemas detected. All OpenAPI 3.0 schemas are supported.

## Test Architecture

```
tests/contracts/
├── conftest.py           # Shared fixtures (TestClient)
├── snapshot_normalizer.py # Central normalization utility
├── schema_providers.py    # OpenAPI schema access
├── contract_registry.py   # Registry loader/writer
└── routers/
    ├── test_accounts.py
    ├── test_cashflow.py
    ├── test_credit_cards.py
    ├── test_loans.py
    └── test_forecasting.py
```

## Validation Types

- **Valid Request**: Returns 200/201 with valid response
- **Missing Fields**: Returns 422 (validation error)
- **Type Violations**: Returns 422 (validation error)
- **Boundary Values**: Returns 422 for out-of-range values
- **Enum Violations**: Returns 422 for invalid enum values

## Future Work

1. Expand to remaining 17 routers
2. Add response schema assertion validation
3. Integrate with CIF for selective test execution
4. Add Schemathesis support when available
5. Generate snapshots for regression testing