# CGC Optimization Report - frontend/lib/ Analysis

## Executive Summary

This report documents the CodeGraphContext (CGC) optimization analysis performed on the `/home/vasantha/AI-Projects/ClariFin_OS/frontend/lib/` directory.

## CGC Queries Performed

### Phase 1: File Discovery
| Query | Purpose | Result Count |
|-------|---------|--------------|
| `MATCH (f:File) WHERE f.path CONTAINS 'frontend/lib' RETURN f.path, f.name` | List all files in frontend/lib | 80 files |
| `MATCH (f:File) WHERE f.path CONTAINS 'frontend/lib' AND f.name = 'index.ts' RETURN f.path` | Find all index.ts barrel files | 7 files |
| `MATCH (f:File) WHERE f.path CONTAINS 'frontend/lib' AND f.name ENDS WITH '.tsx' RETURN f.path` | Find React components | 2 files |

### Phase 2: Function & Interface Discovery
| Query | Purpose | Result Count |
|-------|---------|--------------|
| `MATCH (f:Function) WHERE f.path CONTAINS 'frontend/lib' RETURN f.name, f.path` | List all functions | 175 functions |
| `MATCH (i:Interface) WHERE i.path CONTAINS 'frontend/lib' RETURN i.name, i.path` | List all interfaces | 20 interfaces |
| `MATCH (f:Function) WHERE f.path CONTAINS 'frontend/lib' AND f.name STARTS WITH 'use' RETURN f.name, f.path, f.source` | Find all React hooks | 30 hooks |

### Phase 3: Relationship Analysis
| Query | Purpose | Result Count |
|-------|---------|--------------|
| `MATCH (f:Function)-[:CALLS]->(c:Function) WHERE f.path CONTAINS 'frontend/lib' AND c.path CONTAINS 'frontend/lib' RETURN f.name, c.name` | Internal function calls | 9 relationships |
| `MATCH (f:Function)-[:CALLS]->(c:Function) WHERE c.name = 'useAppQuery' RETURN f.name, f.path, f.source` | Find callers of useAppQuery | 2 callers |
| `MATCH (i:Interface) WHERE i.name = 'RuntimeStateResult' RETURN i.name, i.path, i.source` | Get interface source | 1 interface with source |

### Phase 4: Symbol Lookup
| Query | Purpose | Result Count |
|-------|---------|--------------|
| `find_code("useReconciliations")` | Find specific hook | 1 function + 2 content matches |
| `find_code("useAppQuery")` | Find query hook | 1 function + 4 content matches |
| `find_code("RuntimeStateResult")` | Find interface | 1 interface with source |

## File Reads Performed

| File | Lines | Reason |
|------|-------|--------|
| `frontend/lib/query/index.ts` | 23 | Get exports (barrel file) |
| `frontend/lib/explainability/index.ts` | 48 | Get exports (barrel file) |
| `frontend/lib/runtime/index.ts` | 28 | Get exports (barrel file) |
| `frontend/lib/parser/index.ts` | 121 | Get exports and main entry point |
| `frontend/lib/capabilities/accounts/index.ts` | 18 | Get exports (barrel file) |

**Total file reads: 5** (all minimal targeted reads for barrel files)

## Grep Queries Performed

| Query | Purpose | Result |
|-------|---------|--------|
| None | CGC provided all needed information | N/A |

## Analysis Results

### 1. Module Relationships

**frontend/lib/ directory structure:**
```
frontend/lib/
├── api/                 - API client (client.ts)
├── capabilities/        - Feature modules
│   ├── accounts/        - Account management
│   └── cashflow/        - Cashflow analysis
├── chart/               - Chart utilities
├── config/              - Configuration
├── context/             - React context (member-context.tsx)
├── contracts/           - API contracts
├── explainability/      - Explanation system
├── hooks/               - React Query hooks
├── mappers/             - Data mappers
├── models/              - TypeScript models
├── money.ts             - Currency utilities
├── parser/              - PDF statement parser
├── query/               - React Query infrastructure
├── runtime/             - State management runtime
├── schemas/             - Zod schemas
├── store/               - Zustand stores
└── utils/               - Utility functions
```

### 2. Key Exports (from barrel files)

**query/index.ts exports:**
- `queryKeys`, `QueryKey` (types)
- `STALE_TIME`, `RETRY_POLICY`, `baseQueryOptions`, `baseMutationOptions`, `defaultRetryDelay`
- `useAppQuery`, `normalizeError`, `AppError`, `AppQueryOptions`
- `useAppMutation`, `AppMutationOptions`

**explainability/index.ts exports:**
- Types: `SourceType`, `SourceReference`, `Evidence`, `Confidence`, `Explanation`, etc.
- Functions: `createExplanation`, `mergeEvidence`, `sortEvidence`, `confidenceToBadge`, `groupEvidence`, `flattenExplanation`
- Hooks: `useExplainability`, `useExplainabilityCollection`, `useRecommendationExplanation`

