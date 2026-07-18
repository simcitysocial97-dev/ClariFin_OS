/**
 * Accounts Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Account summary for UI consumption
 */
export interface AccountSummaryModel {
  accountId: string
  name: string
  bank: string
  accountType: string
  balancePaise: number
  averageBalancePaise: number
  trend: string
  velocityPaisePerDay: number
  isActive: boolean
}

/**
 * Accounts response for UI consumption
 */
export interface AccountsModel {
  accounts: AccountSummaryModel[]
  totalBalancePaise: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}