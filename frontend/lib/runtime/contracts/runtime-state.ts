/**
 * Runtime State Contracts
 *
 * Canonical state types for the shared runtime.
 * These are UI-consumable states derived from TanStack Query.
 */

/**
 * Runtime states for UI consumption
 * - loading: Initial data fetch in progress
 * - success: Data available
 * - empty: No data (but request succeeded)
 * - error: Request failed
 * - offline: No network connection
 * - permission: Access denied
 * - stale: Cached data being refreshed in background
 */
export type RuntimeState =
  | 'loading'
  | 'success'
  | 'empty'
  | 'error'
  | 'offline'
  | 'permission'
  | 'stale'

/**
 * Runtime state metadata - optional additional context
 */
export interface RuntimeStateMetadata {
  /** Whether data is stale (background refetch in progress) */
  stale?: boolean
  /** Timestamp of last data update */
  updatedAt?: number
  /** Capability ID for telemetry */
  capability?: string
}

/**
 * Runtime state result - derived from TanStack Query
 * This is the output of the adapter, not a replacement for query state.
 */
export interface RuntimeStateResult<T> {
  state: RuntimeState
  data?: T
  error?: Error
  retry?: () => void
  title?: string
  description?: string
  lastUpdated?: number
  /** Optional metadata for additional context */
  metadata?: RuntimeStateMetadata
}

/**
 * Configuration for state detection
 */
export interface StateConfig {
  /** Function to determine if data is empty */
  isEmpty?: (data: unknown) => boolean
  /** Custom title for error state */
  errorTitle?: string
  /** Custom description for error state */
  errorDescription?: (error: Error) => string
}