# Stage 2 Contract Freeze — Explainability Contracts

## PART 1 — Verify NetWorth Response Model

### Evidence

**Router Return Annotation** (`backend/src/routers/networth.py`, line 10-11):
```python
@router.get("/networth", response_model=NetWorthResponse)
def get_networth() -> NetWorthResponse:
```

**Response Object Returned** (`backend/src/services/networth_service.py`):
```python
return NetWorthResponse(
    net_worth_paise=net_worth_paise,
    assets={...},
    liabilities={...},
    is_partial=...,
    partial_reason=...,
    explanation=networth_explanation,
)
```

**OpenAPI Schema Produced** (`backend/clarifin_openapi.json`, lines 5016-5018):
```json
"schema": {
  "$ref": "#/components/schemas/NetWorthResponse"
}
```

### Canonical Response Model

```python
class NetWorthResponse(BaseModel):
    """Canonical API response for /api/networth endpoint."""
    net_worth_paise: int
    assets: dict[str, int]  # {total_paise, accounts_paise, investments_paise, account_count, investment_count}
    liabilities: dict[str, int]  # {total_paise, loans_paise, cards_paise, loan_count, card_count}
    is_partial: bool
    partial_reason: str | None = None
    explanation: NetWorthExplanation | None = None
```

---

## PART 2 — Canonical Contract Audit

| Contract | Backend Location | Frontend Location | Classification |
|----------|------------------|-----------------|----------------|
| `SourceReference` | `backend/src/models/explanation.py:24-29` | `frontend/lib/explainability/contracts/SourceReference.ts:11-47` | **CANONICAL** (now matches) |
| `SourceReference` | `backend/src/models/explanation.py:24-29` | `frontend/lib/contracts/api/networth.ts:10-34` | **WRAPPER** (Zod schema for validation) |
| `Evidence` | `backend/src/models/explanation.py:32-38` | `frontend/lib/explainability/contracts/Evidence.ts:16-27` | **CANONICAL** (matches) |
| `Evidence` | `backend/src/models/explanation.py:32-38` | `frontend/lib/contracts/api/networth.ts:37-43` | **WRAPPER** (Zod schema for validation) |
| `CalculationStep` | `backend/src/models/explanation.py:41-48` | `frontend/lib/explainability/contracts/CalculationStep.ts:10-31` | **CANONICAL** (matches) |
| `CalculationStep` | `backend/src/models/explanation.py:41-48` | `frontend/lib/contracts/api/networth.ts:46-53` | **WRAPPER** (Zod schema for validation) |
| `Confidence` | `backend/src/models/explanation.py:51-54` | `frontend/lib/explainability/contracts/Confidence.ts:12-20` | **CANONICAL** (matches) |
| `Confidence` | `backend/src/models/explanation.py:51-54` | `frontend/lib/contracts/api/networth.ts:56-59` | **WRAPPER** (Zod schema for validation) |
| `Explanation` | `backend/src/models/explanation.py:57-64` | `frontend/lib/explainability/contracts/Explanation.ts:16-23` | **CANONICAL** (matches) |
| `Explanation` | `backend/src/models/explanation.py:57-64` | `frontend/lib/contracts/api/networth.ts:62-69` | **WRAPPER** (Zod schema for validation) |
| `NetWorthExplanation` | `backend/src/models/explanation.py:67-72` | `frontend/lib/contracts/api/networth.ts:72-77` | **WRAPPER** (Zod schema for validation) |
| `NetWorthExplanation` | `backend/src/models/explanation.py:67-72` | `frontend/lib/models/networth.ts:18-23` | **WRAPPER** (TypeScript interface) |

---

## PART 3 — SourceReference Decision

### Production Consumers

**Backend SourceReference** (`backend/src/models/explanation.py:24-29`):
- Used in `NetWorthService.calculate_with_explanation()`
- Populated with: `type="account"`, `type="investment"`, `type="loan"`, `type="statement"`
- Fields: `type`, `id`, `name`, `date`

**Frontend SourceReference** (`frontend/lib/explainability/contracts/SourceReference.ts:11-47`):
- Used in `Explanation` interface
- Used in `NetWorthModel`
- Used in `MoneyPositionContent` component
- Fields: `type`, `id`, `name`, `date` (now matches backend)

### Decision: **Business Provenance** ✅ IMPLEMENTED

The backend only sends business provenance fields (`type`, `id`, `name`, `date`). The technical provenance fields have been **removed** from frontend SourceReference.

---

## PART 4 — Frontend Contract Duplication

### SourceReference Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/SourceReference.ts` | Interface | **CANONICAL** (now matches backend) |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### Explanation Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Explanation.ts` | Interface | **CANONICAL** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |
| `frontend/lib/models/networth.ts` | Interface | **WRAPPER** — for model typing |

### Evidence Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Evidence.ts` | Interface | **CANONICAL** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### Confidence Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Confidence.ts` | Interface + functions | **CANONICAL** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### CalculationStep Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/CalculationStep.ts` | Interface | **CANONICAL** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

---

## PART 5 — Implementation Status

| File | Action | Status |
|------|--------|--------|
| `backend/src/routers/networth.py` | **UPDATE** — add `response_model=NetWorthResponse` | ✅ DONE |
| `backend/src/models/explanation.py` | **ADD** — `NetWorthResponse` class | ✅ DONE |
| `backend/src/services/networth_service.py` | **UPDATE** — return `NetWorthResponse` | ✅ DONE |
| `frontend/lib/contracts/api/networth.ts` | **UPDATE** — align with backend | ✅ DONE |
| `frontend/lib/explainability/contracts/SourceReference.ts` | **UPDATE** — remove technical fields | ✅ DONE |
| `frontend/lib/explainability/flattenExplanation.ts` | **UPDATE** — use `type`/`id` | ✅ DONE |
| `frontend/components/explainability/components/SourceCard.tsx` | **UPDATE** — use `type`/`id`/`name`/`date` | ✅ DONE |
| `frontend/components/explainability/panels/SourcesPanel.tsx` | **UPDATE** — simplify columns | ✅ DONE |
| `backend/clarifin_openapi.json` | **REGENERATE** — from FastAPI | ✅ DONE |
| `backend/api_types.ts` | **REGENERATE** — from OpenAPI | ✅ DONE |
| `frontend/api-schema.json` | **REGENERATE** — from OpenAPI | ✅ DONE |

---

## PART 6 — Freeze Rules

**Rule 1**: Backend Pydantic models are canonical. All frontend types must derive from them.

**Rule 2**: Frontend contracts must mirror backend. No independent type definitions.

**Rule 3**: No capability owns explainability contracts. They live in `lib/explainability/contracts/`.

**Rule 4**: OpenAPI is the only source of generated API types. `api_types.ts` must be generated, not hand-written.

**Rule 5**: Mapper layer may transform but never redefine contracts. It preserves or adapts, not defines.

**Rule 6**: Business provenance only. No implementation-detail leakage into API.

**Rule 7**: All API endpoints must declare `response_model`. No `dict[str, Any]` returns.

**Rule 8**: Zod schemas for validation must be generated from canonical interfaces, not duplicated.

---

## PART 7 — Git Checkpoint

**Stage 2.6 Implementation Complete** — All explainability contracts canonicalized.

- OpenAPI regenerated with proper `NetWorthResponse` schema
- API types regenerated with strong typing
- SourceReference aligned between backend and frontend
- All validation passing: type-check ✓, ruff ✓, mypy (pre-existing issues only)