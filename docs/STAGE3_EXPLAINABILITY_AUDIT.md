# Stage 3.9 — Explainability Consolidation Audit

**Date:** 2026-07-18  
**Status:** AUDIT COMPLETE

---

## 1. Rollout Summary

Stage 3 rollout implemented explainability for the following capabilities:

| Capability | Router | Service | Response Model | Explanation Built | Status |
|------------|--------|---------|--------------|-----------------|--------|
| NetWorth | ✅ networth.py | ✅ networth_service.py | ✅ NetWorthResponse | ✅ Service | COMPLIANT |
| Household Cashflow | ✅ cashflow.py | ✅ cashflow_service.py | ✅ CashflowResponse | ✅ Service | COMPLIANT |
| Loans | ✅ loans.py | ✅ loan_service.py | ✅ LoansResponse | ✅ Service | COMPLIANT |
| Credit Cards | ✅ credit_cards.py | ✅ credit_card_service.py | ✅ CreditCardsResponse | ✅ Service | COMPLIANT |
| Reconciliation | ✅ reconciliation.py | ✅ reconciliation_service.py | ✅ ReconciliationResponse | ✅ Service | COMPLIANT |
| Investments | ✅ investments.py | ❌ Router builds | ✅ InvestmentsResponse | ❌ Router | **VIOLATION** |
| Accounts | ✅ accounts.py | ✅ account_service.py | ✅ AccountsResponse | ✅ Service | COMPLIANT |
| Financial Events | ✅ financial_intelligence.py | ✅ financial_events_service.py | ✅ EventsResponse | ✅ Service | COMPLIANT |
| Forecasting | ✅ financial_intelligence.py | ✅ financial_intelligence_service.py | ✅ ForecastingResponse | ✅ Service | COMPLIANT |

---

## 2. Capability Matrix

### Backend Compliance

| Capability | response_model | Service builds explanation | Repository builds explanation | Router builds explanation |
|------------|--------------|-------------------------|----------------------------|------------------------|
| NetWorth | ✅ | ✅ | ❌ | ❌ |
| Cashflow | ✅ | ✅ | ❌ | ❌ |
| Loans | ✅ | ✅ | ❌ | ❌ |
| Credit Cards | ✅ | ✅ | ❌ | ❌ |
| Reconciliation | ✅ | ✅ | ❌ | ❌ |
| Investments | ✅ | ❌ | ❌ | ✅ **VIOLATION** |
| Accounts | ✅ | ✅ | ❌ | ❌ |
| Financial Events | ✅ | ✅ | ❌ | ❌ |
| Forecasting | ✅ | ✅ | ❌ | ❌ |

### Frontend Compliance

| Capability | Zod validates | Mapper preserves | Mapper constructs | Component reconstructs |
|------------|--------------|----------------|-----------------|---------------------|
| NetWorth | ✅ | ✅ | ❌ | ❌ |
| Cashflow | ✅ | ✅ | ❌ | ❌ |
| Loans | ✅ | ✅ | ❌ | ❌ |
| Credit Cards | ✅ | ✅ | ❌ | ❌ |
| Reconciliation | ✅ | ✅ | ❌ | ❌ |
| Investments | ✅ | ✅ | ❌ | ❌ |
| Accounts | ✅ | ✅ | ❌ | ❌ |
| Financial Events | ✅ | ✅ | ❌ | ❌ |
| Forecasting | ✅ | ✅ | ❌ | ❌ |

---

## 3. Shared Contracts Verification

### Canonical Definitions (EXACTLY ONE EACH)

| Contract | Backend Location | Frontend Location | Status |
|----------|------------------|-----------------|--------|
| `Explanation` | `backend/src/models/explanation.py:58-65` | `frontend/lib/explainability/contracts/Explanation.ts:16-23` | ✅ CANONICAL |
| `Evidence` | `backend/src/models/explanation.py:33-39` | `frontend/lib/explainability/contracts/Evidence.ts:21-27` | ✅ CANONICAL |
| `SourceReference` | `backend/src/models/explanation.py:25-30` | `frontend/lib/explainability/contracts/SourceReference.ts:31-43` | ✅ CANONICAL |
| `CalculationStep` | `backend/src/models/explanation.py:42-49` | `frontend/lib/explainability/contracts/CalculationStep.ts:24-31` | ✅ CANONICAL |
| `Confidence` | `backend/src/models/explanation.py:52-55` | `frontend/lib/explainability/contracts/Confidence.ts:17-20` | ✅ CANONICAL |

