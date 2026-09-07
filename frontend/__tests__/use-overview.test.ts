/**
 * Unit tests for useOverview hook
 *
 * Tests cover:
 * - Initial load state
 * - Overview retrieval
 * - Summary rendering
 * - Key metric display
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useOverview } from '../lib/hooks/use-overview';

const mockApiFetch = vi.fn();
vi.mock('@/lib/api/gateway', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

const createWrapper = () => {
  const queryClient = new QueryClient();
  const Wrapper = ({ children }: { children: React.ReactNode }) => React.createElement(
    QueryClientProvider, { client: queryClient }, children
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
};

const mockOverviewData = {
  total_spend: 50000,
  total_spend_display: '₹500.00',
  this_month: 8000,
  this_month_display: '₹80.00',
  last_month: 7000,
  last_month_display: '₹70.00',
  month_change: '+14.3%',
  transaction_count: 145,
  card_count: 3,
  months_of_data: 6,
  monthly_average: 8333,
  monthly_average_display: '₹83.33',
  above_below_avg: 'below',
  above_avg_is_bad: true,
  monthly_chart: [
    { month: '2026-01', amount: 7000 },
    { month: '2026-02', amount: 8500 },
    { month: '2026-03', amount: 8000 },
  ],
  category_chart: [
    { name: 'Food', value: 3000 },
    { name: 'Transport', value: 2000 },
  ],
  bank_chart: [
    { bank: 'HDFC', amount: 5000 },
  ],
  recent_transactions: [],
  behavioral_insights: [
    {
      title: 'High food spending',
      description: 'Food expenses are 20% above average',
      severity: 'warning' as const,
      icon: 'utensils',
    },
  ],
};

describe('useOverview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch overview successfully', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockOverviewData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockOverviewData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should display key metrics', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockOverviewData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.total_spend).toBe(50000);
    expect(result.current.data?.month_change).toBe('+14.3%');
    expect(result.current.data?.transaction_count).toBe(145);
  });

  it('should render monthly chart data', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockOverviewData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.monthly_chart).toHaveLength(3);
    expect(result.current.data?.category_chart).toHaveLength(2);
    expect(result.current.data?.bank_chart).toHaveLength(1);
  });

  it('should display behavioral insights', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockOverviewData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.behavioral_insights).toHaveLength(1);
    expect(result.current.data?.behavioral_insights[0].severity).toBe('warning');
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      total_spend: 'not-a-number',
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOverview(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });
});
