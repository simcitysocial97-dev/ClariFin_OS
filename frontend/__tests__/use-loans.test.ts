/**
 * Unit tests for useLoans, useLoanSchedule, usePrepaymentSimulation hooks

 *
 * Tests cover:
 * - Initial load with empty loans
 * - Loan retrieval
 * - Loan schedule fetching
 * - Prepayment simulation
 * - Error handling
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useLoans, useLoanSchedule, usePrepaymentSimulation } from '../lib/hooks/use-loans';

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

const mockLoanData = [
  {
    id: 1,
    name: 'Home Loan',
    lender: 'SBI',
    loan_type: 'home',
    principal_paise: 30000000,
    outstanding_paise: 25000000,
    rate_bps: 850,
    tenure_months: 240,
    emi_paise: 260000,
    disbursed_date: '2024-01-15',
  },
];

describe('useLoans', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch loans successfully', async () => {
    mockApiFetch.mockResolvedValue(createMockResponse(mockLoanData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toEqual(mockLoanData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch multiple loans successfully', async () => {
    const multiLoanData = [
      { ...mockLoanData[0], outstanding_paise: 10000000 },
      { ...mockLoanData[0], id: 2, outstanding_paise: 15000000 },
    ];

    mockApiFetch.mockResolvedValue(createMockResponse(multiLoanData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.reduce((total, loan) => total + (loan.outstanding_paise ?? 0), 0)).toBe(25000000);
  });

  it('should handle empty loans list', async () => {
    mockApiFetch.mockResolvedValue(createMockResponse([]));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toHaveLength(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValue(createMockErrorResponse(500));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.isError).toBe(true);
  });

  it('should validate response schema', async () => {
    const invalidData = [
      {
        id: 'not-a-number',
      },
    ];

    mockApiFetch.mockResolvedValue(createMockResponse(invalidData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.isError).toBe(true);
  });
});

describe('useLoanSchedule', () => {
  it('should not fetch when loanId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoanSchedule(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isFetching).toBe(false);
  });

  it('should fetch schedule when loanId is provided', async () => {
    const mockSchedule = {
      loan_id: 1,
      schedule: [
        { month: 1, emi_paise: 260000, principal: 100000, interest: 160000, balance: 24900000 },
        { month: 2, emi_paise: 260000, principal: 101000, interest: 159000, balance: 24799000 },
      ],
    };

    mockApiFetch.mockResolvedValue(createMockResponse(mockSchedule));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoanSchedule('1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toEqual(mockSchedule);
  });
});

describe('usePrepaymentSimulation', () => {
  it('should not fetch when loanId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => 
      usePrepaymentSimulation(null, 500000, 'reduce_tenure'), 
      { wrapper }
    );

    expect(result.current.isLoading).toBe(false);
  });

  it('should not fetch when prepaymentPaise is 0', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => 
      usePrepaymentSimulation('1', 0, 'reduce_tenure'), 
      { wrapper }
    );

    expect(result.current.isLoading).toBe(false);
  });

  it('should fetch simulation when loanId and prepaymentPaise are provided', async () => {
    const mockSimulation = {
      original_tenure_months: 240,
      new_tenure_months: 220,
      original_emi_paise: 260000,
      new_emi_paise: 260000,
      interest_saved_paise: 1500000,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(mockSimulation));

    const wrapper = createWrapper();
    const { result } = renderHook(() => 
      usePrepaymentSimulation('1', 500000, 'reduce_tenure'), 
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess || result.current.isError).toBe(true))

    expect(result.current.data).toEqual(mockSimulation);
  });
});
