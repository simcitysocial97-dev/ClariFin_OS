/**
 * Loans Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Loan summary for UI consumption
 */
export interface LoanSummaryModel {
  id: number
  name: string
  lender: string | null
  loanType: string
  principalPaise: number
  outstandingPaise: number | null
  emiPaise: number | null
  interestRate: number
  tenureMonths: number | null
  disbursedDate: string | null
  isActive: boolean
}

/**
 * Loans response for UI consumption
 */
export interface LoansModel {
  loans: LoanSummaryModel[]
  totalOutstandingPaise: number
  totalPrincipalPaise: number
  totalMonthlyEmiPaise: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}