import { useQuery, useQueryClient } from '@tanstack/react-query';

export interface HookState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  isFetching: boolean;
  hasLoaded: boolean;
  refetch: () => Promise<void>;
}

export function normalizeError(error: unknown): Error {
  if (error instanceof Error) return error;
  if (typeof error === 'string') return new Error(error);
  return new Error('Unknown error');
}

export function useAsyncQuery<T>(key: readonly unknown[], fetcher: () => Promise<T>, staleTimeMs = 5 * 60 * 1000): HookState<T> {
  const queryClient = useQueryClient();
  const result = useQuery<T, Error>({
    queryKey: key,
    queryFn: fetcher,
    staleTime: staleTimeMs,
  });

  const refetch = async () => {
    await queryClient.invalidateQueries({ queryKey: key });
  };

  return {
    data: result.data ?? null,
    loading: result.isLoading,
    error: result.error ?? null,
    isFetching: result.isFetching,
    hasLoaded: result.isFetching || result.data !== undefined,
    refetch,
  };
}

export const __test = {
  normalizeError,
};