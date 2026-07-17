/**
 * useAppMutation — React Query mutation wrapper with project-wide behavior
 *
 * Adds beforeMutate hook, cache invalidation, and error normalization.
 * Does NOT include UI concerns (toasts) - those belong to callers.
 */

import { useMutation, useQueryClient, type UseMutationOptions, type UseMutationResult } from '@tanstack/react-query'
import { baseMutationOptions } from './queryOptions'
import type { AppError } from './useAppQuery'

// Query key type for invalidation
type QueryKey = readonly unknown[]

// Options for useAppMutation
export interface AppMutationOptions<TData, TError, TVariables>
  extends Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'> {
  mutationFn: (variables: TVariables) => Promise<TData>
  capability?: string
  // Function called before mutation - can return false to cancel
  beforeMutate?: (variables: TVariables) => Promise<boolean> | boolean
  // Query keys to invalidate on success
  invalidate?: QueryKey[] | (() => QueryKey[])
}

// useAppMutation - wraps useMutation with project defaults
export function useAppMutation<TData, TError = AppError, TVariables = void>(
  options: AppMutationOptions<TData, TError, TVariables>,
): UseMutationResult<TData, TError, TVariables> {
  const queryClient = useQueryClient()
  const { beforeMutate, invalidate, ...mutationOptions } = options

  return useMutation({
    ...baseMutationOptions,
    ...mutationOptions,
    mutationFn: async (variables: TVariables) => {
      // Run beforeMutate hook if provided
      if (beforeMutate) {
        const canProceed = await beforeMutate(variables)
        if (!canProceed) {
          throw { message: 'Mutation cancelled' } as TError
        }
      }
      return options.mutationFn(variables)
    },
    onSuccess: (_data, _variables, _context) => {
      // Invalidate specified query keys
      if (invalidate) {
        const keys = typeof invalidate === 'function' ? invalidate() : invalidate
        keys.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: key })
        })
      }
    },
  })
}