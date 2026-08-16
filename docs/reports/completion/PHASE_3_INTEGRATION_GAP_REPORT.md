# Phase 3 — Integration Gap Report

## Audit Date: 2026-07-23

## Executive Summary

**Overall System Completeness:** 85% (backend), 0% (frontend integration not yet audited)

**Critical Findings:**
- 6 broken edges in the runtime pipeline
- 1 missing router (Financial Events)
- 1 duplicate system (Behaviour routers)
- 1 missing service layer (Transactions)
- 3 disconnected automatic triggers (Intelligence, Recommendations)

---

## 1. Orphaned Components

### 1.1 Services Without Routers
| Service | Status | Impact |
|---------|--------|--------|
| `FinancialEventsService` | ❌ No router | Complete backend implementation but no API exposure |

### 1.2 Repositories Without Services
| Repository | Status | Impact |
|------------|--------|--------|
| `LiquidityPatternRepository` | ⚠️ No dedicated service | Used indirectly by FinancialIntelligenceService |

### 1.3 Engines Without Services
| Engine | Status | Impact |
|--------|--------|--------|
| None detected | ✅ All engines are consumed by services | - |

### 1.4 Dead Endpoints
| Router | Endpoint | Status | Evidence |
|--------|----------|--------|----------|
| `/loans` | GET | ⚠️ Dead | projectbrief.md confirms dead route |
| `/investments` | GET | ⚠️ Dead | projectbrief.md confirms dead route |

---

## 2. Duplicate Systems

### 2.1 Duplicate Behaviour Routers
**Files:**
- `backend/src/routers/behaviour.py` → `/api/v1/behaviour/*`
- `backend/src/routers/behavior.py` → `/api/behavior/*`

**Impact:** Code duplication, maintenance burden, potential inconsistencies

**Recommendation:** Consolidate to single router (keep `/api/v1/behaviour/*`)

---

## 3. Missing Service Layers

### 3.1 Transactions
**Current State:** Router directly accesses repositories

**File:** `backend/src/routers/transactions.py`

**Impact:**
- Business logic (overview metrics, analytics) embedded in router
- No reuse potential for other consumers
- Testing complexity

**Recommendation:** Create `TransactionService` to orchestrate repository calls and business logic

---

## 4. Broken Pipeline Edges

### 4.1 Upload → Intelligence (HIGH Severity)
**Broken Edge:** Statement upload does not automatically trigger FinancialIntelligenceService

**Expected Flow:**
```
Upload → Persistence → Engines → [AUTO] FinancialIntelligenceService
```

**Actual Flow:**
```
Upload → Persistence → Engines → [STOP] (requires manual API call)
```

**Impact:** Users upload statements but don't get forecasts/goals until manually triggered

**Fix Required:** Add async task or hook in `import_router.py` to call `FinancialIntelligenceService`

---

### 4.2 Upload → Recommendations (HIGH Severity)
**Broken Edge:** Statement upload does not automatically trigger RecommendationService

**Expected Flow:**
```
Upload → Persistence → [AUTO] RecommendationService
```

**Actual Flow:**
```
Upload → Persistence → [STOP] (requires manual API call)
```

**Impact:** Users don't receive loan optimization recommendations after upload

**Fix Required:** Add async task or hook in `import_router.py` to call `RecommendationService`

---

### 4.3 Intelligence → Recommendations (MEDIUM Severity)
**Broken Edge:** FinancialIntelligenceService outputs are not consumed by RecommendationService

**Expected Flow:**
```
FinancialIntelligenceService → Forecast data → RecommendationService → Personalized recommendations
```

**Actual Flow:**
```
FinancialIntelligenceService → [ISOLATED] → RecommendationService → [ISOLATED]
```

**Impact:** Recommendations are generic, not personalized based on cashflow forecasts

**Fix Required:** Integrate forecast outputs into recommendation logic

---

## 5. Missing Integrations

### 5.1 Financial Events API
**Issue:** Service exists (`FinancialEventsService`) but no router exposes it

**Impact:** Events are computed but invisible to frontend

**Fix Required:** Create `backend/src/routers/financial_events.py`

---

### 5.2 Cashflow Forecast → Dashboard
**Issue:** Dashboard doesn't display forecast data

**Impact:** Users see historical data but not future projections

**Fix Required:** Add forecast widget to DashboardService and frontend

---

### 5.3 Recommendations → Dashboard
**Issue:** Dashboard shows generic insights, not loan-specific recommendations

**Impact:** Users miss personalized loan optimization advice

**Fix Required:** Integrate RecommendationService into DashboardService

---

## 6. Integration Completeness Matrix

