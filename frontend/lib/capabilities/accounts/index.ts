/**
 * Accounts Capability - Public API
 *
 * Single entry point for all accounts-related functionality.
 */

// Re-export hook
export { useManagedAccounts } from './hooks/useAccounts'

// Re-export models
export type { AccountsModel, AccountModel } from './models/model'

// Re-export services (for advanced usage)
export { fetchManagedAccounts } from './services/api'

// Re-export contracts (for validation)
export { AccountSchema, AccountsResponseSchema } from './contracts/api'
export type { AccountDto, AccountsResponseDto } from './contracts/api'