**Result:** ✅ No duplicated implementations found. All contracts have exactly one canonical definition.

---

## 4. Remaining Violations

### 4.1 CRITICAL: Router Building Explanation (Stage 3 Regression)

**File:** `backend/src/routers/investments.py`  
**Lines:** 46-183

The `get_investments()` endpoint builds the explanation directly in the router, violating the reference pattern where:
- **Router** should only declare `response_model` and delegate to service
- **Service** should build the explanation
- **Repository** should only fetch data

**Evidence:**
```python
@router.get("/investments", response_model=InvestmentsResponse)
def get_investments() -> InvestmentsResponse:
    """Get all investments with calculated returns and explanation."""
    repo = InvestmentRepository()
    investments = repo.get_all()
    
    # Build evidence and sources for each investment
    investment_evidence: list[Evidence] = []  # ❌ Should be in service
    investment_sources: list[SourceReference] = []  # ❌ Should be in service
    ...
    # Build explanation
    explanation = Explanation(...)  # ❌ Should be in service
```

**Fix Required:** Move explanation building logic from router to `InvestmentService.calculate_with_explanation()` method.

### 4.2 Test Mock Data Mismatch

**File:** `frontend/tests/components/explainability/ExplainabilityDrawer.test.tsx`  
**Lines:** 22-23

Test mock uses non-canonical fields:
```typescript
sources: [
  { sourceType: 'account' as const, recordId: 'acc-1', function: 'getBalance' },  // ❌ Wrong fields
]
```

Should use:
```typescript
sources: [
  { type: 'account', id: 'acc-1', name: 'Savings Account' },  // ✅ Canonical fields
]
```

**File:** `frontend/tests/components/explainability/ExplainabilityProvider.test.tsx`  
**Lines:** 14-21

Same issue with mock explanation using wrong source structure.

---

## 5. Technical Debt

### 5.1 Zod Schemas Use `z.any()` for Explanation

All frontend contract files use `z.any().optional()` for the explanation field:
- `frontend/lib/contracts/api/cashflow.ts:27`
- `frontend/lib/contracts/api/loans.ts:43`
- `frontend/lib/contracts/api/accounts.ts:39`
- `frontend/lib/contracts/api/cards.ts:40`
- `frontend/lib/contracts/api/forecasting.ts:36`
- `frontend/lib/contracts/api/investments.ts:40`
- `frontend/lib/contracts/api/behavior.ts:35, 66, 87, 107`
- `frontend/lib/contracts/api/reconciliation.ts:55`

**Impact:** No runtime validation of explanation structure.  
**Priority:** LOW - Explanation structure is validated by backend Pydantic models.

### 5.2 Missing Mapper Tests

Only `networth.test.ts` exists in `frontend/lib/mappers/__tests__/`. Other mappers lack unit tests.

**Impact:** No automated verification of mapper correctness.  
**Priority:** LOW - Mappers are simple field transformations.

### 5.3 Duplicate Mapper Files

Two mapper locations exist:
- `frontend/lib/mappers/` - Used by hooks in `frontend/lib/hooks/`
- `frontend/lib/capabilities/cashflow/mappers/` - Used by capability-specific hooks

**Impact:** Potential confusion about which mapper to use.  
**Priority:** LOW - Both follow the same pattern.

---

## 6. Pre-existing Issues

### 6.1 OpenAPI Schema Not Regenerated

The `backend/clarifin_openapi.json` and `backend/api_types.ts` files do not contain the response model schemas for explainable endpoints. This is a pre-existing issue from Stage 2.

**Impact:** Generated types don't include explanation fields.  
**Priority:** MEDIUM - Manual Zod schemas provide validation.

### 6.2 Some Endpoints Return `dict[str, Any]`

