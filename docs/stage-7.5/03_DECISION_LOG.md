# Decision Log - Stage 7.5

## Overview

This document records key architectural and UX decisions made during Stages 0-7 that define the ClariFin_OS experience. These decisions are locked and should not be revisited without explicit approval.

---

## Runtime Architecture Decisions

### DECISION-001: Graph-First Data Model
**Date**: Stage 4B
**Decision**: All financial data is unified through a graph model with nodes and edges.
**Rationale**: Enables cross-workspace queries, money flow tracing, and explainability.
**Impact**: Every workspace must provide a ViewModel that can be converted to graph nodes/edges.
**Evidence**: `frontend/lib/graph/types.ts` defines NodeType and EdgeType enums.

### DECISION-002: Runtime Composition Pattern
**Date**: Stage 5
**Decision**: Command Center Runtime composes Financial Graph Runtime, not inherits.
**Rationale**: Allows independent evolution of graph and command center concerns.
**Impact**: Command Center delegates all graph operations to FinancialGraphRuntime.
**Evidence**: `frontend/lib/command-center/runtime.ts` imports and wraps FinancialGraphRuntime.

### DECISION-003: Intelligence as Graph Consumer
**Date**: Stage 6
**Decision**: Intelligence Runtime consumes graph data, not raw API data.
**Rationale**: Ensures consistent data model across all intelligence engines.
**Impact**: All intelligence engines receive `IntelligenceContext` with graph nodes/edges.
**Evidence**: `frontend/lib/intelligence/runtime.ts` compute() method takes IntelligenceContext.

### DECISION-004: Simulation as Graph Consumer
**Date**: Stage 7
**Decision**: Simulation Runtime consumes graph data for projections.
**Rationale**: Projections are derived from actual financial state, not separate models.
**Impact**: All simulators receive `SimulationContext` with graph nodes/edges.
**Evidence**: `frontend/lib/simulation/runtime.ts` compute() method takes SimulationContext.

---

## Financial Correctness Decisions

### DECISION-005: Paise as Canonical Currency Unit
**Date**: Stage 2A
**Decision**: All monetary values stored as integers in paise (₹1.00 = 100 paise).
**Rationale**: Eliminates floating-point precision errors in financial calculations.
**Impact**: All APIs, repositories, and UI components use `amount_paise` (integer).
**Evidence**: 
- `backend/src/db.py` - `amount_paise INTEGER NOT NULL DEFAULT 0`
- `frontend/lib/utils/format.ts` - `formatINR()` converts paise to rupees for display

### DECISION-006: Basis Points for Scores
**Date**: Stage 6
**Decision**: All scores stored as integers in basis points (0-10000 = 0-100%).
**Rationale**: Consistent precision for all percentage-based metrics.
**Impact**: All score fields use `score_bps` or `confidence` (0-100 scale).
**Evidence**: `frontend/lib/intelligence/types.ts` - scores in basis points.

### DECISION-007: No ML/LLM for Predictions
**Date**: Stage 7
**Decision**: All projections use deterministic algorithms, no machine learning.
**Rationale**: Ensures reproducibility and auditability of all financial projections.
**Impact**: Simulation engines use historical averages and fixed assumptions.
**Evidence**: Stage 7 activeContext.md - "No ML, LLMs, or probabilistic forecasting"

### DECISION-008: Transaction Immutability
**Date**: Stage 2A.1
**Decision**: Transactions are immutable via SQL triggers.
**Rationale**: Ensures ledger integrity and audit trail.
**Impact**: UPDATE/DELETE on transactions raises IntegrityError.
**Evidence**: `backend/src/engines/ledger_audit_engine.py` - immutability triggers.

---

## Workspace Architecture Decisions

### DECISION-009: Workspace Page Pattern
**Date**: Stage 3
**Decision**: Each workspace uses a `workspace-page.tsx` pattern with capability hooks.
**Rationale**: Consistent state management and data flow across workspaces.
**Impact**: All workspaces follow: Page → Capability Hook → Components.
**Evidence**: 
- `frontend/app/transactions/workspace-page.tsx`
- `frontend/lib/capabilities/use-transaction-capability.ts`

