/**
 * Forecasting Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Forecast month for UI consumption
 */
export interface ForecastMonthModel {
  month: string
  expectedIncomePaise: number
  expectedExpensePaise: number
  expectedSurplusPaise: number
  confidenceBps: number
}

/**
 * Forecasting response for UI consumption
 */
export interface ForecastingModel {
  cashflow: ForecastMonthModel[]
  liquidity: Record<string, unknown>
  credit: Record<string, unknown>
  riskFlags: Record<string, unknown>[]
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}