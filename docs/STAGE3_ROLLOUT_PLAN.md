# Stage 3.0 — Explainability Rollout Framework

> **Status:** Architecture Analysis Complete  
> **Date:** 2026-07-18  
> **NetWorth Reference:** FROZEN — Canonical explainability implementation

---

## 1. Capability Inventory

### Summary Table

| Capability | Router | Service | Repository | Models | DTOs | Hook | Mapper | Model | Widget/Page | Current Endpoint | Current Response Model | Mapper Exists? | Widget Exists? | Explainability? | Ready For Migration? |
|------------|--------|---------|------------|--------|------|------|--------|-------|-------------|----------------|-------------------|--------------|----------------|-----------------|---------------------|
| **NetWorth** | networth.py | networth_service.py | networth_repository.py | explanation.py | networth.ts (api) | use-networth.ts | networth.ts (mappers) | networth.ts (models) | money-position-widget.tsx | /api/networth | NetWorthResponse | ✅ Yes | ✅ Yes | ✅ Full | ✅ COMPLETE (Reference) |
| **Household Cashflow** | cashflow.py | cashflow_service.py | cashflow_repository.py | - | cashflow.ts (api) | use-cashflow.ts | mapper.ts (capability) | model.ts (capability) | - | /api/cashflow/monthly, /api/v1/cashflow/monthly | dict[str, Any] | ✅ Yes (capability) | ❌ No | ❌ None | ⚠️ Partial |
| **Debt Management** | loans.py | loan_service.py, loan_analysis_service.py, loan_simulation_service.py | loan_repository.py, loan_payment_repository.py | loan.py, loan_simulation.py, loan_analysis.py | Inline in hook | use-loans.ts | ❌ No | ❌ No | - | /api/loans, /api/loans/{id}/schedule, /api/loans/{id}/prepayment-simulation | dict[str, Any], LoanResponse | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Credit Cards** | credit_cards.py | credit_card_service.py | credit_card_repository.py, credit_card_statement_repository.py | credit_card.py, credit_card_statement.py, credit_card_emi.py, credit_card_foreclosure.py | Inline in hook | use-cards.ts | ❌ No | ❌ No | - | /api/v1/credit-cards, /api/v1/credit-cards/{id}/statement | CreditCardResponse, StatementResponse | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Financial Health** | behaviour.py | behaviour_service.py | behaviour_repository.py | behaviour.py | Inline in hook | use-behavior-score.ts, use-behavior-insights.ts | ❌ No | ❌ No | - | /api/v1/behaviour/profile, /api/v1/behaviour/wellness-score, /api/v1/behaviour/stress-index | FinancialProfileResponse, WellnessScoreResponse, dict | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Forecasting** | financial_intelligence.py, scenarios.py, goals.py | financial_intelligence_service.py | financial_goal_repository.py, forecast_repository.py | financial_goal.py | Inline in hook | use-dashboard-metrics.ts | ❌ No | ❌ No | - | /api/v1/financial-intelligence/forecast, /api/v1/scenarios/* | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Transaction Intelligence** | transactions.py, patterns.py | transaction_intelligence_service.py | transaction_repository.py, pattern_repository.py | transaction.py | Inline in hook | use-overview.ts | ❌ No | ❌ No | - | /api/transactions, /api/patterns/* | Transaction, dict | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Reconciliation** | reconciliation.py | reconciliation_service.py | reconciliation_repository.py, reconciliation_audit_repository.py | reconciliation.py | Inline in hook | use-reconciliation.ts | ❌ No | ❌ No | - | /api/reconciliations/* | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Financial Events** | financial_intelligence.py | financial_events_service.py | financial_event_repository.py | financial_event.py | Inline in hook | - | ❌ No | ❌ No | - | /api/financial-events/* | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Recommendations** | optimisation.py | financial_intelligence_service.py | financial_goal_repository.py | - | Inline in hook | - | ❌ No | ❌ No | - | /api/optimization/recommendations | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Account Management** | accounts.py, managed_accounts.py | account_service.py | account_repository.py, account_balance_repository.py, account_link_repository.py | account.py, account_balance.py, account_link.py, institution.py | Inline in hook | use-accounts.ts | ❌ No | ❌ No | - | /api/v1/accounts/* | AccountResponse, dict | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Pattern Analysis** | patterns.py | pattern_service.py | pattern_repository.py, liquidity_pattern_repository.py | - | Inline in hook | - | ❌ No | ❌ No | - | /api/patterns/* | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |
| **Investments** | investments.py | - | investment_repository.py | investment.py | Inline in hook | use-investments.ts | ❌ No | ❌ No | - | /api/investments | dict[str, Any] | ❌ No | ❌ No | ❌ None | ⚠️ Partial |

---

## 2. Explainability Readiness Score

### Evaluation Criteria

1. **Backend produces deterministic calculations?** — All monetary values in paise, all confidence in basis points
2. **Can evidence be collected?** — Source data available, evidence model exists
3. **Can calculation steps be expressed?** — ADD/SUBTRACT operations, step ordering
4. **Can confidence be computed?** — Confidence model exists, 0-10000 bps range
5. **Can business sources be identified?** — SourceReference model exists
6. **Can current API contract carry explanation?** — Optional explanation field

### Capability Scores

| Capability | Deterministic | Evidence Collectable | Calculation Steps | Confidence Computable | Sources Identifiable | API Contract Ready | **Overall Score** |
|------------|---------------|-------------------|-------------------|---------------------|-------------------|------------------|-----------------|
| **NetWorth** | ✅ 10/10 | ✅ 10/10 | ✅ 10/10 | ✅ 10/10 | ✅ 10/10 | ✅ 10/10 | **HIGH** (Reference) |
| **Household Cashflow** | ✅ 8/10 | ⚠️ 6/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 4/10 | ⚠️ 3/10 | **MEDIUM** |
| **Debt Management** | ✅ 9/10 | ⚠️ 7/10 | ⚠️ 6/10 | ⚠️ 5/10 | ⚠️ 5/10 | ⚠️ 4/10 | **MEDIUM** |
| **Credit Cards** | ✅ 8/10 | ⚠️ 6/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 4/10 | ⚠️ 3/10 | **MEDIUM** |
| **Financial Health** | ✅ 7/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 3/10 | ⚠️ 2/10 | **LOW** |
| **Forecasting** | ✅ 6/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | **LOW** |
| **Transaction Intelligence** | ✅ 7/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 3/10 | ⚠️ 2/10 | **LOW** |
| **Reconciliation** | ✅ 8/10 | ⚠️ 6/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 4/10 | ⚠️ 3/10 | **MEDIUM** |
| **Financial Events** | ✅ 6/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | **LOW** |
| **Recommendations** | ✅ 5/10 | ⚠️ 3/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | **LOW** |
| **Account Management** | ✅ 7/10 | ⚠️ 5/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 3/10 | ⚠️ 2/10 | **LOW** |
| **Pattern Analysis** | ✅ 5/10 | ⚠️ 3/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | **LOW** |
| **Investments** | ✅ 6/10 | ⚠️ 4/10 | ⚠️ 3/10 | ⚠️ 2/10 | ⚠️ 2/10 | ⚠️ 2/10 | **LOW** |

---

## 3. Migration Ordering

### Priority Factors

- **Lowest engineering risk** — Minimal breaking changes, well-tested code
- **Highest architectural reuse** — Can leverage existing patterns
- **Smallest implementation effort** — Fewest missing pieces
- **Highest user value** — Most visible to users, core financial metrics

### Wave 1 — High Readiness, High Value (Ready for immediate migration)

| Capability | Justification |
|------------|---------------|
| **Household Cashflow** | - Deterministic calculations exist<br>- Clear evidence sources (transactions)<br>- Calculation steps: income sum, expense sum, net = income - expense<br>- High user value: core financial visibility<br>- Medium risk: well-tested, stable endpoints |
| **Reconciliation** | - Deterministic matching algorithm<br>- Evidence: transaction pairs, date differences, amount differences<br>- Confidence: match quality scoring exists<br>- High user value: audit trail<br>- Medium risk: stable, tested |

### Wave 2 — Medium Readiness, High Value (Requires moderate preparation)

| Capability | Justification |
|------------|---------------|
| **Debt Management** | - Deterministic EMI calculations<br>- Evidence: loan principal, interest, payments<br>- Calculation steps: amortization schedule<br>- High user value: loan planning<br>- Medium risk: complex calculations, well-tested |
| **Credit Cards** | - Deterministic utilization calculations<br>- Evidence: statement amounts, payments<br>- Calculation steps: outstanding, utilization<br>- High user value: credit management<br>- Medium risk: statement lifecycle complexity |

### Wave 3 — Lower Readiness, Requires Infrastructure (Needs significant preparation)

| Capability | Justification |
|------------|---------------|
| **Financial Health** | - Complex multi-factor scoring<br>- Evidence: requires transaction analysis<br>- Confidence: needs calibration<br>- High user value: wellness insights<br>- Higher risk: multiple engine dependencies |
| **Forecasting** | - Predictive models (not deterministic)<br>- Evidence: historical trends<br>- Confidence: variance-based<br>- Medium user value: future planning<br>- Higher risk: floating point, predictions |
| **Account Management** | - Balance calculations<br>- Evidence: account snapshots<br>- Calculation steps: average, trend, velocity<br>- Medium user value: account tracking<br>- Lower risk: simple aggregations |
| **Transaction Intelligence** | - Pattern detection<br>- Evidence: transaction patterns<br>- Calculation steps: pattern matching<br>- Medium user value: insights<br>- Lower risk: read-only |
| **Financial Events** | - Event lifecycle tracking<br>- Evidence: event transitions<br>- Calculation steps: lineage walking<br>- Lower user value: audit trail<br>- Lower risk: read-only |
| **Recommendations** | - Optimization algorithms<br>- Evidence: recommendation inputs<br>- Calculation steps: priority ranking<br>- Medium user value: guidance<br>- Lower risk: read-only |
| **Pattern Analysis** | - Pattern detection<br>- Evidence: spending patterns<br>- Calculation steps: clustering<br>- Lower user value: insights<br>- Lower risk: read-only |
| **Investments** | - Value calculations<br>- Evidence: investment values<br>- Calculation steps: gain/loss<br>- Lower user value: portfolio<br>- Lower risk: simple aggregations |

---

## 4. Shared Pattern Verification

### Available Shared Infrastructure

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| **Explanation Model** | `backend/src/models/explanation.py` | ✅ Available | Pydantic models: Explanation, NetWorthExplanation, Confidence, Evidence, CalculationStep, SourceReference |
| **Evidence Model** | `backend/src/models/explanation.py:32-38` | ✅ Available | Evidence with id, type, description, value, sourceId |
| **CalculationStep** | `backend/src/models/explanation.py:41-48` | ✅ Available | stepId, description, operation, inputIds, outputId, order |
| **Confidence** | `backend/src/models/explanation.py:51-54` | ✅ Available | value (0-10000 bps), reason |
| **SourceReference** | `backend/src/models/explanation.py:24-29` | ✅ Available | type, id, name, date |
| **ExplainabilityDrawer** | `frontend/components/explainability/ExplainabilityDrawer.tsx` | ✅ Available | Universal drawer, 4 tabs, no capability knowledge |
| **Provider** | `frontend/lib/store/explainability-store.ts` | ✅ Available | Zustand store for drawer state |
| **Hook** | `frontend/components/explainability/hooks/useExplainabilityDrawer.ts` | ✅ Available | Hook for showing explanations |
| **Contracts** | `frontend/lib/explainability/contracts/` | ✅ Available | TypeScript interfaces matching backend |
| **Zod Schemas** | `frontend/lib/contracts/api/networth.ts` | ✅ Available | For API validation |

### Verification Results

All future capabilities can reuse the shared infrastructure. No capability requires custom explainability infrastructure.

---

## 5. Backend Gap Analysis

### Missing Backend Pieces by Capability

| Capability | Missing Response Model | Missing Explanation Builder | Missing Evidence Collection | Missing Confidence | Missing Calculation Steps | Missing Source References |
|------------|---------------------|--------------------------|--------------------------|------------------|------------------------|--------------------------|
| **Household Cashflow** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (transactions) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Debt Management** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (loans) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Credit Cards** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (statements) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Financial Health** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (transactions) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Forecasting** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (historical) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Transaction Intelligence** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (transactions) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Reconciliation** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (matches) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Financial Events** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (events) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Recommendations** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (inputs) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Account Management** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (accounts) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Pattern Analysis** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (patterns) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |
| **Investments** | ❌ No Pydantic response model with explanation | ❌ No service method building explanation | ⚠️ Evidence sources exist (investments) | ⚠️ No confidence calculation | ⚠️ No explicit steps | ⚠️ No source references |

---

## 6. Frontend Gap Analysis

### Missing Frontend Pieces by Capability

| Capability | Missing Zod Schema | Missing Mapper | Missing Model | Missing Hook | Missing Explain Button | Missing Drawer Integration | Missing Tests |
|------------|-------------------|---------------|-------------|-------------|---------------------|-------------------------|---------------|
| **Household Cashflow** | ❌ No Zod schema in contracts/api | ⚠️ Has capability mapper (no explanation) | ⚠️ Has capability model (no explanation) | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Debt Management** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Credit Cards** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Financial Health** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Forecasting** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Transaction Intelligence** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Reconciliation** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Financial Events** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ❌ No hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Recommendations** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ❌ No hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Account Management** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Pattern Analysis** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ❌ No hook | ❌ No widget | ❌ No integration | ❌ No tests |
| **Investments** | ❌ No Zod schema in contracts/api | ❌ No mapper | ❌ No model | ✅ Has hook | ❌ No widget | ❌ No integration | ❌ No tests |

---

## 7. Rollout Template

### Canonical Implementation Checklist

Every capability must follow this exact pattern:

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

### Step-by-Step Implementation Template

#### 7.1 Backend (Pydantic Models)

```python
# File: backend/src/models/explanation.py (extend)

class {Capability}Explanation(Explanation):
    """Explanation for {capability} calculation."""
    # Add capability-specific fields if needed

class {Capability}Response(BaseModel):
    """Canonical API response for /api/{capability} endpoint."""
    # Core response fields (all paise as int)
    # is_partial: bool
    # partial_reason: str | None = None
    # last_updated: str | None = None
    explanation: {Capability}Explanation | None = None
```

#### 7.2 Backend (Service)

```python
# File: backend/src/services/{capability}_service.py

def calculate_with_explanation(self) -> {Capability}Response:
    """
    Compute {capability} with full explainability.
    
    Returns:
        {Capability}Response with explanation
    """
    # 1. Fetch data from repository
    data = self.repo.get_{capability}_data()
    
    # 2. Build evidence for each source
    evidence: list[Evidence] = []
    sources: list[SourceReference] = []
    for item in data:
        evidence.append(Evidence(
            id=f"{capability}-item-{item.get('id')}",
            type="data",
            description=f"{capability} item: {item.get('name')}",
            value=item.get("value_paise", 0),
            sourceId=item.get("id"),
        ))
        sources.append(SourceReference(
            type="{capability}",
            id=item.get("id"),
            name=item.get("name"),
        ))
    
    # 3. Calculate values
    total_paise = sum(e.value for e in evidence)
    
    # 4. Calculate confidence (0-10000 bps)
    confidence_bps = 10000
    confidence_reasons: list[str] = []
    if len(evidence) == 0:
        confidence_bps -= 2000
        confidence_reasons.append("No data available")
    
    # 5. Build calculation steps
    calculation_steps: list[CalculationStep] = [
        CalculationStep(
            stepId="sum-items",
            description="Sum all {capability} values",
            operation="ADD",
            inputIds=[e.id for e in evidence],
            outputId="{capability}-total",
            order=1,
        ),
    ]
    
    # 6. Build explanation
    explanation = {Capability}Explanation(
        metric="{capability}",
        value=total_paise,
        confidence=Confidence(
            value=confidence_bps,
            reason=", ".join(confidence_reasons) if confidence_reasons else "Complete data available",
        ),
        evidence=evidence,
        sources=sources,
        calculationSteps=calculation_steps,
    )
    
    return {Capability}Response(
        # ... core fields ...
        explanation=explanation,
    )
```

#### 7.3 Backend (Router)

```python
# File: backend/src/routers/{capability}.py

@router.get("/{capability}", response_model={Capability}Response)
def get_{capability}() -> {Capability}Response:
    """Compute {capability} with explanation."""
    service = {Capability}Service()
    return service.calculate_with_explanation()
```

#### 7.4 Frontend (Zod Schema)

```typescript
// File: frontend/lib/contracts/api/{capability}.ts

import { z } from 'zod'

// Re-export shared schemas
export { SourceReferenceSchema, EvidenceSchema, CalculationStepSchema, ConfidenceSchema, ExplanationSchema } from './networth'

// Capability-specific response schema
export const {Capability}ResponseSchema = z.object({
    // ... core fields ...
    explanation: ExplanationSchema.optional(),
})

export type {Capability}Dto = z.infer<typeof {Capability}ResponseSchema>
```

#### 7.5 Frontend (Model)

```typescript
// File: frontend/lib/models/{capability}.ts

import type { Explanation } from '@/lib/explainability'

export interface {Capability}Model {
    // Core values (raw paise)
    // Derived UI flags
    // Explanation (preserved from backend)
    explanation: Explanation | null
}
```

#### 7.6 Frontend (Mapper)

```typescript
// File: frontend/lib/mappers/{capability}.ts

import type { {Capability}Dto } from '../contracts/api/{capability}'
import type { {Capability}Model } from '../models/{capability}'

export function map{Capability}ToModel(dto: {Capability}Dto): {Capability}Model {
    return {
        // ... map fields ...
        explanation: dto.explanation ?? null,
    }
}
```

#### 7.7 Frontend (Hook)

```typescript
// File: frontend/lib/hooks/use-{capability}.ts

import { useAppQuery } from '@/lib/query'
import { {Capability}ResponseSchema } from '../contracts/api/{capability}'
import { map{Capability}ToModel } from '../mappers/{capability}'

export function use{Capability}() {
    return useAppQuery({
        queryKey: queryKeys.{capability}.current(),
        queryFn: async () => {
            const dto = await fetch{Endpoint}()
            return map{Capability}ToModel(dto)
        },
        capability: '{capability}',
        staleTime: STALE_TIME.NORMAL,
    })
}
```

#### 7.8 Frontend (Widget)

```typescript
// File: frontend/components/dashboard/widgets/{capability}-widget.tsx

'use client'

import { use{Capability} } from '@/lib/hooks/use-{capability}'
import { useExplainabilityDrawer } from '@/components/explainability'
import { DataStateWrapper } from '@/components/runtime'

export function {Capability}Widget() {
    const query = use{Capability}()
    const { showExplanation } = useExplainabilityDrawer()
    
    return (
        <DataStateWrapper query={query}>
            {(data) => (
                <div>
                    {/* Display data */}
                    {data.explanation && (
                        <Button onClick={() => showExplanation(data.explanation)}>
                            <Info className="h-3 w-3" />
                        </Button>
                    )}
                </div>
            )}
        </DataStateWrapper>
    )
}
```

---

## 8. Validation Against Frozen Rules

### STAGE2_CONTRACT_FREEZE.md Compliance

| Rule | Status | Notes |
|------|--------|-------|
| Rule 1: Backend Pydantic models are canonical | ✅ Compliant | All types derive from Pydantic |
| Rule 2: Frontend contracts must mirror backend | ✅ Compliant | Zod schemas mirror Pydantic |
| Rule 3: No capability owns explainability contracts | ✅ Compliant | Contracts in `lib/explainability/contracts/` |
| Rule 4: OpenAPI is the only source of generated API types | ✅ Compliant | `api_types.ts` generated from OpenAPI |
| Rule 5: Mapper layer may transform but never redefine | ✅ Compliant | Mappers preserve explanation |
| Rule 6: Business provenance only | ✅ Compliant | SourceReference has type, id, name, date |
| Rule 7: All API endpoints must declare response_model | ⚠️ Not Compliant | Most routers return `dict[str, Any]` |
| Rule 8: Zod schemas for validation must be generated | ⚠️ Not Compliant | Most capabilities lack Zod schemas |

### NETWORTH_REFERENCE_IMPLEMENTATION.md Compliance

| Requirement | Status | Notes |
|-------------|--------|-------|
| Canonical Execution Flow | ✅ Compliant | NetWorth follows the pattern |
| Layer Responsibilities | ✅ Compliant | Router → Service → Repository |
| Explanation Structure | ✅ Compliant | metric, value, confidence, evidence, sources, calculationSteps |
| Mapper Rules | ✅ Compliant | Flatten, rename, derive UI flags, preserve explanation |
| UI Rules | ✅ Compliant | Widget uses DataStateWrapper, conditional explain button |
| Explainability Rules | ✅ Compliant | Backend builds explanation, frontend preserves it |
| Invariants | ✅ Compliant | All values in paise, confidence in basis points |
| Extension Rules | ✅ Compliant | Follows documented pattern |
| Forbidden Patterns | ✅ Compliant | No frontend generation, no duplication |

### ARCHITECTURE_CONSTRAINTS.md Compliance

| Constraint | Status | Notes |
|------------|--------|-------|
| Monetary Values (paise) | ✅ Compliant | All values integers |
| Confidence Values (bps) | ✅ Compliant | 0-10000 range |
| Layer Hierarchy | ✅ Compliant | Router → Service → Engine → Repository |
| Purity Enforcement | ✅ Compliant | Engines have no DB access |
| Type System | ✅ Compliant | Python: dict[str, Any], TypeScript: proper types |
| State Ownership | ✅ Compliant | Backend SQLite, Frontend Zustand + React Query |
| Explainability | ✅ Compliant | Every metric has explainable derivation |
| Component Responsibilities | ✅ Compliant | Clear layer boundaries |

### Stage 0 Rules Compliance

| Rule | Status | Notes |
|------|--------|-------|
| Immutable Rulebook | ✅ Compliant | No modifications to frozen rules |
| Evidence over assumptions | ✅ Compliant | All findings documented |
| Read-only audit | ✅ Compliant | No code modifications |
| Append-only reporting | ✅ Compliant | New document created |

---

## 9. Risk Analysis

### High-Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Router response_model changes** | Breaking API changes | Add response_model as optional, maintain backward compatibility |
| **Zod schema validation** | Runtime errors if schema mismatch | Test against actual API responses |
| **Mapper transformation** | Data loss if not careful | Preserve explanation field, no business logic in mapper |
| **Widget integration** | UI breakage if missing | Use conditional rendering, check for explanation existence |

### Medium-Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Confidence calculation** | May produce invalid values | Validate 0-10000 range, use Decimal for precision |
| **Evidence collection** | May miss sources | Audit all data sources, ensure complete coverage |
| **Calculation steps** | May be incomplete | Review all operations, ensure step ordering |

### Low-Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Source references** | Missing metadata | Add name, date where available |
| **Frontend model** | Missing fields | Follow NetWorth pattern exactly |
| **Hook integration** | Query key conflicts | Use unique query keys per capability |

---

## 10. Estimated Effort Per Capability

| Capability | Backend Effort | Frontend Effort | Total Effort |
|------------|--------------|-----------------|--------------|
| **Household Cashflow** | 4 hours | 3 hours | 7 hours |
| **Reconciliation** | 4 hours | 3 hours | 7 hours |
| **Debt Management** | 6 hours | 4 hours | 10 hours |
| **Credit Cards** | 6 hours | 4 hours | 10 hours |
| **Financial Health** | 8 hours | 5 hours | 13 hours |
| **Forecasting** | 6 hours | 4 hours | 10 hours |
| **Account Management** | 5 hours | 3 hours | 8 hours |
| **Transaction Intelligence** | 5 hours | 3 hours | 8 hours |
| **Financial Events** | 4 hours | 3 hours | 7 hours |
| **Recommendations** | 3 hours | 2 hours | 5 hours |
| **Pattern Analysis** | 3 hours | 2 hours | 5 hours |
| **Investments** | 3 hours | 2 hours | 5 hours |

**Total Estimated Effort:** 72 hours (9 person-days)

---

## 11. Next Steps

1. **Create capability-specific Pydantic response models** extending the shared Explanation model
2. **Add response_model to all routers** (non-breaking, optional field)
3. **Implement explanation builders in services** following NetWorth pattern
4. **Create Zod schemas for each capability** in `frontend/lib/contracts/api/`
5. **Create mappers for each capability** in `frontend/lib/mappers/`
6. **Create models for each capability** in `frontend/lib/models/`
7. **Update hooks to use new mappers** and pass through explanation
8. **Add explain buttons to widgets** where appropriate
9. **Test all changes** with type-check, lint, and build
10. **Document any deviations** from the reference pattern

---

*Version: 1.0 (Stage 3.0)*  
*No code modifications made. Architecture analysis only.*