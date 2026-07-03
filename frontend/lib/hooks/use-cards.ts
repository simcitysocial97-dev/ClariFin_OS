import { useAsyncMutation } from './use-async-mutation';
import { useAsyncQuery, HookState } from './use-async-query';
import { queryKeys } from './use-query-finance';
import {
  fetchCards,
  createCard as apiCreateCard,
  updateCard as apiUpdateCard,
  deleteCard as apiDeleteCard,
  type Card,
} from '@/lib/api/client';

export function useCards(accountId?: number): HookState<{ cards: Card[]; total: number }> {
  return useAsyncQuery<{ cards: Card[]; total: number }>(
    ['cards', accountId],
    () => fetchCards(accountId),
  );
}

export function useCard(id: number | null): HookState<Card> {
  return useAsyncQuery<Card>(['card', id], () => Promise.resolve(null as unknown as Card));
}

export function useCreateCard(): {
  createCard: (data: Parameters<typeof apiCreateCard>[0]) => Promise<Card | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<Card, Parameters<typeof apiCreateCard>[0]>({
    mutationFn: apiCreateCard,
    invalidateKeys: [[...queryKeys.overview], ['cards']],
  });

  return {
    createCard: mutation.mutate,
    loading: mutation.loading,
    error: mutation.error,
  };
}

export function useUpdateCard(): {
  updateCard: (id: number, data: Parameters<typeof apiUpdateCard>[1]) => Promise<Card | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<Card, { id: number; data: Parameters<typeof apiUpdateCard>[1] }>({
    mutationFn: ({ id, data }) => apiUpdateCard(id, data),
    invalidateKeys: [[...queryKeys.overview], ['cards']],
  });

  return {
    updateCard: (id: number, data: Parameters<typeof apiUpdateCard>[1]) => mutation.mutate({ id, data }),
    loading: mutation.loading,
    error: mutation.error,
  };
}

export function useDeleteCard(): {
  deleteCard: (id: number) => Promise<{ success: boolean; message: string } | null>;
  loading: boolean;
  error: Error | null;
} {
  const mutation = useAsyncMutation<{ success: boolean; message: string }, number>({
    mutationFn: apiDeleteCard,
    invalidateKeys: [[...queryKeys.overview], ['cards']],
  });

  return {
    deleteCard: mutation.mutate,
    loading: mutation.loading,
    error: mutation.error,
  };
}