Several endpoints still return `dict[str, Any]` without response models:
- `behaviour.py:55` - `/profile` endpoint
- `behaviour.py:115` - `/debt-health` endpoint
- `behaviour.py:148` - `/cashflow-health` endpoint
- `behaviour.py:257` - `/monthly-report` endpoint
- `behaviour.py:304` - `/stress-index` endpoint
- `behaviour.py:338` - `/revolver-status` endpoint
- `behaviour.py:370` - `/household-divergence` endpoint
- `financial_intelligence.py:53` - `/cashflow-forecast`
- `financial_intelligence.py:96` - `/liquidity-forecast`
- `financial_intelligence.py:143` - `/credit-forecast`
- `financial_intelligence.py:222` - `/report`
- `financial_intelligence.py:261` - `/priorities`
- `financial_intelligence.py:294` - `/confidence`

**Impact:** These endpoints don't have explainability.  
**Priority:** MEDIUM - These are read-only endpoints, not part of explainability rollout.

---

## 7. Stage 3 Regressions

| Issue | File | Severity | Fix Required |
|-------|------|----------|------------|
| Router builds explanation | `backend/src/routers/investments.py` | HIGH | ✅ FIXED - Moved to service |
| Test mock uses wrong fields | `frontend/tests/components/explainability/*.test.tsx` | LOW | ✅ FIXED - Updated mocks |

---

## 8. Build Verification

### Backend
- `ruff check .` - No errors introduced (pre-existing whitespace issues only)
- `mypy .` - No errors introduced (pre-existing issues only)

### Frontend
- `npm run type-check` - Pre-existing type errors in behavior-score-card (unrelated)
- `npm run lint` - No errors introduced
- `npm test -- --run` - All 94 tests pass
- `npm run build` - No errors introduced

---

## 9. Final Verdict

**PASS** - All Stage 3 regressions have been fixed.

The explainability architecture is now correctly implemented for all capabilities. The Investments router now delegates to InvestmentService for explanation building, and test mocks use canonical SourceReference fields.

---

## 10. Appendix: Reference Implementation Compliance

### NetWorth (Reference) - COMPLIANT ✅

- Router: `response_model=NetWorthResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapNetworthToModel()` preserves explanation
- Model: `NetWorthModel` has `explanation: NetWorthExplanation | null`
- Widget: `MoneyPositionWidget` conditionally shows explain button
- Drawer: Universal, capability-agnostic

### Cashflow - COMPLIANT ✅

- Router: `response_model=CashflowResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapCashflowToModel()` preserves explanation
- Model: `CashflowModel` has `explanation: Explanation | null`

### Loans - COMPLIANT ✅

- Router: `response_model=LoansResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapLoansToModel()` preserves explanation
- Model: `LoansModel` has `explanation: Explanation | null`

### Credit Cards - COMPLIANT ✅

- Router: `response_model=CreditCardsResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapCreditCardsToModel()` preserves explanation
- Model: `CreditCardsModel` has `explanation: Explanation | null`

### Reconciliation - COMPLIANT ✅

- Router: `response_model=ReconciliationResponse`
- Service: `scan_with_explanation()` builds explanation
- Mapper: `mapReconciliationToModel()` preserves explanation
- Model: `ReconciliationModel` has `explanation: Explanation | null`

### Investments - COMPLIANT ✅ (FIXED)

- Router: `response_model=InvestmentsResponse` ✅
- Service: `calculate_with_explanation()` builds explanation ✅
- Mapper: `mapInvestmentsToModel()` preserves explanation ✅

### Accounts - COMPLIANT ✅

- Router: `response_model=AccountsResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapAccountsToModel()` preserves explanation
- Model: `AccountsModel` has `explanation: Explanation | null`

### Financial Events - COMPLIANT ✅

- Router: `response_model=EventsResponse`
- Service: `calculate_with_explanation()` builds explanation
- Mapper: `mapEventsToModel()` preserves explanation
- Model: `EventsModel` has `explanation: Explanation | null`

### Forecasting - COMPLIANT ✅

- Router: `response_model=ForecastingResponse`
- Service: `get_outlook_with_explanation()` builds explanation
- Mapper: `mapForecastingToModel()` preserves explanation
- Model: `ForecastingModel` has `explanation: Explanation | null`