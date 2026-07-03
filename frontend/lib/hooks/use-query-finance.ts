import { useQueryClient } from '@tanstack/react-query';
import {
  fetchOverview,
  fetchV2Imports,
  fetchBehaviorScore,
  fetchNetWorth,
  fetchNetWorthTrend,
  fetchAssetAllocation,
  fetchMonthlyCashflow,
  fetchCashflowBreakdown,
  fetchInvestmentSummary,
  fetchLoans,
  fetchRecurringTransactions,
} from '@/lib/api/client';
import type { ImportListResponse } from '@/types/v2';
import type { NetWorthTrendResponse, MonthlyCashflowResponse, CashflowBreakdown } from '@/types/financial';
import type { AssetAllocationResponse } from '@/types/investment';
import type { InvestmentSummary } from '@/types/investment';
import type { LoansResponse } from '@/types/loan';
import type { RecurringTransactionsResponse } from '@/types/recurring';
import type { OverviewData, BehaviorScore, NetWorth } from '@/lib/api/client';
import { useAsyncQuery, HookState } from './use-async-query';

export const queryKeys = {
  overview: ['overview'] as const,
  imports: (params?: { status?: string; page?: number; per_page?: number }) =>
    ['imports', params] as const,
  behaviorScore: ['behavior', 'score'] as const,
  netWorth: ['networth'] as const,
  netWorthTrend: (months?: number) => ['networth', 'trend', months] as const,
  assetAllocation: ['allocation'] as const,
  monthlyCashflow: (months?: number) => ['cashflow', 'monthly', months] as const,
  cashflowBreakdown: (month?: string) => ['cashflow', 'breakdown', month] as const,
  investmentSummary: ['investments', 'summary'] as const,
  loans: (status?: string) => ['loans', status] as const,
  recurringTransactions: (activeOnly?: boolean) => ['recurring', activeOnly] as const,
};

type FinanceQueryFactory<T, Args extends any[] = []> = (...args: Args) => HookState<T>;

function createFinanceQuery<T, Args extends any[] = []>(factory: (...args: Args) => HookState<T>): FinanceQueryFactory<T, Args> {
  return factory;
}

export const useImportsQuery = createFinanceQuery<ImportListResponse, [{ status?: string; page?: number; per_page?: number }]>((params = {}) => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<ImportListResponse>(queryKeys.imports(params), () => fetchV2Imports(params), 30_000);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.imports(params) });
  };

  return { ...result, refetch };
});

export const useOverviewQuery = createFinanceQuery<OverviewData>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<OverviewData>(queryKeys.overview, fetchOverview);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.overview });
  };

  return { ...result, refetch };
});

export const useBehaviorScoreQuery = createFinanceQuery<BehaviorScore>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<BehaviorScore>(queryKeys.behaviorScore, fetchBehaviorScore);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.behaviorScore });
  };

  return { ...result, refetch };
});

export const useNetWorthQuery = createFinanceQuery<NetWorth>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<NetWorth>(queryKeys.netWorth, fetchNetWorth);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.netWorth });
  };

  return { ...result, refetch };
});

export const useNetWorthTrendQuery = createFinanceQuery<NetWorthTrendResponse, [number]>((months: number) => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<NetWorthTrendResponse>(queryKeys.netWorthTrend(months), () => fetchNetWorthTrend(months));

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.netWorthTrend(months) });
  };

  return { ...result, refetch };
});

export const useAssetAllocationQuery = createFinanceQuery<AssetAllocationResponse>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<AssetAllocationResponse>(queryKeys.assetAllocation, fetchAssetAllocation);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.assetAllocation });
  };

  return { ...result, refetch };
});

export const useMonthlyCashflowQuery = createFinanceQuery<MonthlyCashflowResponse>(() => {
  const queryClient = useQueryClient();
  const months = undefined;
  const result = useAsyncQuery<MonthlyCashflowResponse>(queryKeys.monthlyCashflow(months), () => fetchMonthlyCashflow(months));

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.monthlyCashflow(months) });
  };

  return { ...result, refetch };
});

export const useCashflowBreakdownQuery = createFinanceQuery<CashflowBreakdown>(() => {
  const queryClient = useQueryClient();
  const month = undefined;
  const result = useAsyncQuery<CashflowBreakdown>(queryKeys.cashflowBreakdown(month), () => fetchCashflowBreakdown(month));

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.cashflowBreakdown(month) });
  };

  return { ...result, refetch };
});

export const useInvestmentSummaryQuery = createFinanceQuery<InvestmentSummary>(() => {
  const queryClient = useQueryClient();
  const result = useAsyncQuery<InvestmentSummary>(queryKeys.investmentSummary, fetchInvestmentSummary);

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.investmentSummary });
  };

  return { ...result, refetch };
});

export const useLoansQuery = createFinanceQuery<LoansResponse>(() => {
  const queryClient = useQueryClient();
  const status = undefined;
  const result = useAsyncQuery<LoansResponse>(queryKeys.loans(status), () => fetchLoans(status));

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.loans(status) });
  };

  return { ...result, refetch };
});

export const useRecurringTransactionsQuery = createFinanceQuery<RecurringTransactionsResponse>(() => {
  const queryClient = useQueryClient();
  const activeOnly = undefined;
  const result = useAsyncQuery<RecurringTransactionsResponse>(queryKeys.recurringTransactions(activeOnly), () => fetchRecurringTransactions(activeOnly));

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: queryKeys.recurringTransactions(activeOnly) });
  };

  return { ...result, refetch };
});