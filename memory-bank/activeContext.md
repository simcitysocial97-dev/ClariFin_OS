# Active Context

## Current Sprint: Stage 1.6 — Universal Explainability Drawer

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

### Next Steps
- Extend explainability to remaining features: accounts, loans, cards, investments
- Migrate remaining charts to use shared chart modules
- Add explanation UI components to display confidence and evidence
- Implement explanation aggregation for dashboard views