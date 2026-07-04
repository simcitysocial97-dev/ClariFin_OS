"use client";

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

// API function imports
import {
  fetchAccounts,
  fetchCards,
  fetchOverview,
  fetchV2Imports,
  fetchTransactions,
  fetchCategories,
  fetchAnalytics,
  fetchLoans,
  fetchInvestments,
  fetchMonthlyCashflow,
  fetchCashflowSummary,
  fetchCashflowBreakdown,
  fetchNetWorth,
  fetchNetWorthTrend,
  fetchIncomeSources,
  fetchRecurringTransactions,
  fetchStatements,
  fetchSnapshots,
  generateSnapshot,
  backfillSnapshots,
  uploadStatement,
  createAccount,
  updateAccount,
  deleteAccount,
  createCard,
  updateCard,
  deleteCard,
  createLoan,
  deleteLoan,
  simulatePrepayment,
  createInvestment,
  updateInvestment,
  deleteInvestment,
  createIncomeSource,
  updateIncomeSource,
  deleteIncomeSource,
  createRecurringTransaction,
  updateRecurringTransaction,
  deleteRecurringTransaction,
  updateTransactionCategory,
} from '@/lib/api/client';

// Type imports
import type { Account, AccountCreateInput, AccountUpdateInput, Card, Statement } from '@/lib/api/client';
import type { Transaction } from '@/types/transaction';
import type { CategoriesResponse, AnalyticsData } from '@/types/api';
import type { InvestmentsResponse, Investment, InvestmentCreate, InvestmentUpdate } from '@/types/investment';
import type { MonthlySnapshot, NetWorthProjectionResponse, MonthlyCashflowResponse, CashflowBreakdown, CashflowSummary, NetWorth, NetWorthTrendResponse, GoalProjection, WhatIfResult, SnapshotBackfillResponse } from '@/types/financial';
import type { IncomeSourcesResponse, IncomeSource, IncomeSourceCreate, IncomeSourceUpdate } from '@/types/income';
import type { RecurringTransactionsResponse, RecurringTransaction, RecurringTransactionCreate, RecurringTransactionUpdate } from '@/types/recurring';
import type { ImportItem } from '@/types/v2';
import type { OverviewData } from '@/lib/api/client';
import type { AmortizationSchedule, PrepaymentResult, Loan, LoanCreate, LoansResponse, PrepaymentSimulationRequest } from '@/types/loan';

// ============================================================================
// INPUT TYPES FOR MUTATIONS
// ============================================================================

// Note: AccountCreateInput, AccountUpdateInput, and PrepaymentSimulationRequest
// are imported from their respective type files above

// ============================================================================
// HOOK STATE INTERFACE
// ============================================================================

export interface HookState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  isFetching: boolean;
  hasLoaded: boolean;
  refetch: () => Promise<void>;
}

// ============================================================================
// UPLOAD HOOK
// ============================================================================

export interface UploadResult {
  success: boolean;
  bank: string;
  transaction_count: number;
  validation_status: string;
  log: string[];
}

export function useUpload() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const upload = async (file: File, member: string = 'Self') => {
    setUploading(true);
    setError(null);
    try {
      const uploadResult = await uploadStatement(file, member);
      setResult(uploadResult);
    } catch (e) {
      setError(e instanceof Error ? e : new Error('Upload failed'));
    } finally {
      setUploading(false);
    }
  };

  return { upload, result, error, uploading };
}

// ============================================================================
// OVERVIEW HOOK
// ============================================================================

