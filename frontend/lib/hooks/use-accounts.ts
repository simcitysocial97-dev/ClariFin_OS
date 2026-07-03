import { useCallback } from 'react';
import { useAsyncMutation } from './use-async-mutation';
import { useAsyncQuery, HookState } from './use-async-query';
import { queryKeys } from './use-query-finance';
import {
  fetchAccounts,
  fetchAccount,
  createAccount as apiCreateAccount,
  updateAccount as apiUpdateAccount,
  deleteAccount as apiDeleteAccount,
  type Account,
  type AccountCreateInput,
  type AccountUpdateInput,
} from '@/lib/api/client';

export function useAccounts(): HookState<{ accounts: Account[]; total: number }> {
  return useAsyncQuery<{ accounts: Account[]; total: number }>(['accounts'], fetchAccounts);
}

export function useAccount(id: number | null): HookState<Account> {
  return useAsyncQuery<Account>(['account', id], () => fetchAccount(id ?? 0), 60_000);
}

export function useCreateAccount(): {
  createAccount: (data: AccountCreateInput) => Promise<Account | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<Account, AccountCreateInput>({
    mutationFn: apiCreateAccount,
    invalidateKeys: [[...queryKeys.overview]],
  });

  return {
    createAccount: mutation.mutate,
    loading: mutation.loading,
    error: mutation.error,
  };
}

export function useUpdateAccount(): {
  updateAccount: (id: number, data: AccountUpdateInput) => Promise<Account | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<Account, { id: number; data: AccountUpdateInput }>({
    mutationFn: ({ id, data }) => apiUpdateAccount(id, data),
    invalidateKeys: [[...queryKeys.overview]],
  });

  return {
    updateAccount: useCallback((id: number, data: AccountUpdateInput) => mutation.mutate({ id, data }), [mutation]),
    loading: mutation.loading,
    error: mutation.error,
  };
}

export function useDeleteAccount(): {
  deleteAccount: (id: number) => Promise<{ success: boolean; message: string } | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<{ success: boolean; message: string }, number>({
    mutationFn: apiDeleteAccount,
    invalidateKeys: [[...queryKeys.overview]],
  });

  return {
    deleteAccount: mutation.mutate,
    loading: mutation.loading,
    error: mutation.error,
  };
}