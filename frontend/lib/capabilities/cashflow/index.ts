/**
 * Cashflow Capability - Public API
 *
 * Single entry point for all cashflow-related functionality.
 */

// Re-export hook
export { useCashflow } from './hooks/useCashflow'

// Re-export models
export type { CashflowModel, CashflowMonthModel } from './models/model'

// Re-export services (for advanced usage)
export { fetchCashflow, fetchCashflowSummary } from './services/api'

// Re-export contracts (for validation)
export { CashflowResponseSchema, CashflowMonthSchema } from './contracts/api'
export type { CashflowResponseDto, CashflowMonthDto } from './contracts/api'