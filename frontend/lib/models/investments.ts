/**
 * Investments Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Investment summary for UI consumption
 */
export interface InvestmentSummaryModel {
  id: number
  name: string
  type: string
  investedPaise: number
  currentPaise: number
  gainPaise: number
  gainPercent: number
  isActive: boolean
}

/**
 * Investments response for UI consumption
 */
export interface InvestmentsModel {
  investments: InvestmentSummaryModel[]
  totalInvestedPaise: number
  totalCurrentPaise: number
  totalGainPaise: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}