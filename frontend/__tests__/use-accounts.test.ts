/**
 * Unit tests for useManagedAccounts hook — M9-C68 migrated to /api/v1/accounts
 *
 * Tests cover:
 * - Initial load state
 * - Account retrieval from v1 endpoint
 * - Error handling for API failures
 * - Schema validation
 * - Response wrapping (v1 returns array, hook wraps to {accounts, total})
 */

import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useManagedAccounts } from '../lib/hooks/use-accounts';

const mockApiFetch = vi.fn();
vi.mock('@/lib/api/gateway', () => ({
  apiFetch: (...args: unknown[]) => mockApiFetch(...args),
}));

const createWrapper = () => {
  const queryClient = new QueryClient();
  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
};

const mockV1Response = [
  {
    id: 'acc-1',
    name: 'Sample Account',
    type: 'savings',
    institution: 'Bank X',
    balance_paise: 150000,
    currency: 'INR',
    status: 'active',
    account_number_last4: '1234',
    opened_date: '2026-01-15T10:00:00Z',
    closed_date: null,
    notes: 'Primary account',
  },
];

describe('useManagedAccounts (v1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch accounts from /api/v1/accounts and wrap response', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockV1Response),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(mockApiFetch).toHaveBeenCalledWith('/api/v1/accounts');
    expect(result.current.data).toEqual({
      accounts: mockV1Response,
      total: 1,
    });
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it('should handle API failure', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: false,
      json: () => Promise.resolve({}),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.data).toBeUndefined();
  });

  it('should handle network error', async () => {
    mockApiFetch.mockRejectedValueOnce(new Error('Network unavailable'));

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
    expect(result.current.error).toBeDefined();
  });

  it('should validate v1 response schema and reject malformed data', async () => {
    const invalidResponse = [
      {
        id: 'acc-1',
        name: 123,
      },
    ];

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(invalidResponse),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isError).toBe(true);
  });

  it('should fetch empty accounts list', async () => {
    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([]),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data?.accounts).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });
});
