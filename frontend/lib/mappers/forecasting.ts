/**
 * Forecasting Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { ForecastingResponseDto, ForecastMonthDto } from '../contracts/api/forecasting'
import type { ForecastingModel, ForecastMonthModel } from '../models/forecasting'

/**
 * Map ForecastMonth DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapForecastMonthToModel(dto: ForecastMonthDto): ForecastMonthModel {
  return {
    month: dto.month,
    expectedIncomePaise: dto.expected_income_paise,
    expectedExpensePaise: dto.expected_expense_paise,
    expectedSurplusPaise: dto.expected_surplus_paise,
    confidenceBps: dto.confidence_bps,
  }
}

/**
 * Map Forecasting DTO to Model
 *
 * Transformation rules:
 * - Map each forecast month to ViewModel
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapForecastingToModel(dto: ForecastingResponseDto): ForecastingModel {
  return {
    cashflow: dto.cashflow.map(mapForecastMonthToModel),
    liquidity: dto.liquidity,
    credit: dto.credit,
    riskFlags: dto.risk_flags,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { ForecastingModel, ForecastMonthModel }