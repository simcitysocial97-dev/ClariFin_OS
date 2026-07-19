/**
 * useForecastCapability Hook - Stage 4 Forecast Intelligence Workspace
 *
 * React hook for forecast state management and orchestration.
 * This is the canonical capability implementation for the Forecast Intelligence Workspace.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import type { ForecastViewModel } from '@/types/forecast-view-model';
import { forecastMapper } from '@/lib/mappers/forecast-mapper';

// Query key for React Query
const FORECAST_QUERY_KEY = 'forecast';

/**
 * Forecast capability state interface
 */
export interface ForecastCapabilityState {
  // Data
  forecast: ForecastViewModel | null;
  loading: boolean;
  error: Error | null;

  // Loading timeout
  loadingTimeout: boolean;
  loadingTimeoutMessage: string;

  // Error recovery
  errorRecoveryAttempts: number;
  isRecovering: boolean;

  // Filters
  horizon: number;
  scenarios: string[];
  metricTypes: string[];

  // Evidence drawer
  isEvidenceDrawerOpen: boolean;
}

/**
 * Forecast capability actions interface
 */
export interface ForecastCapabilityActions {
  // Fetch
  fetchForecast: () => Promise<void>;
  refresh: () => Promise<void>;
  recoverFromError: () => Promise<void>;

  // Filters
  setHorizon: (horizon: number) => void;
  setScenarios: (scenarios: string[]) => void;
  setMetricTypes: (metricTypes: string[]) => void;
  clearFilters: () => void;
  applyFilters: () => Promise<void>;

  // Evidence drawer
  toggleEvidenceDrawer: () => void;
}

/**
 * Forecast capability return type
 */
export type ForecastCapabilityReturn = ForecastCapabilityState & ForecastCapabilityActions;

/**
 * useForecastCapability Hook
 *
 * Provides forecast state management and orchestration for the Forecast Intelligence Workspace.
 * Uses React Query for data fetching and caching.
 */
export function useForecastCapability(): ForecastCapabilityReturn {
  const queryClient = useQueryClient();

  // State
  const [horizon, setHorizon] = useState<number>(12);
  const [scenarios, setScenarios] = useState<string[]>([]);
  const [metricTypes, setMetricTypes] = useState<string[]>([]);
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
    horizon: horizon || undefined,
    scenarios: scenarios.length > 0 ? scenarios.join(',') : undefined,
    metric_types: metricTypes.length > 0 ? metricTypes.join(',') : undefined,
  }), [horizon, scenarios, metricTypes]);

  // React Query for data fetching
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery<ForecastViewModel | null>({
    queryKey: [FORECAST_QUERY_KEY, queryParams],
    queryFn: async () => {
      const response = await fetch('/api/v1/forecast');
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }
      const raw = await response.json();
      return forecastMapper.mapForecastDTO(raw);
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
  const fetchForecast = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const refresh = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: [FORECAST_QUERY_KEY] });
  }, [queryClient]);

  const clearFilters = useCallback(() => {
    setHorizon(12);
    setScenarios([]);
    setMetricTypes([]);
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
    forecast: data ?? null,
    loading: isLoading,
    error: error as Error | null,

    // Loading timeout
    loadingTimeout,
    loadingTimeoutMessage,

    // Error recovery
    errorRecoveryAttempts,
    isRecovering,

    // Filters
    horizon,
    scenarios,
    metricTypes,

    // Evidence drawer
    isEvidenceDrawerOpen,

    // Actions
    fetchForecast,
    refresh,
    recoverFromError,
    setHorizon,
    setScenarios,
    setMetricTypes,
    clearFilters,
    applyFilters,
    toggleEvidenceDrawer,
  };
}