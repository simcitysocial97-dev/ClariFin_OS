# Program 5.3B — API Contract Verification

**Date:** 2026-08-02
**Phase:** Program 5.3B — Backend Architecture Verification & Gap Closure
**Status:** Audit Complete

---

## 1. Endpoint Contract Compliance

| Router                     | Endpoint                     | Request Model                     | Response Model                     | Status                                                                                     |
|----------------------------|--------------------------------|-----------------------------------|------------------------------------|---------------------------------------------------------------------------------------------|
| `dashboard.py`             | `/summary`                  | None                           | `dict[str, Any]`                  | ❌ **Non-Compliant**: No DTO or `response_model` annotation.                              |
| `cashflow.py`              | `/summary`                  | None                           | `dict[str, Any]`                  | ❌ **Non-Compliant**: No DTO or `response_model` annotation.                              |
| `accounts.py`              | `/`                         | `AccountCreateRequest`            | `dict[str, Any]`                  | ❌ **Non-Compliant**: Returns untyped `dict`.                                              |
| `credit_cards.py`          | `/convert-to-emi`           | `EmiConversionRequest`            | `dict[str, Any]`                  | ❌ **Non-Compliant**: Returns untyped `dict`.                                              |
| `loans.py`                 | `/`                         | `LoanCreateRequest`               | `dict[str, Any]`                  | ❌ **Non-Compliant**: Returns untyped `dict`.                                              |
| All Other Routers          | All Endpoints                | None or Untyped                   | `dict[str, Any]` or Untyped       | ❌ **Non-Compliant**: No DTOs, no `response_model` annotations.                           |

---

## 2. DTO Usage Analysis

| DTO Module               | Consumers                     | Status                                                                                     |
|--------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| **No DTOs Found**        | **N/A**                      | ❌ **Critical**: No DTO modules exist in the codebase.                                      |

---

## 3. Mapper Usage Analysis

| Mapper Module             | Consumers                     | Status                                                                                     |
|--------------------------|-------------------------------|---------------------------------------------------------------------------------------------|
| **No Mappers Found**     | **N/A**                      | ❌ **Critical**: No mapper modules exist in the codebase.                                  |

---

## 4. Frontend Contract Risks

### Risk: Untyped Responses
- **Impact**: Frontend cannot rely on stable schemas. Any change in backend response structure breaks frontend silently.
- **Evidence**: 110 of 115 endpoints return `dict[str, Any]` or untyped responses.
- **Mitigation**: Implement DTOs and add `response_model` annotations to all endpoints.

### Risk: Mixed Request/Response Models
- **Impact**: Tight coupling between frontend and backend. Changes to `src/models` propagate directly to frontend.
- **Evidence**: `accounts.py`, `credit_cards.py`, and `loans.py` use `src/models` for request/response.
- **Mitigation**: Replace `src/models` with DTOs in router signatures.

---

## 5. Frontend Contract Stability Assessment

| Endpoint Group       | Contract Stable? | Reason                                                                                     |
|--------------------|------------------|---------------------------------------------------------------------------------------------|
| `dashboard.py`      | ❌ No             | Returns untyped `dict`. No `response_model` annotation.                                    |
| `cashflow.py`       | ❌ No             | Returns untyped `dict`. No `response_model` annotation.                                    |
| `accounts.py`       | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| `credit_cards.py`   | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| `loans.py`          | ❌ No             | Uses `src/models` for request but returns untyped `dict`.                                 |
| All Other Endpoints | ❌ No             | Return `dict[str, Any]` or untyped responses. No DTOs or `response_model` annotations.    |

---

## 6. Recommendations

### Phase 1: DTO and Mapper Restoration
1. **Implement DTOs**: Create DTO modules for all API endpoints.
2. **Implement Mappers**: Create mapper modules to transform domain models to DTOs.
3. **Add `response_model` Annotations**: Annotate all endpoints with `response_model` using DTOs.
4. **Replace `src/models` in Routers**: Migrate routers to use DTOs instead of domain models.

### Phase 2: Frontend Contract Validation
1. **Generate OpenAPI Schema**: Use FastAPI's schema generation to validate DTOs.
2. **Frontend Integration Testing**: Verify frontend compatibility with typed responses.
3. **Contract Tests**: Add tests in `frontend/__tests__/api-contracts/` to validate DTO schemas.