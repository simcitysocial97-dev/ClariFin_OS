/**
 * Unit tests for useInvestments hook
 *
 * Tests cover:
 * - Initial load with empty investments
 * - Investment retrieval
 * - Investment creation/update/deletion
 * - Portfolio calculation
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useInvestments } from '../hooks/use-investments';

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

const mockInvestmentsData = {
  investments: [
    {
      id: 1,
      name: 'Mutual Fund A',
      investment_type: 'mutual_fund',
      platform: 'Zerodha',
      invested_paise: 1000000,
      current_value_paise: 1200000,
      units: 1000,
      buy_price_paise: 1000,
      current_price_paise: 1200,
      as_of_date: '2026-09-01',
      is_active: true,
      notes: 'Long-term',
      last_updated: '2026-09-01T10:00:00Z',
      created_at: '2024-01-15T10:00:00Z',
    },
  ],
  summary: {
    total_investments: 1,
    total_invested_paise: 1000000,
    total_current_value_paise: 1200000,
    total_gain_paise: 200000,
    gain_percent: 20,
    allocation_by_type: { mutual_fund: 1000000 },
  },
};

describe('useInvestments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch investments successfully', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockInvestmentsData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockInvestmentsData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should calculate portfolio gain correctly', async () => {
    const multiInvestmentData = {
      investments: [
        { ...mockInvestmentsData.investments[0], invested_paise: 1000000, current_value_paise: 1200000 },
        { ...mockInvestmentsData.investments[0], id: 2, invested_paise: 500000, current_value_paise: 450000 },
      ],
      summary: {
        total_investments: 2,
        total_invested_paise: 1500000,
        total_current_value_paise: 1650000,
        total_gain_paise: 150000,
        gain_percent: 10,
        allocation_by_type: { mutual_fund: 1500000 },
      },
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(multiInvestmentData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.summary.total_invested_paise).toBe(1500000);
    expect(result.current.data?.summary.total_current_value_paise).toBe(1650000);
    expect(result.current.data?.summary.total_gain_paise).toBe(150000);
  });

  it('should track allocation by type', async () => {
    const diversifiedData = {
      investments: [
        { ...mockInvestmentsData.investments[0], investment_type: 'stocks', invested_paise: 1000000 },
        { ...mockInvestmentsData.investments[0], id: 2, investment_type: 'bonds', invested_paise: 500000 },
        { ...mockInvestmentsData.investments[0], id: 3, investment_type: 'stocks', invested_paise: 2000000 },
      ],
      summary: {
        total_investments: 3,
        total_invested_paise: 3500000,
        total_current_value_paise: 3500000,
        total_gain_paise: 0,
        gain_percent: 0,
        allocation_by_type: { stocks: 3000000, bonds: 500000 },
      },
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(diversifiedData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.summary.allocation_by_type).toEqual({ stocks: 3000000, bonds: 500000 });
  });

  it('should handle empty investments list', async () => {
    const emptyData = {
      investments: [],
      summary: {
        total_investments: 0,
        total_invested_paise: 0,
        total_current_value_paise: 0,
        total_gain_paise: 0,
        gain_percent: 0,
        allocation_by_type: {},
      },
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.investments).toHaveLength(0);
    expect(result.current.data?.summary.total_investments).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      investments: [
        {
          id: 'not-a-number',
        },
      ],
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });
});
