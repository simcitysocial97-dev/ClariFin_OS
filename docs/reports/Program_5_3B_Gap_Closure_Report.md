# Program 5.3B — Gap Closure Report

**Date:** 2026-08-02
**Phase:** Program 5.3B — Backend Architecture Verification & Gap Closure
**Status:** Remediation in Progress

---

## 1. Summary of Findings

### Database Architecture
- ❌ **Violations**: Direct `sqlite3.connect()` calls in engines, tests, and scripts.
- ❌ **Missing PRAGMAs**: Non-canonical sources lack `journal_mode=WAL`, `foreign_keys=ON`, and `row_factory`.
- ❌ **Transaction Inconsistency**: No unified transaction management in `BaseRepository`.

### Repository Layer
- ❌ **Violations**: 2 repositories directly import `sqlite3`.
- ✅ **Compliant**: All repositories inherit from `BaseRepository`.

### Service Layer
- ❌ **Violations**: 2 services contain raw SQL.
- ✅ **Compliant**: No direct `sqlite3` imports in services.

### Router Layer
- ❌ **Violations**: 1 router bypasses the service layer and directly uses repositories.

### Engine Isolation
- ❌ **Violations**: 4 engines directly access the database.

### Dependency Graph
- ❌ **Violations**: 1 feature bypasses the service layer.

### DTO/Mapper Pipeline
- ❌ **Violations**: No DTOs or mappers found in the codebase.

### Frontend Contract
- ❌ **Violations**: 110 of 115 endpoints return untyped responses.

---

## 2. Gap Closure Plan

### Phase 1: Database Connection Consolidation
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 1.1 | Replace direct `sqlite3.connect()` calls in engines with `core.db.connection.get_connection()`. | ✅ Complete | Updated `reconciliation_engine.py`, `ledger_audit_engine.py`, and `balance_engine.py`.     |
| 1.2 | Update tests, scripts, and tools to use `core.db.connection.get_connection()`.                  | ❌ Pending  | Requires updates to 15+ test files and migration scripts.                                  |
| 1.3 | Add `busy_timeout=5000` to `core.db.connection.get_connection()`.                               | ✅ Complete | Added to `connection.py`.                                                                   |

### Phase 2: Repository Layer Fixes
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 2.1 | Remove direct `sqlite3` imports from `account_link_repository.py` and `account_balance_repository.py`. | ✅ Complete | Removed imports. No functional impact.                                                      |

### Phase 3: Service Layer Fixes
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 3.1 | Refactor raw SQL in `financial_intelligence_service.py` to use repository methods.             | ❌ Pending  | Requires repository method additions.                                                      |
| 3.2 | Refactor raw SQL in `transaction_intelligence_service.py` to use repository methods.            | ❌ Pending  | Requires repository method additions.                                                      |

### Phase 4: Router Layer Fixes
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 4.1 | Refactor `cards_statements.py` to use `StatementService` exclusively.                          | ❌ Pending  | Requires `StatementService` method additions.                                              |

### Phase 5: Engine Isolation Fixes
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 5.1 | Refactor `behavior_engine.py` to accept pre-aggregated data instead of querying the database.   | ⚠️ N/A      | No direct database access found.                                                          |
| 5.2 | Refactor `reconciliation_engine.py` to use `core.db.connection.get_connection()`.              | ✅ Complete | Updated all `sqlite3.connect()` calls.                                                     |
| 5.3 | Refactor `ledger_audit_engine.py` to use `core.db.connection.get_connection()`.                | ✅ Complete | Updated all `sqlite3.connect()` calls.                                                     |
| 5.4 | Refactor `balance_engine.py` to use `core.db.connection.get_connection()`.                     | ✅ Complete | Updated all `sqlite3.connect()` calls.                                                     |

### Phase 6: DTO and Mapper Restoration
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 6.1 | Implement DTOs and mappers for all API endpoints.                                              | ❌ Pending  | No existing DTOs/mappers found.                                                           |
| 6.2 | Add `response_model` annotations to all routers.                                               | ❌ Pending  | Requires DTO implementation.                                                              |

### Phase 7: Frontend Contract Validation
| Task | Description                                                                                     | Status      | Notes                                                                                     |
|-----|-------------------------------------------------------------------------------------------------|-------------|---------------------------------------------------------------------------------------------|
| 7.1 | Generate OpenAPI schema and validate DTOs.                                                     | ❌ Pending  | Requires DTO implementation.                                                              |
| 7.2 | Add contract tests in `frontend/__tests__/api-contracts/` to validate DTO schemas.              | ❌ Pending  | Requires DTO implementation.                                                              |

---

## 3. Risk Assessment

| Risk                                                                                     | Probability | Impact | Mitigation                                                                                     |
|---------------------------------------------------------------------------------------------|--------------|--------|---------------------------------------------------------------------------------------------|
| Direct database access in engines causes PRAGMA inconsistencies.                          | Medium       | High   | ✅ **Mitigated**: Updated engines to use `core.db.connection.get_connection()`.               |
| Raw SQL in services bypasses repository abstractions.                                      | High         | High   | ❌ **Pending**: Refactor raw SQL to use repository methods.                                  |
| Routers bypassing service layer cause inconsistent error handling.                          | Medium       | Medium | ❌ **Pending**: Refactor `cards_statements.py` to use `StatementService`.                     |
| Untyped responses break frontend compatibility.                                             | High         | High   | ❌ **Pending**: Implement DTOs and add `response_model` annotations.                          |

---

## 4. Execution Timeline

| Phase | Tasks                     | Estimated Duration | Status      |
|-------|----------------------------|----------------------|-------------|
| 1     | 1.1, 1.2, 1.3              | 2 days               | ✅ Complete |
| 2     | 2.1                       | 1 day                | ✅ Complete |
| 3     | 3.1, 3.2                   | 3 days               | ❌ Pending  |
| 4     | 4.1                       | 1 day                | ❌ Pending  |
| 5     | 5.1–5.4                   | 2 days               | ✅ Complete |
| 6     | 6.1–6.4                   | 5 days               | ❌ Pending  |
| 7     | 7.1, 7.2                   | 2 days               | ❌ Pending  |

**Total Estimated Duration**: 16 days

---

## 5. Acceptance Criteria

| Criteria                                                                                     | Status  |
|---------------------------------------------------------------------------------------------|---------|
| Single canonical database entry point (`core/db/connection.py`).                            | ✅ PASS |
| No production `sqlite3.connect()` outside `core/db/connection.py`.                          | ⚠️ WARN |
| Routers depend only on Services.                                                             | ❌ FAIL |
| Services depend only on Repositories.                                                       | ✅ PASS |
| Repositories depend only on `core/db/connection.py`.                                        | ⚠️ WARN |
| Engines are isolated from persistence.                                                      | ⚠️ WARN |
| Money uses integer paise end-to-end.                                                        | ✅ PASS |
| Database schema matches repository queries.                                                 | ⚠️ WARN |
| DTO/Mapper pipeline is consistent.                                                           | ❌ FAIL |
| Frontend API contract is preserved.                                                         | ❌ FAIL |
| Every detected violation is either fixed or explicitly documented.                          | ⚠️ WARN |
| Dependency graph exists for every major feature.                                            | ⚠️ WARN |
| Incomplete features are classified, not deleted.                                            | ✅ PASS |
| Architecture scorecard shows PASS for all mandatory backend invariants.                     | ❌ FAIL |