### DECISION-010: Evidence Drawer Pattern
**Date**: Stage 3
**Decision**: Evidence drawers are available in all intelligence workspaces.
**Rationale**: Users can trace any number back to its source.
**Impact**: `EvidenceDrawer` component reused across transactions, cashflow, net-worth, behaviour, forecast.
**Evidence**: Component reuse matrix in 01_EXPERIENCE_SPEC.md.

### DECISION-011: Toolbar Standardization
**Date**: Stage 3
**Decision**: All intelligence workspaces use a standardized toolbar.
**Rationale**: Consistent user experience for common actions.
**Impact**: `WorkspaceToolbar` component with refresh, export, search, filter controls.
**Evidence**: `frontend/components/toolbar/workspace-toolbar.tsx`.

### DECISION-012: Loading/Error/Empty State Components
**Date**: Stage 3
**Decision**: Each workspace has dedicated loading, error, and empty state components.
**Rationale**: Better UX than generic states.
**Impact**: Per-workspace skeleton and error components.
**Evidence**: `frontend/components/*/loading-skeleton.tsx`, `error-state.tsx`, `empty-state.tsx`.

---

## Navigation Decisions

### DECISION-013: Sidebar Navigation Structure
**Date**: Stage 3
**Decision**: Two-section navigation: Overview and Manage.
**Rationale**: Clear separation between summary and management views.
**Impact**: 
- Overview: Dashboard only
- Manage: Transactions, Accounts, Credit Cards
**Evidence**: `frontend/lib/config/navigation.ts` - CORE_NAV_SECTIONS.

### DECISION-014: Route Redirects for Legacy Paths
**Date**: Stage 3
**Decision**: Deprecated routes redirect to new locations.
**Rationale**: Prevents 404 errors during navigation.
**Impact**: `ROUTE_REDIRECTS` mapping in navigation config.
**Evidence**: `frontend/lib/config/navigation.ts` - ROUTE_REDIRECTS.

### DECISION-015: No Top-Level Navigation for Intelligence Workspaces
**Date**: Stage 4-7
**Decision**: Net Worth, Cashflow, Behaviour, Forecast, Reconciliation accessible via Command Center only.
**Rationale**: These are analysis tools, not primary management views.
**Impact**: Not in sidebar; accessed via Command Center or direct URL.
**Evidence**: Navigation config only includes dashboard, transactions, accounts, cards.

---

## Component Architecture Decisions

### DECISION-016: Error Boundary Isolation
**Date**: Stage 3
**Decision**: Each major component wrapped in error boundary.
**Rationale**: Prevents total page failure from single component error.
**Impact**: `ErrorBoundary` component used in dashboard and other pages.
**Evidence**: `frontend/app/dashboard/page.tsx` - multiple ErrorBoundary wrappers.

### DECISION-017: React.memo for Performance
**Date**: Stage 3
**Decision**: Workspace pages use React.memo for re-render optimization.
**Rationale**: Large transaction lists cause performance issues.
**Impact**: `memo(TransactionWorkspacePageComponent)` pattern.
**Evidence**: `frontend/app/transactions/workspace-page.tsx`.

### DECISION-018: Zustand for Client State
**Date**: Stage 3
**Decision**: Use Zustand for UI state (sidebar, selections, preferences).
**Rationale**: Simpler than Redux, good TypeScript support.
**Impact**: `use-app-store` for global UI state.
**Evidence**: `frontend/lib/store/use-app-store.ts`.

### DECISION-019: React Query for Server State
**Date**: Stage 3
**Decision**: Use React Query (TanStack Query) for API data.
**Rationale**: Built-in caching, background refresh, error retry.
**Impact**: All `use*` hooks return React Query results.
**Evidence**: `frontend/lib/hooks/use-accounts.ts` - useQuery, useMutation.

---

## Backend Architecture Decisions

### DECISION-020: Repository Pattern
**Date**: Stage 2
**Decision**: All database access through repository classes.
**Rationale**: Clean separation between data access and business logic.
**Impact**: Repositories in `src/repositories/`, services in `src/services/`.
**Evidence**: `backend/src/repositories/transaction_repository.py`.

### DECISION-021: FinanceDB Schema Management Only
**Date**: Stage 4
**Decision**: FinanceDB class handles schema/migrations only, not queries.
**Rationale**: Repositories handle domain queries, FinanceDB handles infrastructure.
**Impact**: `get_db()` deprecated; repositories instantiated directly.
**Evidence**: `backend/src/common/database.py` - "DEPRECATED: Returns a FinanceDB instance."

