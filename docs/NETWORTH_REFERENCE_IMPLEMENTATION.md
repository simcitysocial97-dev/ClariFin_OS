# NetWorth Reference Implementation

> **Status:** FROZEN — Canonical explainability reference
> **Date:** 2026-07-17
> **This implementation is the reference pattern that every future explainability capability must follow.**

---

## 1. Canonical Execution Flow

```
Backend Pydantic Model
    ↓  (FastAPI serialization)
API JSON Response
    ↓  (Zod validation)
DTO (typed)
    ↓  (Mapper — pure transformation)
Model (ViewModel)
    ↓  (React Query hook)
Widget / Drawer
```

### Layer Responsibilities

| Layer | File | Responsibility |
|-------|------|----------------|
| Pydantic Model | `backend/src/models/explanation.py` | Define response contract |
| Service | `backend/src/services/networth_service.py` | Build explanation data |
| Router | `backend/src/routers/networth.py` | Declare `response_model` |
| OpenAPI | `backend/clarifin_openapi.json` | Generated schema |
| Zod Schema | `frontend/lib/contracts/api/networth.ts` | Validate API response |
| DTO Type | Inferred from Zod (`NetWorthDto`) | Typed API response |
| Mapper | `frontend/lib/mappers/networth.ts` | Transform DTO → Model |
| Model | `frontend/lib/models/networth.ts` | ViewModel for UI |
| Hook | `frontend/lib/hooks/use-networth.ts` | Fetch + validate + map |
| Widget | `frontend/components/dashboard/widgets/money-position-widget.tsx` | Display |
| Drawer | `frontend/components/explainability/ExplainabilityDrawer.tsx` | Explainability UI |

---

## 2. Canonical Contracts

### 2.1 Backend Pydantic (`backend/src/models/explanation.py`)

```python
class NetWorthResponse(BaseModel):
    """Canonical API response for /api/networth endpoint."""
    net_worth_paise: int
    assets: dict[str, int]
    liabilities: dict[str, int]
    is_partial: bool
    partial_reason: str | None = None
    last_updated: str | None = None
    explanation: NetWorthExplanation | None = None
```

### 2.2 Frontend Zod (`frontend/lib/contracts/api/networth.ts`)

```typescript
export const NetWorthResponseSchema = z.object({
  net_worth_paise: z.number().int(),
  assets: z.object({
    total_paise: z.number().int(),
    accounts_paise: z.number().int(),
    investments_paise: z.number().int(),
    account_count: z.number().int(),
    investment_count: z.number().int(),
  }),
  liabilities: z.object({
    total_paise: z.number().int(),
    loans_paise: z.number().int(),
    cards_paise: z.number().int(),
    loan_count: z.number().int(),
    card_count: z.number().int(),
  }),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: NetWorthExplanationSchema.optional(),
})
```

### 2.3 Frontend Model (`frontend/lib/models/networth.ts`)

```typescript
export interface NetWorthModel {
  netWorthPaise: number
  assetsTotalPaise: number
  assetsAccountsPaise: number
  assetsInvestmentsPaise: number
  liabilitiesTotalPaise: number
  liabilitiesLoansPaise: number
  liabilitiesCardsPaise: number
  accountCount: number
  investmentCount: number
  loanCount: number
  cardCount: number
  trend: 'up' | 'down' | 'flat'
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: NetWorthExplanation | null
}
```

---

## 3. API Schema

### Endpoint

```
GET /api/networth
```

### Response (200)

```json
{
  "net_worth_paise": 123456,
  "assets": {
    "total_paise": 200000,
    "accounts_paise": 150000,
    "investments_paise": 50000,
    "account_count": 3,
    "investment_count": 2
  },
  "liabilities": {
    "total_paise": 76544,
    "loans_paise": 50000,
    "cards_paise": 26544,
    "loan_count": 1,
    "card_count": 2
  },
  "is_partial": false,
  "partial_reason": null,
  "last_updated": "2026-07-17T21:00:00",
  "explanation": {
    "netWorth": { ... },
    "assets": { ... },
    "liabilities": { ... },
    "confidenceReason": "Complete data available"
  }
}
```

### Explanation Structure

```json
{
  "metric": "net_worth",
  "value": 123456,
  "confidence": {
    "value": 10000,
    "reason": "Complete data available"
  },
  "evidence": [
    {
      "id": "account-balance-1",
      "type": "data",
      "description": "Account balance: Savings Account",
      "value": 100000,
      "sourceId": 1
    }
  ],
  "sources": [
    {
      "type": "account",
      "id": 1,
      "name": "Savings Account"
    }
  ],
  "calculationSteps": [
    {
      "stepId": "sum-accounts",
      "description": "Sum all account balances",
      "operation": "ADD",
      "inputIds": ["account-balance-1"],
      "outputId": "assets-accounts",
      "order": 1
    }
  ]
}
```

---

## 4. Mapper Rules

**File:** `frontend/lib/mappers/networth.ts`

### Transformation Rules

1. **Flatten nested structure** — `dto.assets.total_paise` → `model.assetsTotalPaise`
2. **Rename to camelCase** — `net_worth_paise` → `netWorthPaise`
3. **Derive UI flags** — `trend` calculated from assets vs liabilities
4. **Preserve explanation** — `dto.explanation` → `model.explanation` (NOT generated)
5. **No business logic** — Pure field mapping only
6. **No formatting** — Raw paise values preserved; formatting in components

