/**
 * useAppQuery — React Query wrapper with project-wide behavior
 *
 * Adds capability metadata, error normalization, and future telemetry.
 * Does NOT include UI concerns (toasts, modals) - those belong to callers.
 */

import { useQuery, type UseQueryOptions, type UseQueryResult } from '@tanstack/react-query'
import { baseQueryOptions, type StaleTime, type RetryPolicy } from './queryOptions'

// AppError - normalized error type for the application
export interface AppError {
  message: string
  code?: string
  capability?: string
}

// Normalize any error to AppError
export function normalizeError(error: unknown, capability?: string): AppError {
  if (error instanceof Error) {
    return {
      message: error.message,
      capability,
    }
  }
  if (typeof error === 'string') {
    return {
      message: error,
      capability,
    }
  }
  return {
    message: 'Unknown error',
    capability,
  }
}

// Options for useAppQuery
export interface AppQueryOptions<TData, TError> extends Omit<UseQueryOptions<TData, TError>, 'queryKey'> {
  queryKey: readonly unknown[]
  capability?: string
  staleTime?: StaleTime
  retryPolicy?: RetryPolicy
}

// useAppQuery - wraps useQuery with project defaults and metadata
export function useAppQuery<TData, TError = AppError>(
  options: AppQueryOptions<TData, TError>,
): UseQueryResult<TData, TError> {
  const { capability, staleTime, retryPolicy, ...queryOptions } = options

  // Apply project defaults with optional overrides
  const mergedOptions: UseQueryOptions<TData, TError> = {
    ...baseQueryOptions,
    ...queryOptions,
    staleTime: staleTime ?? baseQueryOptions.staleTime,
    retry: retryPolicy ?? baseQueryOptions.retry,
  }

  // Add capability metadata for future telemetry
  if (capability) {
    mergedOptions.meta = {
      ...queryOptions.meta,
      capability,
    }
  }

  return useQuery(mergedOptions)
}