**runtime/index.ts exports:**
- Types: `RuntimeState`, `RuntimeStateResult`, `StateConfig`
- Functions: `createLoading`, `createSuccess`, `createEmpty`, `createError`, `createOffline`, `createPermission`, `createStale`, `isTerminalState`, `isLoadingState`, `hasDataState`
- Registry: `stateRegistry`, `getStateConfig`, `getStateIcon`, `getStateColor`
- Adapters: `fromQuery`, `createFromQuery`

### 3. React Components

**Files with .tsx extension in frontend/lib:**
- `frontend/lib/context/member-context.tsx` - MemberContext provider
- `frontend/lib/runtime/utils/state-registry.tsx` - State registry component

**Note:** Most React components are in `frontend/components/` (not indexed in frontend/lib)

### 4. Hooks (30 total in frontend/lib)

**Key hooks identified:**
- `useAsyncQuery` - Base async query wrapper
- `useReconciliations` - Reconciliation data hook
- `usePendingReconciliations` - Pending reconciliations
- `useScanReconciliations` - Scan for matches
- `useConfirmReconciliation` - Mutation hook
- `useRejectReconciliation` - Mutation hook
- `useBanksQuery`, `useOverviewQuery`, `useTransactionsQuery`, `useStatementsQuery`, `useCategoryListQuery`, `useUploadQuery`, `useExportCSVQuery`
- `useNetWorth` - Net worth query
- `useCashflow` - Cashflow analysis
- `useManagedAccounts` - Account management
- `useLoans`, `useInvestments`, `useCards`
- `useExplainability`, `useExplainabilityCollection`, `useRecommendationExplanation`

### 5. Utility Dependencies

**Internal call relationships found:**
- `useManagedAccounts` → `useAppQuery`
- `useCashflow` → `useAppQuery`
- `useNetWorth` → `useAppQuery`
- `createFromQuery` → `fromQuery`
- `formatPaise` → `formatINR`
- `formatINRCompact` → `formatINR`
- `fetchCashflowSummary` → `fetchCashflow`
- `createConfidence` → `isValidConfidenceBps`
- `mapNetworthToModel` → `calculateTrend`

### 6. Type Usage

**Key interfaces with source available:**
- `RuntimeStateResult<T>` - State result interface
- `StateConfig` - State configuration
- `ExplainabilityState` - Zustand state
- `ExportCSVState`, `UploadState` - State types
- `AppState` - App store state
- `TableColumn`, `TableRow`, `Table` - Table detection
- `LabelValuePair`, `ProximityConfig` - Proximity engine
- `ValidationResult` - Transaction validation
- `MemberContextType` - Context type
- `FieldConfig`, `Metadata`, `BankConfig` - Metadata extraction
- `UseExplainabilityResult`, `UseExplainabilityCollectionResult`, `UseRecommendationExplanationResult` - Hook return types
- `FlattenedItem` - Explanation flattening

## Success Criteria Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CGC answers majority of navigation questions | ✅ PASS | 80 files, 175 functions, 20 interfaces discovered via CGC |
| File reads remain minimal | ✅ PASS | Only 5 targeted reads for barrel files |
| Recursive repository exploration eliminated | ✅ PASS | No `list_files` recursive calls needed |
| Fallbacks clearly justified | ✅ PASS | No fallbacks needed - CGC provided all required data |

## Remaining Limitations

1. **File source not available via Cypher:** The `f.source` field returns null when querying files directly. Must use `find_code()` to get source code.

2. **Module node path null:** Some Module nodes have `m.path: null` in Cypher results, making it harder to filter by path.

3. **CALLS relationship incomplete:** Some function calls may not be detected due to:
   - Dynamic imports
   - Complex TypeScript patterns
   - External library calls

4. **Result limits:** CGC has a 50-result limit for `find_code` and `analyze_code_relationships`, which may truncate large result sets.

## Recommendations

1. **Configuration is optimal:** The current `.cgcignore` and CGC configuration are well-tuned for this project.

2. **Use `find_code()` for source:** When source code is needed, use `find_code()` instead of Cypher queries on File nodes.

3. **Use Cypher for relationships:** Cypher queries work well for finding relationships between functions and interfaces.

4. **No changes needed to .clinerules:** The existing rules already prioritize CGC-first exploration.

## Metrics Summary

- **CGC Queries:** 15+ (Cypher + find_code)
- **File Reads:** 5 (targeted barrel files only)
- **Grep Queries:** 0
- **list_files calls:** 1 (initial directory listing)
- **Total files analyzed:** 80
- **Total functions found:** 175
- **Total interfaces found:** 20