/**
 * useCashflowCapability Hook - Stage 4 Cashflow Truth Workspace
 *
 * React hook for cashflow state management and orchestration.
 * This is the canonical capability implementation for the Cashflow Truth Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { CashflowViewModel } from '@/types/cashflow-view-model';
import { cashflowMapper } from '@/lib/mappers/cashflow-mapper';

// Query key for React Query
const CASHFLOW_QUERY_KEY = 'cashflow';

/**
 * Cashflow capability state interface
 */
export interface CashflowCapabilityState {
  // Data
  cashflow: CashflowViewModel | null;
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
  categories: string[];
  merchants: string[];
  amountRange: { min?: number; max?: number } | null;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Cashflow capability actions interface
 */
export interface CashflowCapabilityActions {
  // Fetch
  fetchCashflow: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setDateRange: (filter: { from?: string; to?: string } | null) => void;
  setCategories: (categories: string[]) => void;
  setMerchants: (merchants: string[]) => void;
  setAmountRange: (range: { min?: number; max?: number } | null) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Cashflow capability return type
 */
export type CashflowCapabilityReturn = CashflowCapabilityState & CashflowCapabilityActions;

/**
 * useCashflowCapability Hook
 *
 * Provides cashflow state management and orchestration for the Cashflow Truth Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useCashflowCapability(): CashflowCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [dateRange, setDateRange] = useState<{ from?: string; to?: string } | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [merchants, setMerchants] = useState<string[]>([]);
  const [amountRange, setAmountRange] = useState<{ min?: number; max?: number } | null>(null);
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
    categories: categories.length > 0 ? categories.join(',') : undefined,
    merchants: merchants.length > 0 ? merchants.join(',') : undefined,
    amount_min: amountRange?.min,
    amount_max: amountRange?.max,
  }), [dateRange, categories, merchants, amountRange]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<CashflowViewModel | null>({
    queryKey: [CASHFLOW_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/cashflow');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return cashflowMapper.mapCashflowDTO(raw);
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
  const fetchCashflow = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [CASHFLOW_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setDateRange(null);
    setCategories([]);
    setMerchants([]);
    setAmountRange(null);
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
    cashflow: data ?? null,
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
    categories,
    merchants,
    amountRange,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Actions
    fetchCashflow,
    refresh,
    recoverFromError,
    setDateRange,
    setCategories,
    setMerchants,
    setAmountRange,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
  };
}