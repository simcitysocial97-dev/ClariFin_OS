/**
 * Overview Capability - Public API
 *
 * Single entry point for all overview-related functionality.
 */

// Re-export hook
export { useOverview } from './hooks/useOverview'

// Re-export models
export type { OverviewModel, BehavioralInsightModel, MonthlyChartPointModel, CategoryChartPointModel } from './models/model'

// Re-export services (for advanced usage)
export { fetchOverview } from './services/api'

// Re-export contracts (for validation)
export { OverviewResponseSchema } from './contracts/api'
export type { OverviewResponseDto, BehavioralInsightDto, MonthlyChartPointDto, CategoryChartPointDto } from './contracts/api'