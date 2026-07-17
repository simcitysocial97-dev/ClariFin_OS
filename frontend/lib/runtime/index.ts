/**
 * Runtime Library - Public API
 *
 * Shared state runtime for all capabilities.
 */

// Contracts
export type { RuntimeState, RuntimeStateResult, StateConfig } from './contracts/runtime-state'

// Utilities
export {
  createLoading,
  createSuccess,
  createEmpty,
  createError,
  createOffline,
  createPermission,
  createStale,
  isTerminalState,
  isLoadingState,
  hasDataState,
} from './utils/state-utils'

// Registry
export { stateRegistry, getStateConfig, getStateIcon, getStateColor } from './utils/state-registry'

// Adapters
export { fromQuery, createFromQuery } from './adapters/react-query'