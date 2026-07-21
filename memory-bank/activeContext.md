# Active Context

## Stage 8E-C2 Production Visual System Migration - COMPLETE

### Workspace Inventory (Locked Scope - 10 Workspaces)
Per user correction: **Rules workspace is NOT part of this migration**

1. `/app/transactions/workspace-page.tsx` - Investigation Table Surface
2. `/app/accounts/page.tsx` - Relationship Explorer Surface
3. `/app/net-worth/page.tsx` - Graph Surface
4. `/app/cashflow/page.tsx` - Sankey Surface
5. `/app/investments/page.tsx` - Portfolio Explorer Surface
6. `/app/loans/page.tsx` - Amortization Surface
7. `/app/behaviour/workspace-page.tsx` - Timeline Surface
8. `/app/forecast/workspace-page.tsx` - Simulation Surface
9. `/app/reconciliation/page.tsx` - Table Surface
10. `/app/settings/page.tsx` - Configuration Surface

**Note:** `/app/dashboard/page.tsx` and `/app/cards/page.tsx` are auxiliary pages, not in the locked scope.

### Runtime Integration Status
- ✅ SelectionRuntime: Integrated via shell (RightInspector, BottomTimeline)
- ✅ NavigationRuntime: Integrated via shell (LeftRail, TopCommandBar)
- ✅ ExplainabilityRuntime: Integrated via shell (RightInspector)
- ✅ TimelineRuntime: Integrated via shell (BottomTimeline)
- ✅ CommandCenterRuntime: Composes all runtimes

### Changes Made (This Session)
- Corrected workspace inventory to match locked scope (10 workspaces, no Rules)
- Removed unused `commandCenterRuntime` import from transaction-table.tsx
- Updated net-worth-summary.tsx to use Surface instead of Card
- Updated cashflow-summary.tsx to use Surface instead of Card
- Updated settings/page.tsx to use semantic CSS variables

### Components Updated
- `components/transaction-table/transaction-table.tsx` - Removed unused import
- `components/net-worth/net-worth-summary.tsx` - Uses Surface primitive
- `components/cashflow/cashflow-summary.tsx` - Uses Surface primitive
- `app/settings/page.tsx` - Uses semantic CSS variables

### Architecture
```
Top Command Bar (global)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                     Workspace Content                      │
│                                                          │
├──────────────────────────────────────────────────────────┤
│ Right Inspector (global)                                   │
└──────────────────────────────────────────────────────────┘
Bottom Timeline (global)
```

### Verification
- ✅ TypeScript check passed with **zero errors**
- ✅ Ruff check passed with **all checks passed**
- No duplicated shell UI
- No duplicated runtime state
- No new infrastructure
- No business logic changes

### Notes
- Child components (net-worth/*.tsx, cashflow/*.tsx) still use Card - this is intentional per correction #2
- These are business components composed within the Surface/Panel structure
- No keyboard hooks added to workspaces - per correction #3, OS owns keyboard