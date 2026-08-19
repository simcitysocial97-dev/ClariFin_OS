/**
 * useInvestmentsCapability Hook - Stage 4 Investments Intelligence Workspace
 *
 * React hook for investments state management and orchestration.
 * This is the canonical capability implementation for the Investments Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { InvestmentsViewModel } from '@/types/investments-view-model';
import { investmentsMapper } from '@/lib/mappers/investments-mapper';

// Query key for React Query
const INVESTMENTS_QUERY_KEY = 'investments';

/**
 * Investments capability state interface
 */
export interface InvestmentsCapabilityState {
  // Data
  investments: InvestmentsViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  investmentTypes: string[];
  institutions: string[];
  statuses: string[];

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected investment
  selectedInvestmentId: string | null;
}

/**
 * Investments capability actions interface
 */
export interface InvestmentsCapabilityActions {
  // Fetch
  fetchInvestments: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setInvestmentTypes: (types: string[]) => void;
  setInstitutions: (institutions: string[]) => void;
  setStatuses: (statuses: string[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectInvestment: (investmentId: string | null) => void;
}

/**
 * Investments capability return type
 */
export type InvestmentsCapabilityReturn = InvestmentsCapabilityState & InvestmentsCapabilityActions;

/**
 * useInvestmentsCapability Hook
 *
 * Provides investments state management and orchestration for the Investments Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useInvestmentsCapability(): InvestmentsCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [investmentTypes, setInvestmentTypes] = useState<string[]>([]);
  const [institutions, setInstitutions] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedInvestmentId, setSelectedInvestmentId] = useState<string | null>(null);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    investment_types: investmentTypes.length > 0 ? investmentTypes.join(',') : undefined,
    institutions: institutions.length > 0 ? institutions.join(',') : undefined,
    statuses: statuses.length > 0 ? statuses.join(',') : undefined,
  }), [investmentTypes, institutions, statuses]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<InvestmentsViewModel | null>({
    queryKey: [INVESTMENTS_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/investments');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return investmentsMapper.mapInvestmentsDTO(raw);
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes (React Query v5 uses gcTime instead of cacheTime)
    retry: 1,
    retryDelay: 1000,
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
  const fetchInvestments = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [INVESTMENTS_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setInvestmentTypes([]);
    setInstitutions([]);
    setStatuses([]);
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
  }, []);

  const selectInvestment = useCallback((investmentId: string | null) => {
    setSelectedInvestmentId(investmentId);
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
    investments: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    investmentTypes,
    institutions,
    statuses,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Selection
    selectedInvestmentId,

    // Actions
    fetchInvestments,
    refresh,
    recoverFromError,
    setInvestmentTypes,
    setInstitutions,
    setStatuses,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
    selectInvestment,
  };
}