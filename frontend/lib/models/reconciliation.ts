/**
 * Reconciliation Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Reconciliation match for UI consumption
 */
export interface ReconciliationMatchModel {
  id: number | null
  debitTxnId: number
  creditTxnId: number
  debitAccountId: string
  creditAccountId: string
  amountPaise: number
  dateDiffDays: number
  matchConfidence: number
  matchType: string
  status: string | null
  createdAt: string | null
  confirmedAt: string | null
  // Transaction details
  debitDate: string | null
  debitDateIso: string | null
  debitDescription: string | null
  debitAmountPaise: number | null
  debitBank: string | null
  creditDate: string | null
  creditDateIso: string | null
  creditDescription: string | null
  creditAmountPaise: number | null
  creditBank: string | null
}

/**
 * Reconciliation response for UI consumption
 */
export interface ReconciliationModel {
  matches: ReconciliationMatchModel[]
  count: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}