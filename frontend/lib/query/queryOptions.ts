/**
 * Query Options — Shared defaults for React Query
 *
 * Semantic stale times describe purpose, not duration.
 * Retry policies are intentional, not hardcoded.
 */

// Semantic stale time categories
export const STALE_TIME = {
  /** Live data - refetch on every mount (0ms) */
  LIVE: 0,

  /** Frequent updates - 30 seconds */
  FREQUENT: 30_000,

  /** Normal data - 2 minutes */
  NORMAL: 120_000,

  /** Reference data - 5 minutes */
  REFERENCE: 300_000,

  /** Static data - 10 minutes */
  STATIC: 600_000,
} as const

// Retry policies
export const RETRY_POLICY = {
  /** No retries - for non-idempotent or time-sensitive operations */
  NONE: 0,

  /** Normal retry - 3 attempts with exponential backoff */
  NORMAL: 3,

  /** Aggressive retry - 5 attempts for critical data */
  AGGRESSIVE: 5,
} as const

// Default retry delay with exponential backoff
export const defaultRetryDelay = (attemptIndex: number): number =>
  Math.min(1000 * 2 ** attemptIndex, 30000)

// Base query options applied to all queries
export const baseQueryOptions = {
  staleTime: STALE_TIME.NORMAL,
  gcTime: 5 * 60 * 1000,
  retry: RETRY_POLICY.NORMAL,
  retryDelay: defaultRetryDelay,
  refetchOnWindowFocus: false,
  refetchOnReconnect: true,
  networkMode: 'online' as const,
}

// Base mutation options applied to all mutations
export const baseMutationOptions = {
  retry: RETRY_POLICY.NONE,
  networkMode: 'online' as const,
}

// Type exports
export type StaleTime = (typeof STALE_TIME)[keyof typeof STALE_TIME]
export type RetryPolicy = (typeof RETRY_POLICY)[keyof typeof RETRY_POLICY]