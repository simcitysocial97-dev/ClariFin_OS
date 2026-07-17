/**
 * State Utilities - Pure functions for runtime state creation
 *
 * These are pure utility functions that create state objects.
 * They do NOT wrap React Query - that's the adapter's job.
 */

import type { RuntimeState, RuntimeStateResult, RuntimeStateMetadata } from '../contracts/runtime-state'

/**
 * Create a loading state
 */
export function createLoading<T>(): RuntimeStateResult<T> {
  return {
    state: 'loading',
  }
}

/**
 * Create a success state with data
 */
export function createSuccess<T>(data: T): RuntimeStateResult<T> {
  return {
    state: 'success',
    data,
  }
}

/**
 * Create an empty state
 */
export function createEmpty<T>(
  title: string,
  description: string,
  action?: { label: string; onClick: () => void }
): RuntimeStateResult<T> {
  return {
    state: 'empty',
    title,
    description,
    retry: action?.onClick,
  }
}

/**
 * Create an error state
 */
export function createError<T>(
  error: Error,
  title?: string,
  retry?: () => void,
  description?: string
): RuntimeStateResult<T> {
  return {
    state: 'error',
    error,
    title: title ?? 'Something went wrong',
    description,
    retry,
  }
}

/**
 * Create an offline state
 */
export function createOffline<T>(
  title?: string,
  description?: string,
  retry?: () => void
): RuntimeStateResult<T> {
  return {
    state: 'offline',
    title: title ?? 'You are offline',
    description: description ?? 'Check your connection and try again',
    retry,
  }
}

/**
 * Create a permission state
 */
export function createPermission<T>(
  title?: string,
  description?: string
): RuntimeStateResult<T> {
  return {
    state: 'permission',
    title: title ?? 'Access denied',
    description: description ?? 'You do not have permission to view this data',
  }
}

/**
 * Create a stale state (cached data being refreshed)
 */
export function createStale<T>(
  data: T,
  lastUpdated: number,
  metadata?: RuntimeStateMetadata
): RuntimeStateResult<T> {
  return {
    state: 'stale',
    data,
    lastUpdated,
    metadata: {
      stale: true,
      ...metadata,
    },
  }
}

/**
 * Check if a state is terminal (user action required)
 * Terminal states: error, offline, permission
 */
export function isTerminalState(state: RuntimeState): boolean {
  return state === 'error' || state === 'offline' || state === 'permission'
}

/**
 * Check if a state is loading (initial or background)
 */
export function isLoadingState(state: RuntimeState): boolean {
  return state === 'loading' || state === 'stale'
}

/**
 * Check if a state has data
 */
export function hasDataState(state: RuntimeState): boolean {
  return state === 'success' || state === 'stale'
}