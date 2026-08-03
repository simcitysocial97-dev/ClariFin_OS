# Frontend Runtime Map

**Generated:** 2026-08-03  
**Scope:** `frontend/lib/runtime/` — Program B Runtime Consolidation  
**Root Provider:** `<RuntimeProvider>` in `app/layout.tsx`

---

## Runtime Overview

```
RuntimeProvider (root)
    │
    ├── workspaceRuntime   — current workspace, title, breadcrumbs, filters
    ├── selectionRuntime   — active entity (transaction/loan/card/investment/account/reconciliation)
    ├── timelineRuntime    — current date position, granularity, comparison period
    └── navigationRuntime  — history stack, back/forward, deep links
```

All 13 pages call `useWorkspaceRegistration()` to register themselves with `workspaceRuntime` and `navigationRuntime`.  
No data fetching moves into the runtime — capabilities remain unchanged.

---

## Runtime Modules

| Module | File | Owner | State | Consumers | Mutations |
|---|---|---|---|---|---|
| Workspace | `workspace-runtime.ts` | Current workspace, title, breadcrumbs, dateRange, member, filters | 12 pages + command-center | `setTitle`, `setBreadcrumbs`, `navigateTo`, `setDateRange`, `setMember`, `setFilters`, `registerWorkspace` |
| Selection | `selection-runtime.ts` | Active entity, multi-select set, history stack | Pages via `useSelection()` | `selectEntity`, `toggleMulti`, `clearSelection`, `clearMultiSelection` |
| Timeline | `timeline-runtime.ts` | Date position, granularity (month/quarter/year), comparisonPeriod | Pages + bottom-timeline component | `setPosition`, `setGranularity`, `setComparisonPeriod` |
| Navigation | `navigation-runtime.ts` | History entries, currentIndex, canGoBack/canGoForward | CommandCenter, back-button UI | `pushPath`, `goBack`, `goForward`, `clearHistory` |
| Provider | `runtime-provider.tsx` | Composition of all 4 runtimes into React Context | All pages via `useRuntime()` | None (read-only context) |
| Registration Hook | `use-workspace-registration.ts` | Declarative workspace declaration inside page components | All workspace pages | Called once per page during render |
| Types | `runtime-types.ts` | WorkspaceName, SurfaceType, WorkspaceConfig, WorkspaceState, SelectionEntity, SelectionState, TimeGranularity, TimelinePosition, NavigationEntry, NavigationState, RuntimeState | All modules | Type-only — no mutations |

---

## Page → Runtime Chain

| Page | Capability Hook | Workspace Registration | Selection | Timeline | Navigation |
|---|---|---|---|---|---|
| Dashboard | `useDashboardMetrics` (direct) | N/A (no registration — composite) | — | — | `pushPath('/dashboard')` |
| Accounts | `useAccountsCapability` | `useWorkspaceRegistration({name:'accounts'})` | — | — | `pushPath('/accounts')` |
| Transactions | `useTransactionCapability` | `useWorkspaceRegistration({name:'transactions'})` | `selection.selectEntity` | — | `pushPath('/transactions')` |
| Cashflow | `useCashflowCapability` | `useWorkspaceRegistration({name:'cashflow'})` | — | — | `pushPath('/cashflow')` |
| Cards | `useCreditCardsCapability` | `useWorkspaceRegistration({name:'cards'})` | — | — | `pushPath('/cards')` |
| Loans | `useLoansCapability` | `useWorkspaceRegistration({name:'loans'})` | — | — | `pushPath('/loans')` |
| Investments | `useInvestmentsCapability` | `useWorkspaceRegistration({name:'investments'})` | — | — | `pushPath('/investments')` |
| Net Worth | `useNetWorthCapability` | `useWorkspaceRegistration({name:'net-worth'})` | — | — | `pushPath('/net-worth')` |
| Behaviour | `useBehaviourCapability` | `useWorkspaceRegistration({name:'behaviour'})` | — | — | `pushPath('/behaviour')` |
| Forecast | `useForecastCapability` | `useWorkspaceRegistration({name:'forecast'})` | — | — | `pushPath('/forecast')` |
| Reconciliation | `useReconciliationCapability` | `useWorkspaceRegistration({name:'reconciliation'})` | — | — | `pushPath('/reconciliation')` |
| Command Center | Multi-hook composite | `pushPath('/command-center')` | — | — | — |
| Settings | `useAppStore` + `useTheme` | `useWorkspaceRegistration({name:'settings'})` | — | — | `pushPath('/settings')` |

---

## Consumer Breakdown

### Pages (read-only runtime consumption)
None of the 13 pages currently read from `selectionRuntime`, `timelineRuntime`, or `navigationRuntime`.  
They only write via `useWorkspaceRegistration()`. Future programs will wire these.

### Components (read runtime state)
| Component | Reads From | Purpose |
|---|---|---|
| `top-command-bar.tsx` | `workspaceRuntime.state.current` | Shows current workspace name in header |
| `bottom-timeline.tsx` | `timelineRuntime.state` | Renders timeline scrubber at bottom |
| `right-inspector.tsx` | `selectionRuntime.state.active` | Shows selected entity details |
| `command-center/page.tsx` | `navigationRuntime.pushPath` | Logs navigation entry on mount |

