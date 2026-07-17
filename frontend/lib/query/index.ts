/**
 * Query Runtime — Shared React Query infrastructure
 *
 * Export all query-related utilities from a single entry point.
 */

export { queryKeys } from './queryKeys'
export type { QueryKey } from './queryKeys'

export {
  STALE_TIME,
  RETRY_POLICY,
  baseQueryOptions,
  baseMutationOptions,
  defaultRetryDelay,
} from './queryOptions'
export type { StaleTime, RetryPolicy } from './queryOptions'

export { useAppQuery, normalizeError } from './useAppQuery'
export type { AppError, AppQueryOptions } from './useAppQuery'

export { useAppMutation } from './useAppMutation'
export type { AppMutationOptions } from './useAppMutation'