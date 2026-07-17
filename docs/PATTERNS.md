# Patterns — ClariFin_OS Frontend Architecture

> Canonical patterns for frontend development. Every capability follows this architecture.

---

## Shared Query Runtime

The shared query runtime provides a consistent, type-safe interface for all React Query operations.

### Architecture Flow

```
API Response
     ↓
DTO (Zod Schema)
     ↓
Mapper (Pure transformation)
     ↓
Model (Domain-friendly)
     ↓
Query Runtime (useAppQuery/useAppMutation)
     ↓
Component
     ↓
Explainability (Confidence, Evidence, Source)
     ↓
UI (Presentation)
```

### QueryKeyFactory

All query keys are centralized in `frontend/lib/query/queryKeys.ts`.

```typescript
// Query keys are organized by capability
export const queryKeys = {
  // Financial Health capability
  financialHealth: {
    summary: () => ['financialHealth', 'summary'] as const,
  },

  // Cashflow capability
  cashflow: {
    monthly: (months: number = 6) => ['cashflow', 'monthly', months] as const,
  },

  // Account Management capability
  accounts: {
    managed: () => ['accounts', 'managed'] as const,
    computed: () => ['accounts', 'computed'] as const,
  },

  // Credit Cards capability
  cards: {
    list: () => ['cards', 'list'] as const,
  },

  // Debt Management capability
  loans: {
    list: () => ['loans', 'list'] as const,
    schedule: (id: string | null) => ['loans', 'schedule', id] as const,
  },

  // Reconciliation capability
  reconciliation: {
    pending: () => ['reconciliation', 'pending'] as const,
  },

  // Behavior capability
  behavior: {
    score: () => ['behavior', 'score'] as const,
    insights: () => ['behavior', 'insights'] as const,
  },

  // Analytics capability
  analytics: {
    overview: () => ['analytics', 'overview'] as const,
  },

  // Investments capability
  investments: {
    list: () => ['investments', 'list'] as const,
  },
} as const
```

**Rules:**
- All keys return `readonly unknown[]` (readonly tuples)
- Keys are deterministic - same input always returns same key
- No string duplication - keys are defined once
- Keys align with capability registry

### QueryFactory (useAppQuery)

`useAppQuery` wraps TanStack Query with project defaults and metadata.

```typescript
import { useAppQuery, queryKeys, STALE_TIME } from '@/lib/query'

export function useNetWorth() {
  return useAppQuery({
    queryKey: queryKeys.networth.current(),
    queryFn: async () => {
      const dto = await fetchNetworthDto()
      return mapNetworthToModel(dto)
    },
    capability: 'account_management',
    staleTime: STALE_TIME.NORMAL,
  })
}
```

**Options:**
- `queryKey` (required) - Query key from QueryKeyFactory
- `queryFn` (required) - Async function returning data
- `capability` (optional) - Capability ID for telemetry
- `staleTime` (optional) - Override default stale time
- `retryPolicy` (optional) - Override default retry policy
- `select` (optional) - Transform data before caching
- `enabled` (optional) - Conditional query execution
- `placeholderData` (optional) - Data while loading

### MutationFactory (useAppMutation)

`useAppMutation` wraps TanStack Query mutations with project defaults.

```typescript
import { useAppMutation, queryKeys } from '@/lib/query'

export function useCreateAccount() {
  return useAppMutation({
    mutationFn: createAccount,
    capability: 'account_management',
    beforeMutate: async (input) => {
      // Return false to cancel mutation
      // Can be used for confirmation, validation, etc.
      return true
    },
    invalidate: [queryKeys.accounts.managed()],
  })
}
```

**Options:**
- `mutationFn` (required) - Async function for mutation
- `capability` (optional) - Capability ID for telemetry
- `beforeMutate` (optional) - Hook called before mutation (return false to cancel)
- `invalidate` (optional) - Query keys to invalidate on success
- `onSuccess` (optional) - Callback after successful mutation
- `onError` (optional) - Callback after failed mutation

### Semantic Stale Times

```typescript
export const STALE_TIME = {
  LIVE: 0,           // Refetch on every mount
  FREQUENT: 30_000,  // 30 seconds
  NORMAL: 120_000,   // 2 minutes
  REFERENCE: 300_000, // 5 minutes
  STATIC: 600_000,   // 10 minutes
}
```

### Retry Policies