### Shell (composition)
| Component | Wraps | Purpose |
|---|---|---|
| `RuntimeProvider` | Entire app (via `layout.tsx`) | Provides all 4 runtimes via React Context |
| `ShellProvider` | AppShell (via `layout.tsx`) | Existing OS shell — remains untouched |

---

## API Surface

### useWorkspaceRuntime()
```ts
{
  state: WorkspaceState      // current, breadcrumbs, title, dateRange, member, filters
  navigateTo(name, title?, crumbs?)
  setTitle(title)
  setBreadcrumbs(crumbs)
  setDateRange(from?, to?)
  setMember(member)
  setFilters(filters)
  registerWorkspace(config)
  getWorkspaceConfig(name)
  subscribe(fn) → unsubscribe
}
```

### useSelectionRuntime()
```ts
{
  state: SelectionState      // active, multi, history
  selectEntity(entity)
  toggleMulti(id, selected)
  clearSelection()
  clearMultiSelection()
  subscribe(fn) → unsubscribe
}
```

### useTimelineRuntime()
```ts
{
  state: TimelinePosition    // date, granularity, comparisonPeriod
  setPosition(date)
  setGranularity(granularity)
  setComparisonPeriod(from?, to?)
  subscribe(fn) → unsubscribe
}
```

### useNavigationRuntime()
```ts
{
  state: NavigationState     // history, currentIndex
  pushPath(path, workspace?)
  goBack() → Entry | null
  goForward() → Entry | null
  current() → Entry | null
  canGoBack: boolean
  canGoForward: boolean
  clear()
  subscribe(fn) → unsubscribe
}
```

---

## Validation

| Check | Result |
|---|---|
| TypeScript compilation (`tsc --noEmit`) | ✅ PASS (0 errors) |
| Test suite (`vitest run`) | ✅ PASS (507 tests, 53 files) |
| Single RuntimeProvider at root | ✅ PASS — wrapped in `app/layout.tsx` |
| No duplicate providers | ✅ PASS — only one `RuntimeProvider` instance |
| No runtime cycles | ✅ PASS — flat module graph, no circular imports |
| Capability hooks unchanged | ✅ PASS — zero modifications to `lib/capabilities/*` |
| Mapper layer untouched | ✅ PASS — zero modifications to `lib/mappers/*` |
| DTO layer untouched | ✅ PASS — zero modifications to `types/*` |
| Pages use thin registration pattern | ✅ PASS — all 12 workspace pages call `useWorkspaceRegistration` |

---

## Files Created

| File | Lines | Purpose |
|---|---|---|
| `lib/runtime/runtime-types.ts` | 82 | All shared type definitions |
| `lib/runtime/workspace-runtime.ts` | 144 | Workspace state machine + React hook + singleton |
| `lib/runtime/selection-runtime.ts` | 114 | Selection state machine + React hook + singleton |
| `lib/runtime/timeline-runtime.ts` | 101 | Timeline state machine + React hook + singleton |
| `lib/runtime/navigation-runtime.ts` | 136 | Navigation history state machine + React hook + singleton |
| `lib/runtime/runtime-provider.tsx` | 68 | React Context provider composing all 4 runtimes |
| `lib/runtime/index.ts` | 46 | Barrel export for all runtime modules |
| `lib/runtime/use-workspace-registration.ts` | 53 | Declarative hook for page workspace declaration |

## Files Modified

| File | Change |
|---|---|
| `app/layout.tsx` | Added `<RuntimeProvider>` wrapping `<ErrorBoundary>` |
| `app/accounts/workspace-page.tsx` | Added `useWorkspaceRegistration()`, removed `useEffect` command-center registration |
| `app/accounts/page.tsx` | Thin wrapper → `accounts/workspace-page.tsx` |
| `app/transactions/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component, added `aria-label` for a11y |
| `app/transactions/page.tsx` | Thin wrapper → `transactions/workspace-page.tsx` |
| `app/cashflow/page.tsx` | Added `useWorkspaceRegistration()`, removed `useEffect` command-center registration |
| `app/cards/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/cards/page.tsx` | Thin wrapper → `cards/workspace-page.tsx` |
| `app/loans/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/loans/page.tsx` | Thin wrapper → `loans/workspace-page.tsx` |
| `app/investments/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/investments/page.tsx` | Thin wrapper → `investments/workspace-page.tsx` |
| `app/net-worth/page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/behaviour/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/forecast/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/reconciliation/workspace-page.tsx` | Added `useWorkspaceRegistration()` inside component function |
| `app/reconciliation/page.tsx` | Thin wrapper → `reconciliation/workspace-page.tsx` |
| `app/behaviour/page.tsx` | Thin wrapper → `behaviour/workspace-page.tsx` |
| `app/forecast/page.tsx` | Thin wrapper → `forecast/workspace-page.tsx` |
| `app/command-center/page.tsx` | Added `useNavigation()` hook |
| `app/settings/page.tsx` | Added `useWorkspaceRegistration()` inside component function |
