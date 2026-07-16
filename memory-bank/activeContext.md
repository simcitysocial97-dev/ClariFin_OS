# Active Context

## Architecture Constraints Document (Completed)

### Changes Made (July 16, 2026)
- Created `docs/ARCHITECTURE_CONSTRAINTS.md` — immutable rulebook for all future implementations
- Documented 8 core constraint areas: Financial Truth, Data Flow, Type System, State Ownership, Explainability, Component Responsibilities, Testing Philosophy, AI Coding Constraints
- Added conflict resolution section for `behavior`/`behaviour` duplicates and engine purity issues
- Branch `stage-0-constraints-guardrails` created and pushed to origin

### Next Steps
- Proceed to S0.2 — Implement constraint validation rules
- Update ARCHITECTURE.md layer counts (new widgets created)

### OpenAPI Schema Exported (July 2026)
- Exported complete OpenAPI schema to `backend/clarifin_openapi.json`
- Contains 105 unique paths with 126 total endpoints
- All 22 routers included (accounts, audit, banks, behavior, behaviour, cards_statements, cashflow, credit_cards, dashboard, export, financial_intelligence, goals, health, import, investments, loans, managed_accounts, members, networth, optimization, patterns, reconciliation, scenarios, transactions)
- File size: 235 KB (7941 lines)
- Generated TypeScript types: `backend/api_types.ts` (7331 lines)
- Created `backend/CAPABILITY_INVENTORY.md` with domain-organized endpoints (159 lines)