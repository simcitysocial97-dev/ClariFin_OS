/**
 * Cashflow Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

/**
 * Cashflow month data for UI consumption
 */
export interface CashflowMonthModel {
  monthKey: string
  monthLabel: string
  incomePaise: number
  expensePaise: number
  netPaise: number
  transactionCount: number
}

/**
 * Cashflow response for UI consumption
 */
export interface CashflowModel {
  months: CashflowMonthModel[]
  periodMonths: number
  totalIncomePaise: number
  totalExpensePaise: number
  totalNetPaise: number
}