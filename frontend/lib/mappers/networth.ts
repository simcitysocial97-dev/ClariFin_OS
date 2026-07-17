/**
 * NetWorth Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type { NetWorthDto } from '../contracts/api/networth'
import type { NetWorthModel, NetWorthAssetsModel, NetWorthLiabilitiesModel, NetWorthExplanation } from '../models/networth'

/**
 * Calculate trend based on assets vs liabilities
 */
function calculateTrend(
  assetsTotalPaise: number,
  liabilitiesTotalPaise: number,
): 'up' | 'down' | 'flat' {
  const netChangePaise = assetsTotalPaise - liabilitiesTotalPaise
  if (netChangePaise > 0) return 'up'
  if (netChangePaise < 0) return 'down'
  return 'flat'
}

/**
 * Map NetWorth DTO to Model
 *
 * Transformation rules:
 * - Flatten nested structure for easier component access
 * - Derive UI flags (trend)
 * - Rename fields to camelCase for consistency
 * - Preserve explanation from backend (not generated)
 */
export function mapNetworthToModel(dto: NetWorthDto): NetWorthModel {
  const assetsTotalPaise = dto.assets.total_paise
  const liabilitiesTotalPaise = dto.liabilities.total_paise

  // Preserve explanation from backend (source of truth)
  const explanation: NetWorthExplanation | null = dto.explanation ?? null

  const model: NetWorthModel = {
    // Core values
    netWorthPaise: dto.net_worth_paise,
    assetsTotalPaise,
    assetsAccountsPaise: dto.assets.accounts_paise,
    assetsInvestmentsPaise: dto.assets.investments_paise,
    liabilitiesTotalPaise,
    liabilitiesLoansPaise: dto.liabilities.loans_paise,
    liabilitiesCardsPaise: dto.liabilities.cards_paise,

    // Counts
    accountCount: dto.assets.account_count,
    investmentCount: dto.assets.investment_count,
    loanCount: dto.liabilities.loan_count,
    cardCount: dto.liabilities.card_count,

    // Derived UI flags
    trend: calculateTrend(assetsTotalPaise, liabilitiesTotalPaise),
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,

    // Explanation (preserved from backend)
    explanation,
  }

  return model
}

// Re-export types for convenience
export type { NetWorthModel, NetWorthAssetsModel, NetWorthLiabilitiesModel }
