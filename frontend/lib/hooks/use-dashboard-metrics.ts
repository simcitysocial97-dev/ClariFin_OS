/**
 * Consolidated Dashboard Metrics Hook
 * Uses the existing /api/v1/financial-intelligence/outlook endpoint
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';

import { ForecastingResponseSchema } from '../contracts/api/forecasting';
import { mapForecastingToModel } from '../mappers/forecasting';
import type { ForecastingModel } from '../models/forecasting';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DashboardData {
  // Canonical paise fields
  net_cash_flow_paise: number;
  total_income_paise: number;
  total_expenses_paise: number;
  // Deprecated rupees field (for backward compatibility)
  net_cash_flow_rupees?: number;
  // Other fields
  savings_rate: number;
  emi_paise: number;
  emi_ratio: number;
  buffer_days: number;
  financial_health_score: number;
  seven_day_trend: number;
  category_drift_alert: string | null;
  recent_transactions: any[];
}

interface HookState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  dataUpdatedAt: number;
}

async function fetchDashboardSummary(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/api/dashboard/summary`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function fetchForecasting(): Promise<ForecastingModel> {
  const res = await fetch(`${API_BASE}/api/v1/financial-intelligence/outlook`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  const dto = ForecastingResponseSchema.parse(await res.json());
  return mapForecastingToModel(dto);
}

export function useDashboardMetrics(): HookState<DashboardData> {
  const queryClient = useQueryClient();

  const result = useQuery<DashboardData, Error>({
    queryKey: ['dashboard', 'summary'],
    queryFn: fetchDashboardSummary,
    staleTime: 30_000,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] });
  };

  return useMemo(() => ({
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    refetch,
    dataUpdatedAt: result.dataUpdatedAt,
  }), [result, refetch]);
}

export function useForecasting() {
  return useQuery<ForecastingModel, Error>({
    queryKey: ['forecasting', 'outlook'],
    queryFn: fetchForecasting,
    staleTime: 30_000,
  });
}
