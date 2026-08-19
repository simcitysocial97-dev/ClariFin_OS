/**
 * useCreditCardsCapability Hook - Stage 4 Credit Cards Intelligence Workspace
 *
 * React hook for credit cards state management and orchestration.
 * This is the canonical capability implementation for the Credit Cards Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { CreditCardsViewModel } from '@/types/credit-cards-view-model';
import { creditCardsMapper } from '@/lib/mappers/credit-cards-mapper';

// Query key for React Query
const CREDIT_CARDS_QUERY_KEY = 'credit-cards';

/**
 * Credit Cards capability state interface
 */
export interface CreditCardsCapabilityState {
  // Data
  creditCards: CreditCardsViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  statuses: string[];
  banks: string[];

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;

  // Selected card
  selectedCardId: string | null;
}

/**
 * Credit Cards capability actions interface
 */
export interface CreditCardsCapabilityActions {
  // Fetch
  fetchCreditCards: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setStatuses: (statuses: string[]) => void;
  setBanks: (banks: string[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;

  // Selection
  selectCard: (cardId: string | null) => void;
}

/**
 * Credit Cards capability return type
 */
export type CreditCardsCapabilityReturn = CreditCardsCapabilityState & CreditCardsCapabilityActions;

/**
 * useCreditCardsCapability Hook
 *
 * Provides credit cards state management and orchestration for the Credit Cards Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useCreditCardsCapability(): CreditCardsCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [statuses, setStatuses] = useState<string[]>([]);
  const [banks, setBanks] = useState<string[]>([]);
  const [isEvidenceDrawerOpen, setIsEvidenceDrawerOpen] = useState<boolean>(false);
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);

  // Loading timeout state
  const [loadingTimeout, setLoadingTimeout] = useState<boolean>(false);
  const [loadingTimeoutMessage, setLoadingTimeoutMessage] = useState<string>('');
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Error recovery state
  const [errorRecoveryAttempts, setErrorRecoveryAttempts] = useState<number>(0);
  const [isRecovering, setIsRecovering] = useState<boolean>(false);

  // Build query parameters from state
  const queryParams = useMemo(() => ({
    statuses: statuses.length > 0 ? statuses.join(',') : undefined,
    banks: banks.length > 0 ? banks.join(',') : undefined,
  }), [statuses, banks]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<CreditCardsViewModel | null>({
    queryKey: [CREDIT_CARDS_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/credit-cards');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return creditCardsMapper.mapCreditCardsDTO(raw);
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
  const fetchCreditCards = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [CREDIT_CARDS_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setStatuses([]);
    setBanks([]);
  }, []);

  const applyFilters = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const toggleEvidenceDrawer = useCallback(() => {
    setIsEvidenceDrawerOpen(prev => !prev);
  }, []);

  const selectCard = useCallback((cardId: string | null) => {
    setSelectedCardId(cardId);
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
    creditCards: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    statuses,
    banks,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Selection
    selectedCardId,

    // Actions
    fetchCreditCards,
    refresh,
    recoverFromError,
    setStatuses,
    setBanks,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
    selectCard,
  };
}