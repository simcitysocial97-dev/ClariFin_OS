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

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useInvestments } from '../lib/hooks/use-investments';

vi.mock('@/lib/api/gateway', () => ({
  apiFetch: vi.fn(),
}));

import { apiFetch } from '@/lib/api/gateway';
import { createMockResponse, createMockErrorResponse } from './utils/createMockResponse';
const mockApiFetch = vi.mocked(apiFetch);

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: 0,
      },
    },
  });
  const Wrapper = ({ children }: { children: React.ReactNode }) => React.createElement(
    QueryClientProvider, { client: queryClient }, children
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
};

const mockInvestment = {
  id: '1',
  name: 'Mutual Fund A',
  type: 'mutual_funds',
  institution: 'Zerodha',
  current_value_paise: 1200000,
  invested_paise: 1000000,
  returns_paise: 200000,
  returns_percentage: 20,
  returns_ytd_bps: 2000,
  status: 'active' as const,
};

const mockInvestmentsData = {
  investments: [mockInvestment],
  total_value_paise: 1200000,
  total_invested_paise: 1000000,
  total_returns_paise: 200000,
  investment_count: 1,
  insights: [],
  evidence_chain: null,
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
    mockApiFetch.mockResolvedValue(createMockResponse(mockInvestmentsData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toEqual(mockInvestmentsData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should calculate portfolio gain correctly', async () => {
    const multiInvestmentData = {
      investments: [
        { ...mockInvestment, invested_paise: 1000000, current_value_paise: 1200000, returns_paise: 200000, returns_percentage: 20 },
        { ...mockInvestment, id: '2', invested_paise: 500000, current_value_paise: 450000, returns_paise: -50000, returns_percentage: -10 },
      ],
      total_value_paise: 1650000,
      total_invested_paise: 1500000,
      total_returns_paise: 150000,
      investment_count: 2,
      insights: [],
      evidence_chain: null,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(multiInvestmentData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data?.total_invested_paise).toBe(1500000);
    expect(result.current.data?.total_value_paise).toBe(1650000);
    expect(result.current.data?.total_returns_paise).toBe(150000);
  });

  it('should track holdings by type', async () => {
    const diversifiedData = {
      investments: [
        { ...mockInvestment, type: 'stocks', invested_paise: 1000000 },
        { ...mockInvestment, id: '2', type: 'bonds', invested_paise: 500000 },
        { ...mockInvestment, id: '3', type: 'stocks', invested_paise: 2000000 },
      ],
      total_value_paise: 3500000,
      total_invested_paise: 3500000,
      total_returns_paise: 0,
      investment_count: 3,
      insights: [],
      evidence_chain: null,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(diversifiedData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data?.investments.map((investment) => investment.type)).toEqual([
      'stocks',
      'bonds',
      'stocks',
    ]);
  });

  it('should handle empty investments list', async () => {
    const emptyData = {
      investments: [],
      total_value_paise: 0,
      total_invested_paise: 0,
      total_returns_paise: 0,
      investment_count: 0,
      insights: [],
      evidence_chain: null,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(emptyData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data?.investments).toHaveLength(0);
    expect(result.current.data?.investment_count).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValue(createMockErrorResponse(500));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

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

    mockApiFetch.mockResolvedValue(createMockResponse(invalidData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useInvestments(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.isError).toBe(true);
  });
});
