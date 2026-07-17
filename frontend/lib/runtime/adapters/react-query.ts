/**
 * React Query Adapter - Convert TanStack Query results to RuntimeState
 *
 * This is the bridge between React Query and the runtime state system.
 * It does NOT replace React Query - it adapts it for UI consumption.
 */

import type { UseQueryResult } from '@tanstack/react-query'
import type { RuntimeStateResult, StateConfig } from '../contracts/runtime-state'
import {
  createLoading,
  createSuccess,
  createEmpty,
  createError,
  createOffline,
  createStale,
} from '../utils/state-utils'

/**
 * Convert a TanStack Query result to a RuntimeState
 *
 * Priority:
 * 1. error (including network/offline errors)
 * 2. loading (no cached data)
 * 3. stale (has data, refetching)
 * 4. empty (has data but isEmpty returns true)
 * 5. success (has data)
 */
export function fromQuery<T>(
  query: UseQueryResult<T, any>,
  config?: StateConfig
): RuntimeStateResult<T> {
  const { isEmpty, errorTitle, errorDescription } = config ?? {}

  // Error state (including network errors)
  if (query.error) {
    const isOffline = query.error.message?.includes('offline') ?? false
    if (isOffline) {
      return createOffline(
        'You are offline',
        'Check your connection and try again',
        query.refetch
      )
    }
    return createError(
      query.error,
      errorTitle,
      query.refetch,
      errorDescription?.(query.error)
    )
  }

  // Loading state (no cached data)
  if (query.isLoading || (!query.data && query.isFetching)) {
    return createLoading()
  }

  // Stale state (has data, background refetch)
  if (query.isFetching && query.data) {
    return createStale(query.data, query.dataUpdatedAt)
  }

  // Success or empty state
  if (query.data !== undefined && query.data !== null) {
    if (isEmpty?.(query.data as T) ?? false) {
      return createEmpty(
        'No data available',
        'There is no data to display',
        { label: 'Refresh', onClick: query.refetch }
      )
    }
    return createSuccess(query.data)
  }

  // Default to loading if we have no data and no error
  return createLoading()
}

/**
 * Create a query result with custom empty detection
 */
export function createFromQuery<T>(
  query: UseQueryResult<T, any>,
  isEmpty: (data: T) => boolean
): RuntimeStateResult<T> {
  return fromQuery(query, { isEmpty: isEmpty as (data: unknown) => boolean })
}