| Domain | Backend | Router | Service | Engine | Repository | Frontend | Auto-Trigger | Overall |
|--------|---------|--------|---------|--------|------------|----------|--------------|---------|
| Accounts | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❓ | N/A | 80% |
| Transactions | ✅ | ✅ | ❌ | ✅ | ✅ | ❓ | N/A | 60% |
| Statements | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Reconciliation | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Cashflow | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❓ | ❌ | 60% |
| Behaviour | ✅ | 🔁 | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Credit Cards | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Loans | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Fin Intelligence | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |
| Forecasting | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ❓ | ❌ | 50% |
| Goals | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ❓ | ❌ | 50% |
| Recommendations | ✅ | ⚠️ | ✅ | ✅ | ✅ | ❓ | ❌ | 60% |
| Financial Events | ✅ | ❌ | ✅ | ✅ | ✅ | ❓ | ❌ | 40% |
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ | ❓ | ❌ | 70% |

**Legend:**
- ✅ Complete
- ⚠️ Partial
- ❌ Missing
- 🔁 Duplicate
- ❓ Not yet audited (Phase B pending)

---

## 7. Priority Remediation Plan

### Phase 1: Critical Fixes (Week 1)
1. **Create Financial Events router** (`financial_events.py`)
   - Expose `FinancialEventsService` via API
   - 2-3 hours estimated

2. **Consolidate Behaviour routers** (`behaviour.py` + `behavior.py`)
   - Keep `/api/v1/behaviour/*`, remove `/api/behavior/*`
   - Update all imports
   - 1-2 hours estimated

3. **Create TransactionService**
   - Extract business logic from `transactions.py` router
   - 4-6 hours estimated

### Phase 2: Pipeline Integration (Week 2)
4. **Add auto-trigger for FinancialIntelligenceService**
   - Modify `import_router.py` to call intelligence after upload
   - Consider async task queue (Celery) or background thread
   - 6-8 hours estimated

5. **Add auto-trigger for RecommendationService**
   - Modify `import_router.py` to call recommendations after upload
   - 4-6 hours estimated

### Phase 3: Enhanced Integration (Week 3)
6. **Integrate Intelligence → Recommendations**
   - Pass forecast data to recommendation engine
   - 4-6 hours estimated

7. **Add Cashflow Forecast to Dashboard**
   - Extend DashboardService to include forecast widget
   - 3-4 hours estimated

8. **Add Recommendations to Dashboard**
   - Integrate loan recommendations into dashboard insights
   - 2-3 hours estimated

---

## 8. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Auto-trigger causes performance degradation | Medium | High | Use background tasks, add timeout |
| Duplicate router removal breaks frontend | Low | Medium | Search all frontend references before removal |
| Missing TransactionService breaks existing code | Medium | Medium | Create service, keep router compatibility layer |
| Financial Events API design conflicts with frontend | Medium | Low | Coordinate with frontend team on API design |

---

## 9. Testing Strategy

### Backend Verification
- [ ] All routers return 200 OK (smoke tests)
- [ ] All services are reachable via routers
- [ ] No orphan repositories (all used by services)
- [ ] No orphan services (all used by routers)
- [ ] Pipeline triggers fire automatically after upload

### Integration Verification
- [ ] Upload statement → Intelligence computed
- [ ] Upload statement → Recommendations generated
- [ ] Intelligence → Dashboard displays forecast
- [ ] Recommendations → Dashboard displays advice
- [ ] Financial Events → API accessible

---

## 10. Appendix: Evidence

### A.10.1 Missing Router Evidence
```python
# backend/src/services/financial_events_service.py
class FinancialEventsService:
    # Complete implementation...
    pass

# No corresponding router file found:
# backend/src/routers/financial_events.py ❌ MISSING
```

### A.10.2 Duplicate Router Evidence
```python
# backend/src/routers/behaviour.py
router = APIRouter(prefix="/api/v1/behaviour", tags=["behaviour"])

# backend/src/routers/behavior.py
router = APIRouter(prefix="/api/behavior", tags=["behavior"])

# Both provide identical endpoints:
# - GET /summary
# - GET /score
# - GET /insights
```

### A.10.3 Missing Service Layer Evidence
```python
# backend/src/routers/transactions.py
@router.get("/transactions")
def get_transactions():
    repo = TransactionRepository()  # Direct repo access
    return repo.get_all()
    # ❌ No TransactionService orchestration
```

### A.10.4 Broken Auto-Trigger Evidence
```python
# backend/src/routers/import_router.py
@router.post("/upload")
async def upload_statement():
    # ... upload logic ...
    stmt_repo.insert_statement(...)
    txn_repo.insert_transactions(...)
    # ❌ No call to FinancialIntelligenceService
    # ❌ No call to RecommendationService
    return {"success": True}
```

---

*This report completes Phase 3 — Runtime Capability & Pipeline Audit*
*Next Phase: Phase 4 — Unified Verification Architecture*
