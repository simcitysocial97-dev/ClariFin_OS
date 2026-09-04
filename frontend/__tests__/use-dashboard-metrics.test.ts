/**
 * Unit tests for useDashboardMetrics hook
 *
 * Tests cover:
 * - Initial load state
 * - Dashboard metrics retrieval
 * - KPI computation
 * - Metric rendering
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useDashboardMetrics } from '../hooks/use-dashboard-metrics';

const mockApiFetch = vi.fn();
vi.mock('@/lib/api/gateway', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

const createWrapper = () => {
  const queryClient = new QueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

const mockDashboardMetrics = {
  net_cash_flow_paise: 200000,
  total_income_paise: 500000,
  total_expenses_paise: 300000,
  emi_paise: 50000,
  savings_rate: 0.4,
  emi_ratio: 0.1,
  buffer_days: 15,
  financial_health_score: 85,
  recent_transactions: [],
};

describe('useDashboardMetrics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it('should fetch dashboard metrics successfully', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockDashboardMetrics);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should compute cash flow correctly', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.net_cash_flow_paise).toBe(200000);
    expect(result.current.data?.total_income_paise).toBe(500000);
    expect(result.current.data?.total_expenses_paise).toBe(300000);
  });

  it('should calculate savings rate correctly', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.savings_rate).toBe(0.4);
  });

  it('should calculate EMI ratio correctly', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.emi_ratio).toBe(0.1);
    expect(result.current.data?.emi_paise).toBe(50000);
  });

  it('should show buffer days metric', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.buffer_days).toBe(15);
  });

  it('should display financial health score', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.financial_health_score).toBe(85);
  });

  it('should handle null financial health score', async () => {
    const metricsWithNullScore = {
      ...mockDashboardMetrics,
      financial_health_score: null,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(metricsWithNullScore),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.financial_health_score).toBeNull();
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      net_cash_flow_paise: 'not-a-number',
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).not.toBeNull();
  });

  it('should refetch on demand', async () => {
    mockApiFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockDashboardMetrics),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useDashboardMetrics(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFetch).toHaveBeenCalledTimes(2);
  });
});
