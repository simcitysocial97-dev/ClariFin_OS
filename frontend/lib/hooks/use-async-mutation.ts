import { useMutation, useQueryClient } from '@tanstack/react-query';

export interface MutationState<TData, TVariables> {
  loading: boolean;
  error: Error | null;
  data: TData | null;
  mutate: (variables: TVariables) => Promise<TData | null>;
  reset: () => void;
}

export function useAsyncMutation<TData, TVariables>(options: {
  mutationFn: (variables: TVariables) => Promise<TData>;
  invalidateKeys?: readonly unknown[][];
  onSuccess?: (data: TData) => void;
  onError?: (error: Error) => void;
}): MutationState<TData, TVariables> {
  const queryClient = useQueryClient();
  const { mutationFn, invalidateKeys = [], onSuccess, onError } = options;

  const mutation = useMutation<TData, Error, TVariables>({
    mutationFn,
    onSuccess: (data) => {
      if (onSuccess) onSuccess(data);
      invalidateKeys.forEach((key) => queryClient.invalidateQueries({ queryKey: key }));
    },
    onError: (error) => {
      if (onError) onError(error);
    },
  });

  const reset = () => {
    // reset is not directly supported in v5; mutation state resets on new calls
  };

  return {
    loading: mutation.isPending,
    error: mutation.error ?? null,
    data: mutation.data ?? null,
    mutate: mutation.mutateAsync,
    reset,
  };
}

export const __test = { useAsyncMutation };