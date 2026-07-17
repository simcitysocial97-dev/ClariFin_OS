/**
 * NetWorth Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation, RecommendationExplanation } from '@/lib/explainability'

// Re-export explanation types for convenience
export type { Explanation, RecommendationExplanation }

/**
 * NetWorth explanation from backend
 * Contains explanations for netWorth, assets, and liabilities
 */
export interface NetWorthExplanation {
  netWorth: Explanation
  assets: Explanation
  liabilities: Explanation
  confidenceReason?: string
}

export interface NetWorthModel {
  // Core values (raw paise, for formatting in components)
  netWorthPaise: number
  assetsTotalPaise: number
  assetsAccountsPaise: number
  assetsInvestmentsPaise: number
  liabilitiesTotalPaise: number
  liabilitiesLoansPaise: number
  liabilitiesCardsPaise: number

  // Counts
  accountCount: number
  investmentCount: number
  loanCount: number
  cardCount: number

  // Derived UI flags
  trend: 'up' | 'down' | 'flat'
  isPartial: boolean
  partialReason: string | null

  // Last updated timestamp
  lastUpdated: string | null

  // Explanation (preserved from backend, not generated)
  explanation: NetWorthExplanation | null
}

export interface NetWorthAssetsModel {
  totalPaise: number
  accountsPaise: number
  investmentsPaise: number
  accountCount: number
  investmentCount: number
}

export interface NetWorthLiabilitiesModel {
  totalPaise: number
  loansPaise: number
  cardsPaise: number
  loanCount: number
  cardCount: number
}
