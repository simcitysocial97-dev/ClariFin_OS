# Program 5.3B — API Contract Verification

**Date:** 2026-08-02
**Phase:** Program 5.3B — Backend Architecture Verification & Gap Closure
**Status:** Audit Complete

---

## 1. Endpoint Contract Compliance

| Router                     | Endpoint                     | Request Model                     | Response Model                     | Status                                                                                     |
|----------------------------|--------------------------------|-----------------------------------|------------------------------------|---------------------------------------------------------------------------------------------|
| `dashboard.py`             | `/summary`                  | None                           | `DashboardSummaryDTO`             | ⚠️ **Partial Compliance**: Uses DTO but no `response_model` annotation.                   |
| `cashflow.py`              | `/summary`                  | None                           | `CashflowSummaryDTO`              | ⚠️ **Partial Compliance**: Uses DTO but no `response_model` annotation.                  |
| `accounts.py`              | `/`                         | `AccountCreateRequest`            | `dict[str, Any]`                  | ❌ **Non-Compliant**: Uses `src/models` for request but returns untyped `dict`.           |
| `credit_cards.py`          | `/convert-to-emi`           | `EmiConversionRequest`            | `dict[str, Any]`                  | ❌ **Non-Compliant**: Uses `src/models` for request but returns untyped `dict`.           |
| `loans.py`                 | `/`                         | `LoanCreateRequest`               | `dict[str, Any]`                  | ❌ **Non-Compliant**: Uses `src/models` for request but returns untyped `dict`.           |
| All Other Routers          | All Endpoints                | None or Untyped                   | `dict[str, Any]` or Untyped       | ❌ **Non-Compliant**: No DTOs, no `response_model` annotations.                           |

---

## 2. DTO Usage Analysis

| DTO Module               | Consumers                     | Status                                                                                     |
|--------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| `dashboard_dto.py`        | `dashboard.py`              | ✅ **Compliant**: Used in router.                                                           |
| `cashflow_dto.py`         | `cashflow.py`               | ✅ **Compliant**: Used in router.                                                           |
| `accounts_dto.py`         | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `analytics_dto.py`        | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `behaviour_dto.py`        | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `credit_cards_dto.py`     | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `forecast_dto.py`         | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `investments_dto.py`      | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `loans_dto.py`            | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `net_worth_dto.py`        | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `reconciliation_dto.py`   | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `statement_dto.py`        | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `transaction_dto.py`      | None                         | ❌ **Dead Code**: No consumers.                                                              |

---

## 3. Mapper Usage Analysis

| Mapper Module             | Consumers                     | Status                                                                                     |
|--------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| `account_mapper.py`       | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `analytics_mapper.py`     | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `dashboard_mapper.py`     | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `statement_mapper.py`     | None                         | ❌ **Dead Code**: No consumers.                                                              |
| `transaction_mapper.py`   | None                         | ❌ **Dead Code**: No consumers.                                                              |

---

## 4. Frontend Contract Risks

### Risk: Untyped Responses
- **Impact**: Frontend cannot rely on stable schemas. Any change in backend response structure breaks frontend silently.
- **Evidence**: 110 of 115 endpoints return `dict[str, Any]` or untyped responses.
- **Mitigation**: Add `response_model` annotations and DTOs for all endpoints.

### Risk: Mixed Request/Response Models
- **Impact**: Tight coupling between frontend and backend. Changes to `src/models` propagate directly to frontend.
- **Evidence**: `accounts.py`, `credit_cards.py`, and `loans.py` use `src/models` for request/response.
- **Mitigation**: Replace `src/models` with DTOs in router signatures.

### Risk: Dead DTOs and Mappers
- **Impact**: Maintenance overhead and confusion. Dead code may mislead developers.
- **Evidence**: 10 of 13 DTO modules and all 5 mappers have no consumers.
- **Mitigation**: Remove dead DTOs and mappers or wire them to endpoints.

---

## 5. Frontend Contract Stability Assessment

| Endpoint Group       | Contract Stable? | Reason                                                                                     |
|--------------------|------------------|---------------------------------------------------------------------------------------------|
| `dashboard.py`      | ❌ No             | Uses `DashboardSummaryDTO` but built manually (no mapper). No `response_model` annotation. |
| `cashflow.py`       | ❌ No             | Uses `CashflowSummaryDTO` but no `response_model` annotation.                             |
| `accounts.py`       | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| `credit_cards.py`   | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| `loans.py`          | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| All Other Endpoints | ❌ No             | Return `dict[str, Any]` or untyped responses. No DTOs or `response_model` annotations.    |

---

## 6. Recommendations

### Phase 1: DTO and Mapper Restoration
1. **Implement Mappers**: Wire all 5 mappers to transform domain models to DTOs.
2. **Add `response_model` Annotations**: Annotate all endpoints with `response_model` using DTOs.
3. **Replace `src/models` in Routers**: Migrate `accounts.py`, `credit_cards.py`, and `loans.py` to use DTOs instead of domain models.

### Phase 2: Dead Code Removal
1. **Remove Dead DTOs**: Delete 10 unused DTO modules.
2. **Remove Dead Mappers**: Delete all 5 unused mapper modules.

### Phase 3: Frontend Contract Validation
1. **Generate OpenAPI Schema**: Use FastAPI's schema generation to validate DTOs.
2. **Frontend Integration Testing**: Verify frontend compatibility with typed responses.
3. **Contract Tests**: Add tests in `frontend/__tests__/api-contracts/` to validate DTO schemas.