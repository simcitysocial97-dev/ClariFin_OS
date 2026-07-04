# ENTERPRISE REPAIR PLAN - FRONTEND HOOK LAYER

## PHASE 1: ROOT CAUSE ANALYSIS

### Dependency Graph Analysis

**BROKEN LAYER (use-finance-data.ts)**
- 27 errors in the file itself
- Used by 50+ consumer files
- All hooks missing generic type parameters
- Missing: `useUpload`, `useOverview`

**WORKING LAYER (use-query-finance.ts)**
- Uses `useAsyncQuery<T>` with proper generics
- Properly typed with `HookState<T>`
- Used by: dashboard, networth, cashflow, investments components

**CONSUMER FILES (by error count)**
1. app/accounts/page.tsx - 22 errors
2. app/loans/page.tsx - 21 errors
3. app/cards/page.tsx - 15 errors
4. app/transactions/page.tsx - 11 errors
5. components/recurring/subscriptions-table.tsx - 9 errors
6. components/income/income-streams-table.tsx - 9 errors

### Hook Return Type Analysis

| Hook | Expected Return | Current Inferred | Missing Generic |
|------|-----------------|------------------|-----------------|
| useAccounts | HookState<{ accounts: Account[]; total: number }> | HookState<never> | Account[] |
| useCards | HookState<{ cards: Card[]; total: number }> | HookState<never> | Card[] |
| useLoans | HookState<LoansResponse> | HookState<never> | LoansResponse |
| useTransactions | HookState<{ transactions: Transaction[]; pagination: Pagination }> | HookState<never> | Transaction[] |
| useCategories | HookState<CategoriesResponse> | HookState<never> | CategoriesResponse |
| useInvestments | HookState<InvestmentsResponse> | HookState<never> | InvestmentsResponse |
| useSnapshots | HookState<SnapshotsResponse> | HookState<never> | MonthlySnapshot[] |
| useCashflow | HookState<MonthlyCashflowResponse> | HookState<never> | MonthlyCashflow[] |
| useAnalytics | HookState<AnalyticsData> | HookState<never> | AnalyticsData |
| useNetWorth | HookState<NetWorth> | HookState<never> | NetWorth |
| useNetWorthForecast | HookState<NetWorthProjectionResponse> | HookState<never> | NetWorthProjection[] |
| useAmortizationSchedule | HookState<AmortizationSchedule> | HookState<never> | AmortizationEntry[] |
| useIncomeStreams | HookState<IncomeSourcesResponse> | HookState<never> | IncomeStream[] |
| useRecurringTransactions | HookState<RecurringTransactionsResponse> | HookState<never> | RecurringTransaction[] |
| useV2Imports | HookState<ImportListResponse> | HookState<never> | ImportItem[] |

### Missing Exports Analysis

**useUpload** (expected in upload-modal.tsx)
- Expected: `{ upload, result, error }`
- `upload(file: File, member: string)` - function to upload PDF
- `result` - UploadResult type
- `error` - Error | null

**useOverview** (expected in upload-modal.tsx)
- Expected: `{ data, isLoading, error, refetch }`
- `data` - OverviewData type
- Should use `fetchOverview` from api/client

## PHASE 2: REPAIR THE HOOK LAYER

### Changes to use-finance-data.ts

1. **Add type imports** at the top:
```typescript
import type { Account } from '@/lib/api/client';
import type { Card } from '@/lib/api/client';
import type { Loan, LoansResponse, AmortizationSchedule, PrepaymentResult } from '@/types/loan';
import type { Transaction } from '@/types/transaction';
import type { CategoriesResponse } from '@/types/api';
import type { InvestmentsResponse, InvestmentSummary } from '@/types/investment';
import type { MonthlySnapshot, SnapshotsResponse, NetWorthProjectionResponse, MonthlyCashflowResponse, CashflowBreakdown, NetWorth } from '@/types/financial';
import type { IncomeSourcesResponse } from '@/types/income';
import type { RecurringTransactionsResponse } from '@/types/recurring';
import type { ImportListResponse } from '@/types/v2';
import type { OverviewData } from '@/lib/api/client';
```

2. **Fix each hook** to use proper generics:
```typescript
// Before (broken)
export function useAccounts() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['accounts'],
    queryFn: async () => { return []; },
    initialData: []
  });
  return { accounts: data, isLoading, error };
}

// After (fixed)
export function useAccounts() {
  const { data, isLoading, error } = useQuery<Account[], Error>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const result = await fetchAccounts();
      return result.accounts;
    },
  });
  return { accounts: data ?? [], isLoading, error };
}
```

## PHASE 3: FIX THE TWO BROKEN EXPORTS

### Add useUpload hook
```typescript
export function useUpload() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const upload = async (file: File, member: string = 'Self') => {
    setUploading(true);
    setError(null);
    try {
      const result = await uploadStatement(file, member);
      setResult(result);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Upload failed'));
    } finally {
      setUploading(false);
    }
  };

  return { upload, result, error, uploading };
}
```

### Add useOverview hook
```typescript
export function useOverview() {
  const { data, isLoading, error } = useQuery<OverviewData, Error>({
    queryKey: ['overview'],
    queryFn: fetchOverview,
  });
  return { data: data ?? null, isLoading, error };
}
```

## PHASE 4: FIX QUERY SIGNATURES

### Fix useCalculateGoal
```typescript
// Before (broken - queryFn receives wrong params)
queryFn: async (params: { targetAmount: number; monthlyContribution: number; years: number }) => {

// After (fixed - use proper signature)
queryFn: async () => {
  // This hook should accept params as argument, not in queryFn
}
```

### Fix useCalculateWhatIf
Similar fix needed.

## PHASE 5: REPAIR DOWNSTREAM FILES

Order of repair (highest error count first):
1. app/accounts/page.tsx
2. app/loans/page.tsx
3. app/cards/page.tsx
4. app/transactions/page.tsx
5. Remaining components

## PHASE 6: REMOVE DUPLICATES

After hook layer is fixed, check if these files are still needed:
- lib/hooks/use-accounts.ts
- lib/hooks/use-cards.ts
- lib/hooks/use-queries.ts

## PHASE 7: VALIDATION

Run after each phase:
```bash
cd frontend && npx tsc --noEmit
```

## PHASE 8: BROWSER VALIDATION

Only after build succeeds:
```bash
cd frontend && npm run build
```

## PHASE 9: GIT COMMITS

Create branch and commit after each phase:
```bash
git checkout -b fix/typescript-hook-layer
git add -A
git commit -m "fix: restore typed React Query hooks"
```

---

**READY FOR IMPLEMENTATION**

Please toggle to Act mode to proceed with the repair.