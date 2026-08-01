# Program 5.3B — Gap Closure Report

**Date:** 2026-08-02
**Phase:** Program 5.3B — Backend Architecture Verification & Gap Closure
**Status:** Audit Complete

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
- ❌ **Violations**: 5 routers bypass the service layer and directly use repositories.

### Engine Isolation
- ❌ **Violations**: 4 engines directly access the database.

### Dependency Graph
- ❌ **Violations**: 7 features bypass the service layer or directly access the database.

### DTO/Mapper Pipeline
- ❌ **Violations**: 10 of 13 DTO modules and all 5 mappers are unused.
- ⚠️ **Partial Compliance**: 2 routers use DTOs but lack `response_model` annotations.

### Frontend Contract
- ❌ **Violations**: 110 of 115 endpoints return untyped responses.

---

## 2. Gap Closure Plan

### Phase 1: Database Connection Consolidation
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 1.1 | Replace direct `sqlite3.connect()` calls in engines with `core.db.connection.get_connection()`. | High  | 4          |
| 1.2 | Update tests, scripts, and tools to use `core.db.connection.get_connection()`.                  | Medium| 3          |
| 1.3 | Add `busy_timeout=5000` to `core.db.connection.get_connection()`.                               | Low   | 1          |

---

### Phase 2: Repository Layer Fixes
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 2.1 | Remove direct `sqlite3` imports from `account_link_repository.py` and `account_balance_repository.py`. | Medium| 2          |

---

### Phase 3: Service Layer Fixes
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 3.1 | Refactor raw SQL in `financial_intelligence_service.py` to use repository methods.             | High  | 4          |
| 3.2 | Refactor raw SQL in `transaction_intelligence_service.py` to use repository methods.            | High  | 5          |

---

### Phase 4: Router Layer Fixes
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 4.1 | Create `BankService` and refactor `banks.py` to use it.                                         | Medium| 3          |
| 4.2 | Create `ExportService` and refactor `export.py` to use it.                                       | Medium| 3          |
| 4.3 | Create `InvestmentService` and refactor `investments.py` to use it.                             | Medium| 3          |
| 4.4 | Create `MemberService` and refactor `members.py` to use it.                                     | Medium| 3          |
| 4.5 | Refactor `import_router.py` to use `StatementService` and `TransactionService`.                 | High  | 4          |
| 4.6 | Refactor `reconciliation.py` to remove direct `ReconciliationRepository` imports.              | Medium| 2          |
| 4.7 | Refactor `cards_statements.py` to use `StatementService`.                                       | Medium| 2          |
| 4.8 | Refactor `managed_accounts.py` to use `AccountService`.                                         | Medium| 2          |

---

### Phase 5: Engine Isolation Fixes
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 5.1 | Refactor `behavior_engine.py` to accept pre-aggregated data instead of querying the database.   | High  | 5          |
| 5.2 | Refactor `reconciliation_engine.py` to use `core.db.connection.get_connection()`.              | High  | 4          |
| 5.3 | Refactor `ledger_audit_engine.py` to use `core.db.connection.get_connection()`.                | High  | 4          |
| 5.4 | Refactor `balance_engine.py` to use `core.db.connection.get_connection()`.                     | High  | 4          |

---

### Phase 6: DTO and Mapper Restoration
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 6.1 | Implement all 5 mappers to transform domain models to DTOs.                                    | High  | 5          |
| 6.2 | Add `response_model` annotations to all endpoints using DTOs.                                   | High  | 4          |
| 6.3 | Replace `src/models` usage in `accounts.py`, `credit_cards.py`, and `loans.py` with DTOs.       | Medium| 3          |
| 6.4 | Remove 10 unused DTO modules and all 5 unused mapper modules.                                  | Low   | 1          |

---

### Phase 7: Frontend Contract Validation
| Task | Description                                                                                     | Risk  | Complexity |
|-----|-------------------------------------------------------------------------------------------------|-------|------------|
| 7.1 | Generate OpenAPI schema and validate DTOs.                                                     | Medium| 2          |
| 7.2 | Add contract tests in `frontend/__tests__/api-contracts/` to validate DTO schemas.              | Medium| 3          |

---

## 3. Risk Assessment

| Risk                                                                                     | Probability | Impact | Mitigation                                                                                     |
|---------------------------------------------------------------------------------------------|--------------|--------|---------------------------------------------------------------------------------------------|
| Direct database access in engines causes PRAGMA inconsistencies.                          | High         | High   | Phase 1: Consolidate all connections under `core.db.connection.get_connection()`.           |
| Raw SQL in services bypasses repository abstractions.                                      | High         | High   | Phase 3: Refactor raw SQL to use repository methods.                                         |
| Routers bypassing service layer cause inconsistent error handling.                          | Medium       | Medium | Phase 4: Create missing services and refactor routers to use them.                           |
| Untyped responses break frontend compatibility.                                             | High         | High   | Phase 6: Implement mappers and add `response_model` annotations.                            |
| Dead DTOs/mappers increase maintenance overhead.                                           | Low          | Low    | Phase 6: Remove unused DTOs and mappers.                                                     |

---

## 4. Execution Timeline

| Phase | Tasks | Estimated Duration |
|-------|-------|----------------------|
| 1     | 1.1, 1.2, 1.3 | 2 days               |
| 2     | 2.1       | 1 day                |
| 3     | 3.1, 3.2   | 3 days               |
| 4     | 4.1–4.8   | 4 days               |
| 5     | 5.1–5.4   | 4 days               |
| 6     | 6.1–6.4   | 3 days               |
| 7     | 7.1, 7.2   | 2 days               |

**Total Estimated Duration**: 19 days

---

## 5. Acceptance Criteria

| Criteria                                                                                     | Status  |
|---------------------------------------------------------------------------------------------|---------|
| Single canonical database entry point (`core/db/connection.py`).                            | ❌ FAIL |
| No production `sqlite3.connect()` outside `core/db/connection.py`.                          | ❌ FAIL |
| Routers depend only on Services.                                                             | ❌ FAIL |
| Services depend only on Repositories.                                                       | ❌ FAIL |
| Repositories depend only on `core/db/connection.py`.                                        | ❌ FAIL |
| Engines are isolated from persistence.                                                      | ❌ FAIL |
| Money uses integer paise end-to-end.                                                        | ✅ PASS |
| Database schema matches repository queries.                                                 | ⚠️ WARN |
| DTO/Mapper pipeline is consistent.                                                           | ❌ FAIL |
| Frontend API contract is preserved.                                                         | ❌ FAIL |
| Every detected violation is either fixed or explicitly documented.                          | ❌ FAIL |
| Dependency graph exists for every major feature.                                            | ❌ FAIL |
| Incomplete features are classified, not deleted.                                            | ✅ PASS |
| Architecture scorecard shows PASS for all mandatory backend invariants.                     | ❌ FAIL |