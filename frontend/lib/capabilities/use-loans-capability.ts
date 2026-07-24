/**
 * useLoansCapability Hook - Stage 4 Loans Intelligence Workspace
 *
 * React hook for loans state management and orchestration.
 * This is the canonical capability implementation for the Loans Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { LoansViewModel } from '@/types/loans-view-model';
import { loansMapper } from '@/lib/mappers/loans-mapper';

// Query key for React Query
const LOANS_QUERY_KEY = 'loans';

/**
 * Loans capability state interface
 */
export interface LoansCapabilityState {
  // Data
  loans: LoansViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  loanTypes: string[];
  lenders: string[];
  statuses: string[];

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected loan
  selectedLoanId: string | null;
}

/**
 * Loans capability actions interface
 */
export interface LoansCapabilityActions {
  // Fetch
  fetchLoans: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setLoanTypes: (types: string[]) => void;
  setLenders: (lenders: string[]) => void;
  setStatuses: (statuses: string[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectLoan: (loanId: string | null) => void;
}

/**
 * Loans capability return type
 */
export type LoansCapabilityReturn = LoansCapabilityState & LoansCapabilityActions;

/**
 * useLoansCapability Hook
 *
 * Provides loans state management and orchestration for the Loans Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useLoansCapability(): LoansCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [loanTypes, setLoanTypes] = useState<string[]>([]);
  const [lenders, setLenders] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedLoanId, setSelectedLoanId] = useState<string | null>(null);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    loan_types: loanTypes.length > 0 ? loanTypes.join(',') : undefined,
    lenders: lenders.length > 0 ? lenders.join(',') : undefined,
    statuses: statuses.length > 0 ? statuses.join(',') : undefined,
  }), [loanTypes, lenders, statuses]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<LoansViewModel | null>({
    queryKey: [LOANS_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/loans');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return loansMapper.mapLoansDTO(raw);
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
  const fetchLoans = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [LOANS_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setLoanTypes([]);
    setLenders([]);
    setStatuses([]);
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
  }, []);

  const selectLoan = useCallback((loanId: string | null) => {
    setSelectedLoanId(loanId);
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
    loans: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    loanTypes,
    lenders,
    statuses,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Selection
    selectedLoanId,

    // Actions
    fetchLoans,
    refresh,
    recoverFromError,
    setLoanTypes,
    setLenders,
    setStatuses,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
    selectLoan,
  };
}