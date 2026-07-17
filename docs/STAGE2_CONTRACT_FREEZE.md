# Stage 2 Contract Freeze — Explainability Contracts

## PART 1 — Verify NetWorth Response Model

### Evidence

**Router Return Annotation** (`backend/src/routers/networth.py`, line 12):
```python
@router.get("/networth")
def get_networth() -> dict[str, Any]:
```

**Actual Response Model**: None. The endpoint returns `dict[str, Any]` without a Pydantic response model.

**Response Object Returned** (`backend/src/services/networth_service.py`, line 322-344):
```python
return {
    "net_worth_paise": net_worth_paise,
    "assets": {...},
    "liabilities": {...},
    "is_partial": ...,
    "partial_reason": ...,
    "explanation": networth_explanation.model_dump(),  # NetWorthExplanation
}
```

**Explanation Model Used** (`backend/src/models/explanation.py`):
- `SourceReference` (lines 24-29) — business provenance
- `Evidence` (lines 32-38) — data evidence
- `CalculationStep` (lines 41-48) — calculation steps
- `Confidence` (lines 51-54) — confidence in basis points
- `Explanation` (lines 57-64) — complete explanation
- `NetWorthExplanation` (lines 67-72) — net worth specific

**OpenAPI Schema Produced** (`backend/clarifin_openapi.json`, lines 5003-5025):
```json
"/api/networth": {
  "get": {
    "responses": {
      "200": {
        "schema": {
          "additionalProperties": true,
          "type": "object",
          "title": "Response Get Networth Api Networth Get"
        }
      }
    }
  }
}
```

### Canonical Response Model That Should Exist

```python
class NetWorthResponse(BaseModel):
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
| `SourceReference` | `backend/src/models/explanation.py:24-29` | `frontend/lib/explainability/contracts/SourceReference.ts:11-54` | **DUPLICATE** (field name mismatch: `type` vs `sourceType`) |
| `SourceReference` | `backend/src/models/explanation.py:24-29` | `frontend/lib/contracts/api/networth.ts:10-47` | **DUPLICATE** (technical provenance fields) |
| `Evidence` | `backend/src/models/explanation.py:32-38` | `frontend/lib/explainability/contracts/Evidence.ts:16-27` | **CANONICAL** (matches) |
| `Evidence` | `backend/src/models/explanation.py:32-38` | `frontend/lib/contracts/api/networth.ts:50-56` | **WRAPPER** (Zod schema for validation) |
| `CalculationStep` | `backend/src/models/explanation.py:41-48` | `frontend/lib/explainability/contracts/CalculationStep.ts:10-31` | **CANONICAL** (matches) |
| `CalculationStep` | `backend/src/models/explanation.py:41-48` | `frontend/lib/contracts/api/networth.ts:59-66` | **WRAPPER** (Zod schema for validation) |
| `Confidence` | `backend/src/models/explanation.py:51-54` | `frontend/lib/explainability/contracts/Confidence.ts:12-20` | **CANONICAL** (matches) |
| `Confidence` | `backend/src/models/explanation.py:51-54` | `frontend/lib/contracts/api/networth.ts:69-72` | **WRAPPER** (Zod schema for validation) |
| `Explanation` | `backend/src/models/explanation.py:57-64` | `frontend/lib/explainability/contracts/Explanation.ts:16-23` | **CANONICAL** (matches) |
| `Explanation` | `backend/src/models/explanation.py:57-64` | `frontend/lib/contracts/api/networth.ts:75-82` | **WRAPPER** (Zod schema for validation) |
| `NetWorthExplanation` | `backend/src/models/explanation.py:67-72` | `frontend/lib/contracts/api/networth.ts:85-90` | **WRAPPER** (Zod schema for validation) |
| `NetWorthExplanation` | `backend/src/models/explanation.py:67-72` | `frontend/lib/models/networth.ts:18-23` | **WRAPPER** (TypeScript interface) |

---

## PART 3 — SourceReference Decision

### Production Consumers

**Backend SourceReference** (`backend/src/models/explanation.py:24-29`):
- Used in `NetWorthService.calculate_with_explanation()` (lines 127-131, 144-148, 161-165, 187-192)
- Populated with: `type="account"`, `type="investment"`, `type="loan"`, `type="statement"`
- Fields: `type`, `id`, `name`, `date`

**Frontend SourceReference** (`frontend/lib/explainability/contracts/SourceReference.ts:11-54`):
- Used in `Explanation` interface (line 21)
- Used in `NetWorthModel` (line 47)
- Used in `MoneyPositionContent` component (line 33)
- Fields: `sourceType`, `table`, `recordId`, `repository`, `service`, `engine`, `router`, `endpoint`, `function`, `file`, `line`, `statementId`, `transactionId`, `description`

### Decision: **Business Provenance**

The backend only sends business provenance fields (`type`, `id`, `name`, `date`). The technical provenance fields (`function`, `file`, `line`, etc.) are **never populated** and have **no production consumer**.

**Recommendation**: Remove technical provenance fields from frontend SourceReference. Keep only business provenance.

---

## PART 4 — Frontend Contract Duplication

### SourceReference Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/SourceReference.ts` | Interface | **Canonical** (should be) |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **DUPLICATE** — should be removed |

### Explanation Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Explanation.ts` | Interface | **Canonical** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |
| `frontend/lib/models/networth.ts` | Interface | **WRAPPER** — for model typing |

### Evidence Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Evidence.ts` | Interface | **Canonical** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### Confidence Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/Confidence.ts` | Interface + functions | **Canonical** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### CalculationStep Definitions

| Location | Type | Status |
|----------|------|--------|
| `frontend/lib/explainability/contracts/CalculationStep.ts` | Interface | **Canonical** |
| `frontend/lib/contracts/api/networth.ts` | Zod schema | **WRAPPER** — for validation only |

### Duplication Resolution

- `frontend/lib/contracts/api/networth.ts` should **DELETE** its SourceReferenceSchema, EvidenceSchema, CalculationStepSchema, ConfidenceSchema, ExplanationSchema, NetWorthExplanationSchema
- These should be **IMPORTED** from `@/lib/explainability/contracts` instead
- The Zod schemas for validation should be generated from the canonical interfaces

---

## PART 5 — Migration Plan

| File | Action |
|------|--------|
| `backend/src/routers/networth.py` | **UPDATE** — add `response_model=NetWorthResponse` to endpoint |
| `backend/src/models/explanation.py` | **NO CHANGE** — already canonical |
| `frontend/lib/contracts/api/networth.ts` | **DELETE** — remove duplicate schemas, import from explainability |
| `frontend/lib/explainability/contracts/SourceReference.ts` | **UPDATE** — remove technical provenance fields, rename `sourceType` to `type` |
| `frontend/lib/explainability/contracts/index.ts` | **NO CHANGE** — re-exports are correct |
| `frontend/lib/models/networth.ts` | **NO CHANGE** — imports from explainability are correct |
| `frontend/lib/mappers/networth.ts` | **NO CHANGE** — preserves explanation as-is |
| `frontend/lib/hooks/use-networth.ts` | **NO CHANGE** — uses NetWorthResponseSchema |
| `frontend/api-schema.json` | **NO CHANGE** — will auto-update from OpenAPI |
| `backend/api_types.ts` | **NO CHANGE** — will auto-update from OpenAPI |

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

This document was created to freeze the canonical explainability contracts before Stage 2.5 implementation begins.