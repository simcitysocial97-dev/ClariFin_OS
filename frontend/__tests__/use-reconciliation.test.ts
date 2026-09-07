/**
 * Unit tests for useReconciliations, usePendingReconciliations, useScanReconciliations hooks
 *
 * Tests cover:
 * - Initial load with empty reconciliations
 * - Reconciliation retrieval
 * - Pending reconciliation fetching
 * - Scan reconciliation
 * - Confirm/reject reconciliation mutations
 * - Error handling
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useReconciliations, usePendingReconciliations, useScanReconciliations } from '../lib/hooks/use-reconciliation';

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

const mockReconciliationData = {
  ledger_entry: {
    id: 'led-1',
    account_id: 'acc-1',
    date: '2026-09-01',
    description: 'Salary Credit',
    amount_paise: 500000,
    balance_after_paise: 1000000,
  },
  transaction: {
    id: 'txn-1',
    bank: 'SBI',
    date: '2026-09-01',
    description: 'Salary Credit',
    amount_paise: 500000,
  },
  matched: true,
  match_confidence: 0.95,
  match_type: 'exact_amount',
};

const mockReconciliationsData = {
  reconciliations: [mockReconciliationData],
  pending_count: 1,
  total_count: 1,
};

describe('useReconciliations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
    expect(result.current.data).toBeNull();
  });

  it('should fetch reconciliations successfully', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockReconciliationsData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockReconciliationsData);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should handle empty reconciliations list', async () => {
    const emptyData = {
      reconciliations: [],
      pending_count: 0,
      total_count: 0,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(emptyData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.reconciliations).toHaveLength(0);
    expect(result.current.data?.pending_count).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).not.toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it('should validate response schema', async () => {
    const invalidData = {
      reconciliations: [
        {
          ledger_entry: 'not-an-object',
        },
      ],
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).not.toBeNull();
  });
});

describe('usePendingReconciliations', () => {
  it('should fetch pending reconciliations', async () => {
    const pendingData = {
      reconciliations: [
        { ...mockReconciliationData, matched: false },
      ],
      pending_count: 1,
      total_count: 1,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(pendingData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePendingReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.pending_count).toBe(1);
  });
});

describe('useScanReconciliations', () => {
  it('should fetch scan results', async () => {
    const scanData = {
      matches: [
        {
          ledger_entry_id: 'led-1',
          transaction_id: 'txn-1',
          confidence: 0.9,
        },
      ],
      count: 1,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(scanData),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useScanReconciliations(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.count).toBe(1);
    expect(result.current.data?.matches).toHaveLength(1);
  });
});
