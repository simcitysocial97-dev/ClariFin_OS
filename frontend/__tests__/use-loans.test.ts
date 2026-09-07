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

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useLoans, useLoanSchedule, usePrepaymentSimulation } from '../lib/hooks/use-loans';

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

const mockLoanData = {
  loans: [
    {
      id: 1,
      name: 'Home Loan',
      lender: 'SBI',
      loan_type: 'home_loan',
      principal_paise: 30000000,
      outstanding_paise: 25000000,
      interest_rate: 8.5,
      tenure_months: 240,
      emi_paise: 260000,
      disbursed_date: '2024-01-15',
      next_emi_date: '2026-10-01',
      gold_weight_grams: null,
      gold_purity: null,
      interest_type: 'reducing',
      is_active: true,
      notes: 'Primary residence',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2026-09-01T14:30:00Z',
    },
  ],
  summary: {
    total_loans: 1,
    total_outstanding_paise: 25000000,
    total_principal_paise: 30000000,
    total_monthly_emi_paise: 260000,
  },
};

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
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockLoanData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockLoanData);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should calculate summary totals correctly', async () => {
    const multiLoanData = {
      loans: [
        { ...mockLoanData.loans[0], outstanding_paise: 10000000 },
        { ...mockLoanData.loans[0], id: 2, outstanding_paise: 15000000 },
      ],
      summary: {
        total_loans: 2,
        total_outstanding_paise: 25000000,
        total_principal_paise: 40000000,
        total_monthly_emi_paise: 450000,
      },
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(multiLoanData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.summary.total_loans).toBe(2);
    expect(result.current.data?.summary.total_outstanding_paise).toBe(25000000);
  });

  it('should handle empty loans list', async () => {
    const emptyData = {
      loans: [],
      summary: {
        total_loans: 0,
        total_outstanding_paise: 0,
        total_principal_paise: 0,
        total_monthly_emi_paise: 0,
      },
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.loans).toHaveLength(0);
    expect(result.current.data?.summary.total_loans).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoans(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      loans: [
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
    const { result } = renderHook(() => useLoans(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

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

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSchedule),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useLoanSchedule('1'), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

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

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockSimulation),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => 
      usePrepaymentSimulation('1', 500000, 'reduce_tenure'), 
      { wrapper }
    );

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockSimulation);
  });
});