### DECISION-022: Service Layer Orchestration
**Date**: Stage 2
**Decision**: Services orchestrate multiple repositories for business operations.
**Rationale**: Avoids N+1 queries in API handlers.
**Impact**: API handlers call services, not repositories directly.
**Evidence**: `backend/src/services/dashboard_service.py` - orchestrates TransactionRepository, ReconciliationRepository.

---

## Data Flow Decisions

### DECISION-023: API Response Validation
**Date**: Stage 3
**Decision**: All API responses validated with Zod before use.
**Rationale**: Prevents runtime errors from shape mismatches.
**Impact**: `safeParse()` used in all hooks; errors logged to console.
**Evidence**: `frontend/lib/hooks/use-accounts.ts` - AccountsResponseSchema.safeParse.

### DECISION-024: Evidence Chain in All Insights
**Date**: Stage 6
**Decision**: Every insight must include evidence chain.
**Rationale**: Users can verify any claim made by the system.
**Impact**: `EvidenceChain` required in Insight, Alert, Recommendation types.
**Evidence**: `frontend/lib/intelligence/types.ts` - EvidenceChain interface.

### DECISION-025: Related Nodes for Cross-Reference
**Date**: Stage 4
**Decision**: All insights include related graph node IDs.
**Rationale**: Enables navigation from insight to source data.
**Impact**: `related_nodes: string[]` in all output types.
**Evidence**: `frontend/lib/intelligence/types.ts` - related_nodes field.

---

## UI/UX Decisions

### DECISION-026: Dark Mode Default
**Date**: Stage 3
**Decision**: Dark mode is the default theme.
**Rationale**: Modern financial app aesthetic, reduces eye strain.
**Impact**: `defaultTheme="dark"` in ThemeProvider.
**Evidence**: `frontend/app/layout.tsx`.

### DECISION-027: Mobile-First Responsive
**Date**: Stage 3
**Decision**: All layouts designed mobile-first, then enhanced for desktop.
**Rationale**: Mobile usage is primary for many users.
**Impact**: `grid-cols-1` as base, `lg:grid-cols-*` for desktop.
**Evidence**: All page components use responsive grid classes.

### DECISION-028: Keyboard Navigation Support
**Date**: Stage 3
**Decision**: Transaction workspace supports keyboard shortcuts.
**Rationale**: Power users need efficient navigation.
**Impact**: `keydown` event listener in workspace page.
**Evidence**: `frontend/app/transactions/workspace-page.tsx` - handleKeyDown.

---

## Integration Decisions

### DECISION-029: Command Center as Graph Hub
**Date**: Stage 5
**Decision**: Command Center builds graph from all workspace ViewModels.
**Rationale**: Single source of truth for cross-workspace analysis.
**Impact**: Command Center page fetches all workspace data and builds graph.
**Evidence**: `frontend/app/command-center/page.tsx` - builds viewModels from all hooks.

### DECISION-030: Cross-Workspace Navigation
**Date**: Stage 4-7
**Decision**: Each intelligence workspace includes cross-navigation component.
**Rationale**: Users can jump from insight to related workspace.
**Impact**: `CrossNavigation` component in workspace pages.
**Evidence**: `frontend/app/behaviour/workspace-page.tsx` - CrossNavigation component.

---

## Future Considerations (Locked)

### FC-001: Forecast Workspace Page
**Status**: Not in navigation; accessible via direct URL or Command Center.
**Reason**: Forecast is analysis tool, not primary management view.
**Future**: May add to navigation if user feedback indicates need.

### FC-002: Net Worth/Cashflow/Behaviour in Navigation
**Status**: Not in sidebar.
**Reason**: These are derived views, accessed through Command Center.
**Future**: May add as sub-items under Overview if needed.

### FC-003: Additional Simulation Engines
**Status**: 8 engines implemented (cashflow, net_worth, loan, investment, retirement, goal, budget, emergency_fund).
**Reason**: Covers core financial projection needs.
**Future**: May add more engines based on user demand.

---

## Decision Authority

All decisions in this document are:
- Based on implemented code in Stages 0-7
- Reflected in the current codebase
- Should not be changed without explicit approval
- Guide implementation for Stages 8-10