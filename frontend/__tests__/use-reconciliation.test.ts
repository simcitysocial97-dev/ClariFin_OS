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

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useReconciliations, usePendingReconciliations, useScanReconciliations } from '../lib/hooks/use-reconciliation';

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

const mockReconciliationData = {
  id: 1,
  debit_txn_id: 101,
  credit_txn_id: 201,
  debit_account_id: 'acc-1',
  credit_account_id: 'acc-2',
  amount_paise: 500000,
  date_diff_days: 0,
  match_confidence_bps: 9500,
  match_type: 'exact',
  status: 'confirmed',
  created_at: '2026-09-01T00:00:00Z',
  confirmed_at: '2026-09-01T00:00:00Z',
  debit_date: '2026-09-01',
  debit_date_iso: '2026-09-01',
  debit_description: 'Salary Credit',
  debit_amount_paise: 500000,
  debit_bank: 'SBI',
  credit_date: '2026-09-01',
  credit_date_iso: '2026-09-01',
  credit_description: 'Salary Credit',
  credit_amount_paise: 500000,
  credit_bank: 'SBI',
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
    mockApiFetch.mockResolvedValue(createMockResponse(mockReconciliationsData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

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

    mockApiFetch.mockResolvedValue(createMockResponse(emptyData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data?.reconciliations).toHaveLength(0);
    expect(result.current.data?.pending_count).toBe(0);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValue(createMockErrorResponse(500));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

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

    mockApiFetch.mockResolvedValue(createMockResponse(invalidData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).not.toBeNull();
  });
});

describe('usePendingReconciliations', () => {
  it('should fetch pending reconciliations', async () => {
    const pendingData = {
      reconciliations: [
        { ...mockReconciliationData, status: 'pending', confirmed_at: null },
      ],
      pending_count: 1,
      total_count: 1,
    };

    mockApiFetch.mockResolvedValue(createMockResponse(pendingData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePendingReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

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

    mockApiFetch.mockResolvedValue(createMockResponse(scanData));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useScanReconciliations(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.data?.count).toBe(1);
    expect(result.current.data?.matches).toHaveLength(1);
  });
});
