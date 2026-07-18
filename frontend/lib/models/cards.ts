/**
 * Credit Cards Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Credit card summary for UI consumption
 */
export interface CreditCardSummaryModel {
  cardId: string
  bank: string
  cardLast4: string | null
  creditLimitPaise: number
  currentOutstandingPaise: number
  minimumDuePaise: number
  utilizationBps: number
  isActive: boolean
}

/**
 * Credit cards response for UI consumption
 */
export interface CreditCardsModel {
  cards: CreditCardSummaryModel[]
  totalOutstandingPaise: number
  totalCreditLimitPaise: number
  totalUtilizationBps: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}