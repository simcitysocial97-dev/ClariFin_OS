/**
 * Investments Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { InvestmentsDto, InvestmentSummaryDto } from '../contracts/api/investments'
import type { InvestmentsModel, InvestmentSummaryModel } from '../models/investments'

/**
 * Map InvestmentSummary DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapInvestmentSummaryToModel(dto: InvestmentSummaryDto): InvestmentSummaryModel {
  return {
    id: dto.id,
    name: dto.name,
    type: dto.type,
    investedPaise: dto.invested_paise,
    currentPaise: dto.current_value_paise,
    gainPaise: dto.gain_paise,
    gainPercent: dto.gain_percent,
    isActive: dto.is_active,
  }
}

/**
 * Map Investments DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapInvestmentsToModel(dto: InvestmentsDto): InvestmentsModel {
  return {
    investments: dto.investments.map(mapInvestmentSummaryToModel),
    totalInvestedPaise: dto.total_invested_paise,
    totalCurrentPaise: dto.total_current_value_paise,
    totalGainPaise: dto.total_gain_paise,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { InvestmentsModel, InvestmentSummaryModel }