export function useOverview() {
  const queryClient = useQueryClient();
  const result = useQuery<OverviewData, Error>({
    queryKey: ['overview'],
    queryFn: fetchOverview,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['overview'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
  };
}

// ============================================================================
// NET WORTH HOOKS
// ============================================================================

export function useNetWorth() {
  const queryClient = useQueryClient();
  const result = useQuery<NetWorth, Error>({
    queryKey: ['netWorth'],
    queryFn: fetchNetWorth,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['netWorth'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    // Convenience properties
    netWorth: result.data?.net_worth_paise ?? 0,
    assets: result.data?.total_assets_paise ?? 0,
    liabilities: result.data?.total_liabilities_paise ?? 0,
    currency: 'INR',
  };
}

export function useNetWorthTrend() {
  const queryClient = useQueryClient();
  const result = useQuery<NetWorthTrendResponse, Error>({
    queryKey: ['netWorthTrend'],
    queryFn: () => fetchNetWorthTrend(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['netWorthTrend'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    trend: result.data?.trend ?? [],
  };
}

// ============================================================================
// ACCOUNTS HOOKS
// ============================================================================

export function useAccounts() {
  const queryClient = useQueryClient();
  const result = useQuery<Account[], Error>({
    queryKey: ['accounts'],
    queryFn: async () => {
      const res = await fetchAccounts();
      return res.accounts;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['accounts'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    accounts: result.data ?? [],
  };
}

export function useCreateAccount() {
  const queryClient = useQueryClient();
  const result = useMutation<Account, Error, AccountCreateInput>({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    }
  });

  return {
    ...result,
    createAccount: result.mutate,
    creating: result.isPending,
  };
}

export function useUpdateAccount() {
  const queryClient = useQueryClient();
  const result = useMutation<Account, Error, { id: number; account: AccountUpdateInput }>({
    mutationFn: ({ id, account }) => updateAccount(id, account),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    }
  });

  return {
    ...result,
    updateAccount: result.mutate,
    updating: result.isPending,
  };
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  const result = useMutation<{ success: boolean; message: string }, Error, number>({
    mutationFn: deleteAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts'] });
    }
  });

  return {
    ...result,
    deleteAccount: result.mutate,
    deleting: result.isPending,
  };
}

// ============================================================================
// CARDS HOOKS
// ============================================================================

export function useCards() {
  const queryClient = useQueryClient();
  const result = useQuery<Card[], Error>({
    queryKey: ['cards'],
    queryFn: async () => {
      const res = await fetchCards();
      return res.cards;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['cards'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    cards: result.data ?? [],
  };
}

export function useCreateCard() {
  const queryClient = useQueryClient();
  const result = useMutation<Card, Error, Omit<Card, 'id' | 'created_at' | 'updated_at' | 'credit_limit_display' | 'is_active'>>({
    mutationFn: createCard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    }
  });

  return {
    ...result,
    createCard: result.mutate,
    creating: result.isPending,
  };
}

export function useUpdateCard() {
  const queryClient = useQueryClient();
  const result = useMutation<Card, Error, { id: number; card: Partial<Card> }>({
    mutationFn: ({ id, card }) => updateCard(id, card),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    }
  });

  return {
    ...result,
    updateCard: result.mutate,
    updating: result.isPending,
  };
}

export function useDeleteCard() {
  const queryClient = useQueryClient();
  const result = useMutation<{ success: boolean; message: string }, Error, number>({
    mutationFn: deleteCard,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cards'] });
    }
  });

  return {
    ...result,
    deleteCard: result.mutate,
    deleting: result.isPending,
  };
}

// ============================================================================
// LOANS HOOKS
// ============================================================================

export function useLoans() {
  const queryClient = useQueryClient();
  const result = useQuery<LoansResponse, Error>({
    queryKey: ['loans'],
    queryFn: () => fetchLoans(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['loans'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    loans: result.data?.loans ?? [],
  };
}

export function useCreateLoan() {
  const queryClient = useQueryClient();
  const result = useMutation<Loan, Error, LoanCreate>({
    mutationFn: createLoan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] });
    }
  });

  return {
    ...result,
    createLoan: result.mutate,
    creating: result.isPending,
  };
}

export function useDeleteLoan() {
  const queryClient = useQueryClient();
  const result = useMutation<void, Error, number>({
    mutationFn: deleteLoan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] });
    }
  });

  return {
    ...result,
    deleteLoan: result.mutate,
    deleting: result.isPending,
  };
}

export function useAmortizationSchedule() {
  const queryClient = useQueryClient();
  const result = useQuery<AmortizationSchedule, Error>({
    queryKey: ['amortizationSchedule'],
    queryFn: async () => {
      // This would need a loanId parameter in a real implementation
      return {
        loan_id: 0,
        emi_paise: 0,
        total_periods: 0,
        total_interest_paise: 0,
        schedule: []
      };
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['amortizationSchedule'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    schedule: result.data?.schedule ?? [],
  };
}

export function useSimulatePrepayment() {
  const queryClient = useQueryClient();
  const result = useMutation<PrepaymentResult, Error, { loanId: number; data: PrepaymentSimulationRequest }>({
    mutationFn: ({ loanId, data }) => simulatePrepayment(loanId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['loans'] });
    }
  });

  return {
    ...result,
    simulatePrepayment: result.mutate,
    simulating: result.isPending,
  };
}

// ============================================================================
// TRANSACTIONS HOOKS
// ============================================================================

export function useTransactions() {
  const queryClient = useQueryClient();
  const result = useQuery<Transaction[], Error>({
    queryKey: ['transactions'],
    queryFn: async () => {
      const res = await fetchTransactions();
      return res.transactions;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['transactions'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    transactions: result.data ?? [],
  };
}

// ============================================================================
// CATEGORIES HOOKS
// ============================================================================

export function useCategories() {
  const queryClient = useQueryClient();
  const result = useQuery<CategoriesResponse, Error>({
    queryKey: ['categories'],
    queryFn: () => fetchCategories(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['categories'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    categories: result.data?.summary ?? [],
  };
}

export function useUpdateCategory() {
  const queryClient = useQueryClient();
  const result = useMutation<void, Error, { id: number; category: string; subcategory?: string }>({
    mutationFn: ({ id, category, subcategory }) => updateTransactionCategory(id, category, subcategory),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categories'] });
    }
  });

  return {
    ...result,
    update: result.mutate,
    updating: result.isPending,
  };
}

// ============================================================================
// INVESTMENTS HOOKS
// ============================================================================

export function useInvestments() {
  const queryClient = useQueryClient();
  const result = useQuery<InvestmentsResponse, Error>({
    queryKey: ['investments'],
    queryFn: () => fetchInvestments(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['investments'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    investments: result.data?.investments ?? [],
  };
}

export function useCreateInvestment() {
  const queryClient = useQueryClient();
  const result = useMutation<Investment, Error, InvestmentCreate>({
    mutationFn: createInvestment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] });
    }
  });

  return {
    ...result,
    createInvestment: result.mutate,
    creating: result.isPending,
  };
}

export function useUpdateInvestment() {
  const queryClient = useQueryClient();
  const result = useMutation<Investment, Error, { id: number; investment: InvestmentUpdate }>({
    mutationFn: ({ id, investment }) => updateInvestment(id, investment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] });
    }
  });

  return {
    ...result,
    updateInvestment: result.mutate,
    updating: result.isPending,
  };
}

export function useDeleteInvestment() {
  const queryClient = useQueryClient();
  const result = useMutation<{ success: boolean; message: string }, Error, number>({
    mutationFn: deleteInvestment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['investments'] });
    }
  });

  return {
    ...result,
    deleteInvestment: result.mutate,
    deleting: result.isPending,
  };
}

// ============================================================================
// CASHFLOW HOOKS
// ============================================================================

export function useCashflow() {
  const queryClient = useQueryClient();
  const result = useQuery<MonthlyCashflowResponse, Error>({
    queryKey: ['cashflow'],
    queryFn: () => fetchMonthlyCashflow(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['cashflow'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    cashflow: result.data?.months ?? [],
  };
}

export function useMonthlyCashflow() {
  return useCashflow();
}

export function useCashflowSummary() {
  const queryClient = useQueryClient();
  const result = useQuery<CashflowSummary, Error>({
    queryKey: ['cashflowSummary'],
    queryFn: fetchCashflowSummary,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['cashflowSummary'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
  };
}

export function useCashflowBreakdown() {
  const queryClient = useQueryClient();
  const result = useQuery<CashflowBreakdown, Error>({
    queryKey: ['cashflowBreakdown'],
    queryFn: () => fetchCashflowBreakdown(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['cashflowBreakdown'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    breakdown: result.data ?? null,
  };
}

// ============================================================================
// ANALYTICS HOOKS
// ============================================================================

export function useAnalytics() {
  const queryClient = useQueryClient();
  const result = useQuery<AnalyticsData, Error>({
    queryKey: ['analytics'],
    queryFn: fetchAnalytics,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['analytics'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    analytics: result.data ?? null,
  };
}

// ============================================================================
// SNAPSHOTS HOOKS
// ============================================================================

export function useSnapshots() {
  const queryClient = useQueryClient();
  const result = useQuery<MonthlySnapshot[], Error>({
    queryKey: ['snapshots'],
    queryFn: async () => {
      const res = await fetchSnapshots();
      return res.snapshots;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['snapshots'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    snapshots: result.data ?? [],
  };
}

export function useGenerateSnapshot() {
  const queryClient = useQueryClient();
  const result = useMutation<MonthlySnapshot, Error, string | undefined>({
    mutationFn: (month) => generateSnapshot(month),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    }
  });

  return {
    ...result,
    generateSnapshot: result.mutate,
    generating: result.isPending,
  };
}

export function useBackfillSnapshots() {
  const queryClient = useQueryClient();
  const result = useMutation<SnapshotBackfillResponse, Error, { start: string; end: string }>({
    mutationFn: backfillSnapshots,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['snapshots'] });
    }
  });

  return {
    ...result,
    backfillSnapshots: result.mutate,
    backfilling: result.isPending,
  };
}

// ============================================================================
// INCOME HOOKS
// ============================================================================

export function useIncomeStreams() {
  const queryClient = useQueryClient();
  const result = useQuery<IncomeSourcesResponse, Error>({
    queryKey: ['incomeStreams'],
    queryFn: () => fetchIncomeSources(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['incomeStreams'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    incomeStreams: result.data?.sources ?? [],
  };
}

export function useIncomeSources() {
  return useIncomeStreams();
}

export function useCreateIncomeSource() {
  const queryClient = useQueryClient();
  const result = useMutation<IncomeSource, Error, IncomeSourceCreate>({
    mutationFn: createIncomeSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeStreams'] });
    }
  });

  return {
    ...result,
    createIncomeSource: result.mutate,
    creating: result.isPending,
  };
}

export function useUpdateIncomeSource() {
  const queryClient = useQueryClient();
  const result = useMutation<IncomeSource, Error, { id: number; source: IncomeSourceUpdate }>({
    mutationFn: ({ id, source }) => updateIncomeSource(id, source),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeStreams'] });
    }
  });

  return {
    ...result,
    updateIncomeSource: result.mutate,
    updating: result.isPending,
  };
}

export function useDeleteIncomeSource() {
  const queryClient = useQueryClient();
  const result = useMutation<{ success: boolean; message: string }, Error, number>({
    mutationFn: deleteIncomeSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['incomeStreams'] });
    }
  });

  return {
    ...result,
    deleteIncomeSource: result.mutate,
    deleting: result.isPending,
  };
}

// ============================================================================
// RECURRING TRANSACTIONS HOOKS
// ============================================================================

export function useRecurringTransactions() {
  const queryClient = useQueryClient();
  const result = useQuery<RecurringTransactionsResponse, Error>({
    queryKey: ['recurringTransactions'],
    queryFn: () => fetchRecurringTransactions(),
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['recurringTransactions'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    recurringTransactions: result.data?.recurring ?? [],
  };
}

export function useCreateRecurringTransaction() {
  const queryClient = useQueryClient();
  const result = useMutation<RecurringTransaction, Error, RecurringTransactionCreate>({
    mutationFn: createRecurringTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurringTransactions'] });
    }
  });

  return {
    ...result,
    createRecurringTransaction: result.mutate,
    creating: result.isPending,
  };
}

export function useUpdateRecurringTransaction() {
  const queryClient = useQueryClient();
  const result = useMutation<RecurringTransaction, Error, { id: number; transaction: RecurringTransactionUpdate }>({
    mutationFn: ({ id, transaction }) => updateRecurringTransaction(id, transaction),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurringTransactions'] });
    }
  });

  return {
    ...result,
    updateRecurringTransaction: result.mutate,
    updating: result.isPending,
  };
}

export function useDeleteRecurringTransaction() {
  const queryClient = useQueryClient();
  const result = useMutation<{ success: boolean; message: string }, Error, number>({
    mutationFn: deleteRecurringTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recurringTransactions'] });
    }
  });

  return {
    ...result,
    deleteRecurringTransaction: result.mutate,
    deleting: result.isPending,
  };
}

// ============================================================================
// PROJECTION HOOKS
// ============================================================================

export function useNetWorthProjection() {
  const queryClient = useQueryClient();
  const result = useQuery<NetWorthProjectionResponse, Error>({
    queryKey: ['netWorthProjection'],
    queryFn: async () => {
      // This would need parameters in a real implementation
      return {
        projections: [],
        assumptions: {
          equity_return_percent: 0,
          debt_return_percent: 0,
          savings_basis: '',
          monthly_compounding: false,
          loan_interest_calculation: '',
          months_projected: 0
        },
        summary: { starting_net_worth_paise: 0, ending_net_worth_paise: 0, net_worth_change_paise: 0 }
      };
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['netWorthProjection'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    forecast: result.data?.projections ?? [],
  };
}

export function useNetWorthForecast() {
  return useNetWorthProjection();
}

export function useCalculateGoal() {
  const queryClient = useQueryClient();
  const result = useQuery<GoalProjection, Error>({
    queryKey: ['calculateGoal'],
    queryFn: async () => {
      // This would need parameters in a real implementation
      return { months_needed: null, projected_date: null, total_contributed_paise: 0, total_returns_paise: 0, target_achievable: false };
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['calculateGoal'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    calculateGoal: result.data ?? null,
  };
}

export function useCalculateWhatIf() {
  const queryClient = useQueryClient();
  const result = useQuery<WhatIfResult, Error>({
    queryKey: ['whatIfSimulation'],
    queryFn: async () => {
      // This would need parameters in a real implementation
      return {
        baseline: [],
        modified: [],
        difference_at_1y_paise: 0,
        difference_at_3y_paise: 0,
        difference_at_5y_paise: 0,
        percentage_improvement_5y: 0,
        baseline_summary: { starting_net_worth_paise: 0, ending_net_worth_paise: 0, net_worth_change_paise: 0 },
        modified_summary: { starting_net_worth_paise: 0, ending_net_worth_paise: 0, net_worth_change_paise: 0 },
        assumptions: { equity_return_percent: 0, debt_return_percent: 0, savings_basis: '', monthly_compounding: false, loan_interest_calculation: '', months_projected: 0 }
      };
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['whatIfSimulation'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    calculateWhatIf: result.data ?? null,
  };
}

// ============================================================================
// STATEMENTS HOOK
// ============================================================================

export function useStatements() {
  const queryClient = useQueryClient();
  const result = useQuery<Statement[], Error>({
    queryKey: ['statements'],
    queryFn: async () => {
      const res = await fetchStatements();
      return res.statements;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['statements'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    statements: result.data ?? [],
  };
}

// ============================================================================
// V2 IMPORTS HOOK
// ============================================================================

export function useV2Imports() {
  const queryClient = useQueryClient();
  const result = useQuery<ImportItem[], Error>({
    queryKey: ['v2Imports'],
    queryFn: async () => {
      const res = await fetchV2Imports();
      return res.items;
    },
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['v2Imports'] });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
    imports: result.data ?? [],
  };
}

// ============================================================================
// TYPE ALIASES FOR CONVENIENCE
// ============================================================================

export type { Account, Card, Transaction, CategoriesResponse, InvestmentsResponse, LoansResponse, MonthlySnapshot, NetWorth, OverviewData };