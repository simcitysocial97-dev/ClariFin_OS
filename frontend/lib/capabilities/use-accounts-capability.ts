/**
 * useAccountsCapability Hook - Stage 4 Accounts Intelligence Workspace
 *
 * React hook for accounts state management and orchestration.
 * This is the canonical capability implementation for the Accounts Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { AccountsViewModel } from '@/types/accounts-view-model';
import { accountsMapper } from '@/lib/mappers/accounts-mapper';

// Query key for React Query
const ACCOUNTS_QUERY_KEY = 'accounts';

/**
 * Accounts capability state interface
 */
export interface AccountsCapabilityState {
  // Data
  accounts: AccountsViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  accountTypes: string[];
  institutions: string[];
  statuses: string[];
  dateRange: { from?: string; to?: string } | null;
  balanceRange: { min?: number; max?: number } | null;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected account
  selectedAccountId: string | null;
}

/**
 * Accounts capability actions interface
 */
export interface AccountsCapabilityActions {
  // Fetch
  fetchAccounts: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setAccountTypes: (types: string[]) => void;
  setInstitutions: (institutions: string[]) => void;
  setStatuses: (statuses: string[]) => void;
  setDateRange: (range: { from?: string; to?: string } | null) => void;
  setBalanceRange: (range: { min?: number; max?: number } | null) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectAccount: (accountId: string | null) => void;
}

/**
 * Accounts capability return type
 */
export type AccountsCapabilityReturn = AccountsCapabilityState & AccountsCapabilityActions;

/**
 * useAccountsCapability Hook
 *
 * Provides accounts state management and orchestration for the Accounts Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useAccountsCapability(): AccountsCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [accountTypes, setAccountTypes] = useState<string[]>([]);
  const [institutions, setInstitutions] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<{ from?: string; to?: string } | null>(null);
  const [balanceRange, setBalanceRange] = useState<{ min?: number; max?: number } | null>(null);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    account_types: accountTypes.length > 0 ? accountTypes.join(',') : undefined,
    institutions: institutions.length > 0 ? institutions.join(',') : undefined,
    statuses: statuses.length > 0 ? statuses.join(',') : undefined,
    date_range: dateRange ? `${dateRange.from},${dateRange.to}` : undefined,
  }), [accountTypes, institutions, statuses, dateRange]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<AccountsViewModel | null>({
    queryKey: [ACCOUNTS_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/accounts');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return accountsMapper.mapAccountsDTO(raw);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (React Query v5 uses gcTime instead of cacheTime)
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Loading timeout effect - show message after 10 seconds
  useEffect(() => {
    if (isLoading) {
      loadingTimeoutRef.current = setTimeout(() => {
        setLoadingTimeout(true);
        setLoadingTimeoutMessage('Loading is taking longer than expected. Please wait...');
      }, 10000);
    } else {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
      setLoadingTimeout(false);
      setLoadingTimeoutMessage('');
    }

    return () => {
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
    };
  }, [isLoading]);

  // Actions
  const fetchAccounts = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [ACCOUNTS_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setAccountTypes([]);
    setInstitutions([]);
    setStatuses([]);
    setDateRange(null);
    setBalanceRange(null);
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
  }, []);

  const selectAccount = useCallback((accountId: string | null) => {
    setSelectedAccountId(accountId);
  }, []);

  // Error recovery action - attempts to recover from error state
  const recoverFromError = useCallback(async () => {
    if (errorRecoveryAttempts >= 3) {
      return; // Max recovery attempts reached
    }

    setIsRecovering(true);
    setErrorRecoveryAttempts(prev => prev + 1);

    try {
      // Wait a bit before retrying
      await new Promise(resolve => setTimeout(resolve, 1000));
      await refetch();
    } finally {
      setIsRecovering(false);
    }
  }, [errorRecoveryAttempts, refetch]);

  // Return state and actions
  return {
    // Data
    accounts: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    accountTypes,
    institutions,
    statuses,
    dateRange,
    balanceRange,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Selection
    selectedAccountId,

    // Actions
    fetchAccounts,
    refresh,
    recoverFromError,
    setAccountTypes,
    setInstitutions,
    setStatuses,
    setDateRange,
    setBalanceRange,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
    selectAccount,
  };
}