```typescript
export const RETRY_POLICY = {
  NONE: 0,         // No retries
  NORMAL: 3,       // 3 attempts
  AGGRESSIVE: 5,   // 5 attempts
}
```

---

## Runtime State Pattern

The `DataStateWrapper` is the **ONLY approved pattern** for rendering queried data. It connects React Query → Runtime Adapter → Loading/Error/Empty runtime → Capability UI.

### Architecture Flow

```
React Query Result
       ↓
fromQuery() Adapter
       ↓
RuntimeState (loading/error/empty/offline/permission/stale/success)
       ↓
DataStateWrapper
       ↓
Override or Default State Component
       ↓
Capability UI (children/render prop)
```

### Usage

```typescript
import { DataStateWrapper } from '@/components/runtime'
import { useNetWorth } from '@/lib/hooks/use-networth'

export function MoneyPositionWidget() {
  const query = useNetWorth()

  return (
    <DataStateWrapper
      query={query}
      loadingVariant="spinner"
      loadingMessage="Loading net worth..."
    >
      {(data) => <MoneyPositionContent data={data} />}
    </DataStateWrapper>
  )
}
```

### Props

| Prop | Type | Description |
|------|------|-------------|
| `query` | `UseQueryResult` | TanStack Query result (required) |
| `children` | `(data: T) => ReactNode` | Render prop for success state |
| `render` | `(data: T) => ReactNode` | Alternative render prop (normalized with children) |
| `loading` | `ReactNode` | Custom loading component override |
| `error` | `ReactNode` | Custom error component override |
| `empty` | `ReactNode` | Custom empty component override |
| `offline` | `ReactNode` | Custom offline component override |
| `permission` | `ReactNode` | Custom permission component override |
| `stale` | `ReactNode` | Stale indicator (renders alongside data) |
| `fallback` | `ReactNode` | Default fallback for unknown states |
| `isEmpty` | `(data: T) => boolean` | Custom empty detection function |
| `loadingVariant` | `LoadingVariant` | Loading display variant |
| `loadingMessage` | `string` | Custom loading message |

### Override Behavior

If an override prop is provided, it takes precedence over the default state component:

```typescript
<DataStateWrapper
  query={query}
  loading={<MyLoading />}
  error={<MyError />}
  empty={<MyEmpty />}
>
  {(data) => <Content data={data} />}
</DataStateWrapper>
```

### State Components

| State | Default Component |
|-------|-------------------|
| `loading` | `LoadingState` |
| `error` | `ErrorState` |
| `empty` | `EmptyState` |
| `offline` | `OfflineState` |
| `permission` | `PermissionState` |
| `stale` | Renders children with optional stale indicator |
| `success` | Renders children |

### Explainability Integration

When an error contains an `Explanation` object, `ErrorState` automatically shows an "Explain" button that opens the `ExplainabilityDrawer`:

```typescript
// Error with explanation
const error = new Error('Calculation failed') as Error & {
  explanation: Explanation
}

// ErrorState will show "Explain" button
<DataStateWrapper query={query} />
```

### Loading Variants

```typescript
// Available variants
<LoadingState variant="spinner" />    // Full spinner with message
<LoadingState variant="skeleton" />   // Skeleton rows
<LoadingState variant="inline" />     // Inline spinner
<LoadingState variant="fullscreen" />  // Full screen overlay
<LoadingState variant="compact" />    // Small centered spinner
```

### Testing

All runtime components have tests in `frontend/tests/components/runtime/`:

- `DataStateWrapper.test.tsx` - Wrapper rendering, state transitions, overrides
- `LoadingState.test.tsx` - Loading variants and accessibility
- `ErrorState.test.tsx` - Error display and retry behavior

Run tests with:
```bash
cd frontend && npm run test -- --run
```

---

## Hook Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| Components | Presentation + user interaction |
| Hooks | Data fetching + business logic |
| Stores (Zustand) | Global application state |
| Lib | Shared utilities + parsers |

---

## Example: Complete Capability Implementation

