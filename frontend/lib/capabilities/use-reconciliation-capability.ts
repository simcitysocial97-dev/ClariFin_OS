/**
 * useReconciliationCapability Hook - Stage 4 Reconciliation Intelligence Workspace
 *
 * React hook for reconciliation state management and orchestration.
 * This is the canonical capability implementation for the Reconciliation Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { ReconciliationViewModel } from '@/types/reconciliation-view-model';
import { reconciliationMapper } from '@/lib/mappers/reconciliation-mapper';

// Query key for React Query
const RECONCILIATION_QUERY_KEY = 'reconciliation';

/**
 * Reconciliation capability state interface
 */
export interface ReconciliationCapabilityState {
  // Data
  reconciliation: ReconciliationViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  status: string[];
  banks: string[];

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected discrepancy
  selectedDiscrepancyId: number | null;
}

/**
 * Reconciliation capability actions interface
 */
export interface ReconciliationCapabilityActions {
  // Fetch
  fetchReconciliation: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setStatus: (status: string[]) => void;
  setBanks: (banks: string[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectDiscrepancy: (discrepancyId: number | null) => void;
}

/**
 * Reconciliation capability return type
 */
export type ReconciliationCapabilityReturn = ReconciliationCapabilityState & ReconciliationCapabilityActions;

/**
 * useReconciliationCapability Hook
 *
 * Provides reconciliation state management and orchestration for the Reconciliation Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useReconciliationCapability(): ReconciliationCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [status, setStatus] = useState<string[]>([]);
  const [banks, setBanks] = useState<string[]>([]);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedDiscrepancyId, setSelectedDiscrepancyId] = useState<number | null>(null);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    status: status.length > 0 ? status.join(',') : undefined,
    banks: banks.length > 0 ? banks.join(',') : undefined,
  }), [status, banks]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<ReconciliationViewModel | null>({
    queryKey: [RECONCILIATION_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/reconciliation');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return reconciliationMapper.mapReconciliationDTO(raw);
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
  const fetchReconciliation = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [RECONCILIATION_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setStatus([]);
    setBanks([]);
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
  }, []);

  const selectDiscrepancy = useCallback((discrepancyId: number | null) => {
    setSelectedDiscrepancyId(discrepancyId);
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
    reconciliation: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    status,
    banks,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Selection
    selectedDiscrepancyId,

    // Actions
    fetchReconciliation,
    refresh,
    recoverFromError,
    setStatus,
    setBanks,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
    selectDiscrepancy,
  };
}