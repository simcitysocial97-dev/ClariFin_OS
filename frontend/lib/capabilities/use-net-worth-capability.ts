/**
 * useNetWorthCapability Hook - Stage 4 Net Worth Intelligence Workspace
 *
 * React hook for net worth state management and orchestration.
 * This is the canonical capability implementation for the Net Worth Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { NetWorthViewModel } from '@/types/net-worth-view-model';
import { netWorthMapper } from '@/lib/mappers/net-worth-mapper';

// Query key for React Query
const NET_WORTH_QUERY_KEY = 'netWorth';

/**
 * Net Worth capability state interface
 */
export interface NetWorthCapabilityState {
  // Data
  netWorth: NetWorthViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  dateRange: { from?: string; to?: string } | null;
  accountTypes: string[];
  period: string;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Net Worth capability actions interface
 */
export interface NetWorthCapabilityActions {
  // Fetch
  fetchNetWorth: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setDateRange: (filter: { from?: string; to?: string } | null) => void;
  setAccountTypes: (types: string[]) => void;
  setPeriod: (period: string) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Net Worth capability return type
 */
export type NetWorthCapabilityReturn = NetWorthCapabilityState & NetWorthCapabilityActions;

/**
 * useNetWorthCapability Hook
 *
 * Provides net worth state management and orchestration for the Net Worth Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useNetWorthCapability(): NetWorthCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [dateRange, setDateRange] = useState<{ from?: string; to?: string } | null>(null);
  const [accountTypes, setAccountTypes] = useState<string[]>([]);
  const [period, setPeriod] = useState<string>('1M');
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    date_range: dateRange ? `${dateRange.from},${dateRange.to}` : undefined,
    account_types: accountTypes.length > 0 ? accountTypes.join(',') : undefined,
    period,
  }), [dateRange, accountTypes, period]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<NetWorthViewModel | null>({
    queryKey: [NET_WORTH_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/net-worth');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return netWorthMapper.mapNetWorthDTO(raw);
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
  const fetchNetWorth = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [NET_WORTH_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setDateRange(null);
    setAccountTypes([]);
    setPeriod('1M');
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
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
    netWorth: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    dateRange,
    accountTypes,
    period,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Actions
    fetchNetWorth,
    refresh,
    recoverFromError,
    setDateRange,
    setAccountTypes,
    setPeriod,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
  };
}