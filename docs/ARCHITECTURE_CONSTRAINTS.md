# Architecture Constraints — ClariFin_OS

> **Immutable Rulebook** — Every future implementation must obey these constraints.  
> This is NOT an implementation guide or design document.

---

## 1. Financial Truth

### Monetary Values
- **All currency values are integers representing paise** (₹1.00 = 100 paise)
- NEVER use `float` or `double` for currency calculations
- Use `_parse_amount_paise()` for safe string-to-paise conversion
- Division operations MUST use `decimal.Decimal` with explicit rounding
- All monetary outputs are integers; fractions default to 0

### Confidence Values
- All confidence values are integers in **basis points** (0-10000 = 0-100%)
- Confidence range MUST be enforced: 0 ≤ value ≤ 10000
- Decimal precision MUST be preserved in calculations

### Financial Identities
- `income_paise - expense_paise = surplus_paise` (mathematical identity preserved)
- Loan principal monotonically decreases during repayment
- Final loan balance equals 0 in healthy loans
- Credit utilization ratio in [0, 1] range

---

## 2. Data Flow

### Layer Hierarchy (Router → Service → Engine → Repository → SQLite)
```
Router (HTTP) ─→ Service (orchestration) ─→ Engine (pure logic) ─→ Repository (SQL) ─→ SQLite
```

### Data Flow Rules
- **Routers** validate HTTP parameters only, NOT business logic
- **Services** orchestrate business logic, delegating to engines
- **Engines** are pure computation — NO database access, NO side effects
- **Repositories** are the ONLY layer that may import `FinanceDB`
- Data flows downward (parameters); results flow upward (returns)

### Purity Enforcement
- Engines accepting data via parameters (list[dict]), NOT db_path
- If `sqlite3.connect()` found in engines, refactor immediately (AR-1 violation)
- Legacy impure engines (balance_engine.py, ledger_audit_engine.py) are exceptions for audit purposes

---

## 3. Type System

### Python (Backend)
- Type hints: `dict[str, Any]` NOT `Dict[str, Any]`
- All monetary inputs/outputs: `int` (paise)
- All confidence values: `int` (basis points)
- Never use `Optional[T]` for critical monetary fields — default to 0

### TypeScript (Frontend)
- NO `as any`, `@ts-ignore`, or `@ts-nocheck`
- All currency displays convert paise → rupees (divide by 100)
- NEVER use `parseFloat()` or `Number()` for currency display
- Use integer arithmetic for all conversions

### OpenAPI Contract
- Types generated from `http://localhost:8000/openapi.json`
- Frontend types MUST match backend contract exactly
- API changes require integration test validation

---

## 4. State Ownership

### Backend
- **Single source of truth**: SQLite database via `FinanceDB` class
- All state mutations go through repository layer
- Immutable transactions enforced via database triggers (no UPDATE/DELETE)

### Frontend
- **Zustand** for global state (accounts, transactions, preferences)
- **TanStack React Query** for server state (API calls, caching)
- **Local state** for ephemeral UI state (form inputs, modals)

### State Boundaries
- Frontend NEVER mutates backend state directly
- All state changes flow through API endpoints
- Each layer owns exactly one concern (UI, server state, domain logic, persistence)

---

## 5. Explainability

### Calculation Transparency
- Every financial metric MUST have an explainable derivation
- Engine outputs include contributing factors where applicable
- LLM explanations MUST trace back to deterministic data (never used for calculations)
- Cache explanations to prevent drift

### Audit Trail
- Reconciliation audit log captures all match actions
- Financial event lifecycle log tracks state transitions
- Score changes MUST be attributable to input changes
- User-facing recommendations include confidence scores

---

## 6. Component Responsibilities

### Backend Layers
| Layer | Responsibility | Forbidden Actions |
|-------|---------------|-------------------|
| Router | HTTP validation, serialization | Business logic, direct DB access |
| Service | Orchestrate engines/repositories | Direct DB access (except via repos) |
| Engine | Pure computation | Database imports, side effects |
| Repository | SQL access via `BaseRepository` | Direct sqlite3 usage (must extend BaseRepository) |
| Model | Domain data structures | Database logic, computations |

### Frontend Layers
| Layer | Responsibility |
|-------|---------------|
| Components | Presentation + user interaction |
| Hooks | Data fetching + business logic |
| Stores (Zustand) | Global application state |
| Lib | Shared utilities + parsers |

---

## 7. Testing Philosophy

### Determinism First
- Every test MUST be repeatable with same inputs
- Tests run in parallel with isolated state
- Property tests use Hypothesis with profiles (fast/normal/deep)

### Golden Master Validation
- All financial formulas validated against known calculators
- EMI formulas verified against Excel/bank calculators
- Edge cases tested: negative amortization, rounding, large numbers

### Test Categories
| Category | Target Coverage | Tools |
|----------|---------------|-------|
| Engines | 90%+ | pytest (pure functions) |
| Models | 95%+ | pytest (dataclasses) |
| API Layer | 80%+ | pytest (integration) |
| Frontend | Component + hook coverage | Vitest + Playwright |

### Invariants Testing
- All monetary invariants in `tests/domain/invariants/money.py`
- All confidence invariants in `tests/domain/invariants/forecast.py`
- All cashflow invariants in `tests/domain/invariants/cashflow.py`
- All loan invariants in `tests/domain/invariants/loan.py`

---

## 8. AI Coding Constraints

### Repository Boundary Rule (MANDATORY)
- ONLY files under `src/repositories/` may import `FinanceDB`
- Routers MUST NOT import `FinanceDB` or `get_db()`
- Engines MUST NOT import `FinanceDB` — violates layer purity
- Refactor immediately if boundary violation detected

### Next.js Conventions
- Prepend `'use client'` ONLY for components with state/hooks
- Default to Server Components (lean, no client JS)
- Dynamic routing: `app/reconciliation/[id]/page.tsx`

### Code Safety
- NEVER drop database tables — use `ADD COLUMN IF NOT EXISTS`
- NEVER use TypeScript escape hatches (`as any`, `@ts-ignore`)
- NEVER use float for currency — integers (paise) only
- Never allow silent auto-balancing — mismatches require explicit user confirmation

### Verification Protocol
After ANY file modification:
1. Frontend: `npm run type-check && npm run lint && npm test -- --run && npm run build`
2. Backend: `./venv/bin/python3 -m ruff check . && ./venv/bin/python3 -m mypy .`

---

## 9. Conflict Resolution

### Existing Documentation Conflicts
| Constraint | Conflict | Resolution |
|-----------|----------|------------|
| Repository boundary | BALANCE/LEDGER engines have direct sqlite3 access | Acceptable for audit tools; refactor other engines |
| Float usage | Some interest_rate columns stored as REAL | Future migrations: use integer basis points |
| Duplicate code | `behavior`/`behaviour` modules coexist | Canonical: `behaviour_*`; legacy marked DEPRECATED |

### Deprecated Systems
- `engines/behavior_engine.py` → DEPRECATED, use `engines/behaviour_engine/`
- `routers/behavior.py` → legacy wrapper, consolidate to `behaviour.py`
- `services/behavior_service.py` → deprecated wrapper, use `BehaviourService`

---

## 10. Living Document Protocol

This document is updated ONLY when:
- Financial truth rules change (new invariant discovered)
- Layer boundaries shift (new layer added, responsibility redefined)
- Monetary convention changes (currency, precision)
- Type system evolves (new Python/TypeScript versions)
- Testing philosophy shifts (new framework, approach)

**Trigger-based updates prevent unnecessary churn while maintaining authority.**