### Forbidden Patterns

- ❌ Do NOT generate explanation in mapper
- ❌ Do NOT add business logic in mapper
- ❌ Do NOT format values in mapper
- ❌ Do NOT reconstruct explanation from other fields

---

## 5. UI Rules

### Widget (`money-position-widget.tsx`)

- Uses `DataStateWrapper` for loading/error/empty states
- Accesses `data.explanation?.netWorth` to show explain button
- Calls `showExplanation(data.explanation.netWorth)` to open drawer
- Uses `formatINRCompact()` for display formatting
- Only shows explain button when explanation exists

### Drawer (`ExplainabilityDrawer.tsx`)

- **Universal** — knows nothing about NetWorth, Loans, Cards, etc.
- Only knows about `Explanation` contract
- Four tabs: Overview, Calculation, Evidence, Sources
- Reused by every future capability

---

## 6. Explainability Rules

### Backend Rules

1. **Evidence is built from source data** — each account, loan, investment, card produces evidence
2. **Calculation steps are explicit** — each ADD/SUBTRACT step is documented
3. **Confidence is calculated** — starts at 10000 bps, reduced for missing data
4. **Sources are tracked** — each evidence item has a source reference
5. **Explanation is nested** — `NetWorthExplanation` contains `netWorth`, `assets`, `liabilities`

### Frontend Rules

1. **Explanation is preserved** — never reconstructed or generated on frontend
2. **Zod validates** — explanation structure is validated at the API boundary
3. **Mapper passes through** — explanation is mapped as-is
4. **Widget conditionally shows** — only shows explain button when explanation exists
5. **Drawer is generic** — accepts any `Explanation` object

---

## 7. Invariants

1. `net_worth_paise = assets.total_paise - liabilities.total_paise`
2. `assets.total_paise = assets.accounts_paise + assets.investments_paise`
3. `liabilities.total_paise = liabilities.loans_paise + liabilities.cards_paise`
4. All monetary values are in **paise** (integer)
5. All confidence values are in **basis points** (0-10000)
6. `explanation` is optional — may be `null` or absent
7. `last_updated` is always present (may be `null`)
8. `is_partial` is always present (boolean)

---

## 8. Extension Rules

When adding a new explainability capability:

1. **Backend:** Add Pydantic model → Service method → Router endpoint
2. **OpenAPI:** Regenerate to pick up new schema
3. **Frontend Zod:** Add schema in `frontend/lib/contracts/api/`
4. **Frontend DTO:** Infer type from Zod schema
5. **Frontend Model:** Add interface in `frontend/lib/models/`
6. **Frontend Mapper:** Add pure transformation function
7. **Frontend Hook:** Add fetch + validate + map hook
8. **Widget:** Consume model, show explain button
9. **Drawer:** Already universal — no changes needed

### Required Files for New Capability

```
backend/src/models/explanation.py  (extend or add model)
backend/src/services/              (add service method)
backend/src/routers/               (add endpoint)
frontend/lib/contracts/api/        (add Zod schema)
frontend/lib/models/               (add model interface)
frontend/lib/mappers/              (add mapper function)
frontend/lib/hooks/                (add hook)
frontend/components/               (add widget)
```

---

## 9. Forbidden Patterns

- ❌ **No explanation generation on frontend** — backend is the source of truth
- ❌ **No duplicated semantics** — don't redefine types that exist in Zod/OpenAPI
- ❌ **No renamed fields** — field names must match across the chain
- ❌ **No reconstructed values** — don't rebuild explanation from raw data
- ❌ **No business logic in mappers** — mappers are pure transformations
- ❌ **No formatting in models** — models hold raw values; components format
- ❌ **No capability-specific drawer** — use the universal ExplainabilityDrawer
- ❌ **No technical provenance in explanation** — business provenance only
- ❌ **No new abstractions** — follow the existing pattern exactly

---

## 10. Checklist for Future Capabilities

- [ ] Backend Pydantic model defined
- [ ] Backend service builds explanation
- [ ] Backend router declares `response_model`
- [ ] OpenAPI schema generated
- [ ] Frontend Zod schema validates response
- [ ] Frontend DTO type inferred from Zod
- [ ] Frontend model interface defined
- [ ] Frontend mapper transforms DTO → Model
- [ ] Frontend hook fetches + validates + maps
- [ ] Widget shows explain button conditionally
- [ ] Drawer displays explanation (no changes needed)
- [ ] All monetary values in paise (integer)
- [ ] All confidence values in basis points (0-10000)
- [ ] Explanation preserved from backend (not generated)
- [ ] No business logic in mapper
- [ ] No formatting in model
- [ ] No duplicated types
- [ ] No renamed fields
- [ ] Tests pass

---

## 11. Verification Commands

```bash
# Backend
cd backend && ./venv/bin/python3 -m ruff check . && ./venv/bin/python3 -m mypy .

# Frontend
cd frontend && npm run type-check && npm run lint && npm test -- --run && npm run build
```

---

## Declaration

This implementation is now the **reference pattern** that every future explainability capability must follow. No deviations from this architecture are permitted without explicit architecture review.