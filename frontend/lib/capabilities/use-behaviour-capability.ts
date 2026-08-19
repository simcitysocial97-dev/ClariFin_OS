/**
 * useBehaviourCapability Hook - Stage 4 Behaviour Intelligence Workspace
 *
 * React hook for behaviour state management and orchestration.
 * This is the canonical capability implementation for the Behaviour Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { BehaviourViewModel } from '@/types/behaviour-view-model';
import { behaviourMapper } from '@/lib/mappers/behaviour-mapper';
import { BehaviorScoreSchema, type BehaviorScore } from '@/lib/schemas/behavior-score';

// Query key for React Query
const BEHAVIOUR_QUERY_KEY = 'behaviour';

/**
 * Behaviour capability state interface
 */
export interface BehaviourCapabilityState {
  // Data
  behaviour: BehaviourViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  period: string;

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Behaviour capability actions interface
 */
export interface BehaviourCapabilityActions {
  // Fetch
  fetchBehaviour: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setPeriod: (period: string) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Behaviour capability return type
 */
export type BehaviourCapabilityReturn = BehaviourCapabilityState & BehaviourCapabilityActions;

/**
 * useBehaviourCapability Hook
 *
 * Provides behaviour state management and orchestration for the Behaviour Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useBehaviourCapability(): BehaviourCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [period, setPeriod] = useState<string>('');
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
    period: period || undefined,
  }), [period]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<BehaviourViewModel | null>({
    queryKey: [BEHAVIOUR_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/behaviour/wellness-score');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      const parsed = BehaviorScoreSchema.safeParse(raw);
      if (!parsed.success) {
        console.error('[useBehaviourCapability] API response validation failed:', parsed.error.issues);
        throw new Error('API response shape mismatch — check backend contract');
      }
      return behaviourMapper.mapBehavioralScoreToViewModel(parsed.data as BehaviorScore);
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
  const fetchBehaviour = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [BEHAVIOUR_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setPeriod('');
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
    behaviour: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    period,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Actions
    fetchBehaviour,
    refresh,
    recoverFromError,
    setPeriod,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
  };
}