```typescript
// 1. DTO (frontend/lib/contracts/api/networth.ts)
export const NetWorthResponseSchema = z.object({
  net_worth_paise: z.number().int(),
  assets: z.object({
    total_paise: z.number().int(),
  }),
  liabilities: z.object({
    total_paise: z.number().int(),
  }),
})

// 2. Model (frontend/lib/models/networth.ts)
export interface NetWorthModel {
  netWorthPaise: number
  assetsTotalPaise: number
  liabilitiesTotalPaise: number
}

// 3. Mapper (frontend/lib/mappers/networth.ts)
export function mapNetworthToModel(dto: NetWorthDto): NetWorthModel {
  return {
    netWorthPaise: dto.net_worth_paise,
    assetsTotalPaise: dto.assets.total_paise,
    liabilitiesTotalPaise: dto.liabilities.total_paise,
  }
}

// 4. Hook (frontend/lib/hooks/use-networth.ts)
import { useAppQuery, queryKeys, STALE_TIME } from '@/lib/query'

export function useNetWorth() {
  return useAppQuery({
    queryKey: queryKeys.networth.current(),
    queryFn: async () => {
      const dto = await fetchNetworthDto()
      return mapNetworthToModel(dto)
    },
    capability: 'account_management',
    staleTime: STALE_TIME.NORMAL,
  })
}

// 5. Component (frontend/app/networth/page.tsx)
'use client'
import { useNetWorth } from '@/lib/hooks/use-networth'

export default function NetWorthPage() {
  const { data, isLoading, error } = useNetWorth()
  // ...
}
```

---

## Explainability Runtime

The explainability runtime provides a consistent interface for financial metric explanations.

### Architecture Flow

```
Financial Engine
       ↓
Explanation generated
       ↓
API DTO
       ↓
Zod Contract
       ↓
Mapper (preserves explanation)
       ↓
Model (includes explanation)
       ↓
useExplainability() Hook
       ↓
Component
```

### Explanation Lifecycle

Every financial metric can have an explanation that traces its derivation:

```
Net Worth
    ↓
Assets (sum of accounts + investments)
    ↓
Accounts (list with individual balances)
    ↓
Transactions (source of balance calculations)
    ↓
Source (statement_id, account_id)
```

### Contracts

Located in `frontend/lib/explainability/contracts/`:

- **Evidence** - Single piece of data contributing to a calculation
- **SourceReference** - Business provenance (account, loan, statement, etc.)
- **CalculationStep** - Operation in the calculation chain
- **Confidence** - Score in basis points (0-10000)
- **Explanation** - Complete explanation for a metric

### Utilities

Located in `frontend/lib/explainability/`:

- `createExplanation()` - Factory for creating explanations
- `mergeEvidence()` - Combine evidence arrays
- `sortEvidence()` - Sort by type priority
- `confidenceToBadge()` - Convert BPS to UI level
- `groupEvidence()` - Group by type
- `flattenExplanation()` - Linear form for export/audit

### Hook

```typescript
import { useExplainability } from '@/lib/explainability'

function NetWorthComponent() {
  const { data } = useNetWorth()
  const { state, hasEvidence, confidenceBps, confidenceLevel } = useExplainability(data?.explanation)

  if (state === 'loading') return <Loading />
  if (state === 'empty') return <NoData />

  return (
    <div>
      <NetWorthDisplay value={data.netWorthPaise} />
      {hasEvidence && (
        <ConfidenceBadge level={confidenceLevel} value={confidenceBps} />
      )}
    </div>
  )
}
```

### Confidence

All confidence values are integers in basis points (0-10000 = 0-100%).

```typescript
// Backend generates confidence
confidence: {
  value: 8500,  // 85%
  reason: "Complete data available"
}

// Frontend converts to badge
const level = confidenceToBadge(8500)  // 'high'
```

### Evidence

Evidence is PRESERVED from the backend, not generated in the frontend.

```typescript
// Backend provides evidence
evidence: [
  { id: 'account-1', type: 'data', description: 'Account balance', value: 50000 },
  { id: 'account-2', type: 'data', description: 'Account balance', value: 30000 },
]

// Frontend uses as-is
```

---

## Error Handling

The query runtime normalizes errors to `AppError`:

```typescript
export interface AppError {
  message: string
  code?: string
  capability?: string
}
```

**Important:** The runtime does NOT include UI concerns. Callers handle toasts, modals, and error displays.

```typescript
// In component
const { error } = useAppQuery({ ... })

if (error) {
  toast({
    title: 'Error',
    description: error.message,
    variant: 'destructive',
  })
}
```

---

## Testing

All query factories have contract tests in `frontend/tests/lib/query/`:

- `queryKeys.test.ts` - Query key factory tests
- `useAppQuery.test.ts` - Query factory tests
- `useAppMutation.test.ts` - Mutation factory tests

Run tests with:
```bash
cd frontend && npm run test -- --run