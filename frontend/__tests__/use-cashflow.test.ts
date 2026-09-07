/**
 * Unit tests for useCashflow hook
 *
 * Tests cover:
 * - Initial load with empty cashflow
 * - Cashflow retrieval with month parameter
 * - Aggregation of income/expenses
 * - Time series trend data
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCashflow } from '../lib/hooks/use-cashflow';

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

const mockCashflowData = {
  months: [
    {
      month: '2026-01',
      income_paise: 500000,
      expenses_paise: 300000,
      net_paise: 200000,
      transaction_count: 45,
    },
    {
      month: '2026-02',
      income_paise: 520000,
      expenses_paise: 350000,
      net_paise: 170000,
      transaction_count: 42,
    },
    {
      month: '2026-03',
      income_paise: 510000,
      expenses_paise: 320000,
      net_paise: 190000,
      transaction_count: 48,
    },
  ],
  total_count: 3,
};

describe('useCashflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch cashflow with default 6 months', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCashflowData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFetch).toHaveBeenCalledWith('/api/cashflow/monthly?months=6');
    expect(result.current.data).toEqual(mockCashflowData);
  });

  it('should fetch cashflow with custom months parameter', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCashflowData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(12), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFetch).toHaveBeenCalledWith('/api/cashflow/monthly?months=12');
  });

  it('should aggregate income and expenses', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCashflowData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    const months = result.current.data?.months || [];
    const totalIncome = months.reduce((sum, m) => sum + m.income_paise, 0);
    const totalExpenses = months.reduce((sum, m) => sum + m.expenses_paise, 0);
    const totalNet = months.reduce((sum, m) => sum + m.net_paise, 0);

    expect(totalIncome).toBe(1530000);
    expect(totalExpenses).toBe(970000);
    expect(totalNet).toBe(560000);
  });

  it('should handle empty months list', async () => {
    const emptyData = {
      months: [],
      total_count: 0,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.months).toHaveLength(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });

  it('should handle negative net (expenses > income)', async () => {
    const negativeNetData = {
      months: [
        {
          month: '2026-01',
          income_paise: 300000,
          expenses_paise: 500000,
          net_paise: -200000,
          transaction_count: 30,
        },
      ],
      total_count: 1,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(negativeNetData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.months[0].net_paise).toBe(-200000);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      months: [
        {
          month: 123, // should be string
        },
      ],
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useCashflow(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });
});
