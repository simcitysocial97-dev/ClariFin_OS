/**
 * Consolidated Dashboard Metrics Hook
 * Uses the existing /api/dashboard/summary endpoint
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useMemo } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface DashboardData {
  net_cash_flow: number;
  savings_rate: number;
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
}

async function fetchDashboardSummary(): Promise<DashboardData> {
  const res = await fetch(`${API_BASE}/api/dashboard/summary`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
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
  }), [result, refetch]);
}