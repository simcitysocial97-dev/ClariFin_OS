# Active Context

## Current Sprint: Stage 1.12 — Architecture Freeze & Verification

### Completed
- Built reusable ExplainabilityDrawer UI runtime consuming Explanation objects
- Created 9 components: ExplainabilityDrawer, Overview/Evidence/Calculation/Sources panels
- Implemented EvidenceCard, ConfidenceBadge, CalculationStepCard, SourceCard
- Created ExplainabilityProvider with Zustand store for global state management
- Integrated drawer into NetWorth widget as reference implementation
- Updated SourceReference contract to canonical provenance model

### Recently Completed: Stage 1.8 — Chart Runtime Extraction
- Created shared chart modules: `lib/chart/recharts.ts`, `chart-config.ts`, `chart-colors.ts`
- Migrated CashflowChart to use shared chart runtime
- Fixed `formatINRCompact()` precision and updated tests
- All validation passing: type-check ✓, tests (94/94) ✓, build ✓

### Recently Completed: Stage 1.10 — Accounts Capability Migration
- Created canonical capability structure: `lib/capabilities/accounts/`
- Migrated useManagedAccounts to use useAppQuery with shared query keys
- Created contracts/api.ts, models/model.ts, mappers/mapper.ts, services/api.ts, hooks/useAccounts.ts, index.ts
- Updated page component to use AccountModel with camelCase fields
- Kept old hook as compatibility shim for backward compatibility
- All validation passing: type-check ✓, tests (94/94) ✓, build ✓

### Completed: Stage 1.12 — Architecture Verification
- Verified backend layer boundaries: Router → Service → Engine → Repository → SQLite
- Verified FinanceDB import boundary: Only in repositories/
- Verified frontend capability pattern: Accounts, Cashflow follow contracts→services→mappers→models→hooks
- Created `docs/COMPATIBILITY_LAYERS.md` cataloging all compatibility shims
- Created `docs/TECHNICAL_DEBT.md` with 6 entries (TD-001 to TD-006)
- Updated `ARCHITECTURE.md` with runtime layers documentation
- Frontend validation: type-check ✓, tests (94/94) ✓, build ✓
- Backend validation: ruff (160 pre-existing style issues), mypy (pre-existing test issues), pytest (1184 passed, 15 pre-existing failures)

### Next Steps
- Stage 1 complete. Ready for Stage 2.
- Address technical debt items in Stage 2.0:
  - Remove duplicate behavior/behaviour modules
  - Migrate remaining frontend hooks to capability pattern
  - Refactor legacy engine DB access (optional)