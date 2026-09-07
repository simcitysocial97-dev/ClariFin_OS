/**
 * Unit tests for useManagedAccounts hook
 *
 * Tests cover:
 * - Initial load state
 * - Account retrieval
 * - Error handling for API failures
 * - Schema validation
 */

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
  const Wrapper = ({ children }: { children: React.ReactNode }) => React.createElement(
    QueryClientProvider, { client: queryClient }, children
  );
  Wrapper.displayName = 'TestQueryClientWrapper';
  return Wrapper;
};

describe('useManagedAccounts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have correct initial state', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.isError).toBe(false);
  });

  it('should fetch accounts successfully', async () => {
    const mockAccounts = {
      accounts: [
        {
          id: 'acc-1',
          name: 'Sample Account',
          bank: 'Bank X',
          account_type: 'Checking',
          balance_paise: 150000,
          account_number_last4: '1234',
          is_active: 1,
          notes: 'Primary account',
          created_at: '2026-01-15T10:00:00Z',
          updated_at: '2026-02-01T14:30:00Z',
        },
      ],
      total: 1,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockAccounts),
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useManagedAccounts(), { wrapper });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockAccounts);
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

  it('should validate response schema', async () => {
    const invalidResponse = {
      accounts: [
        {
          id: 'acc-1',
          name: 123,
        },
      ],
    };

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
    const emptyResponse = {
      accounts: [],
      total: 0,
    };

    mockApiFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(emptyResponse),
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
