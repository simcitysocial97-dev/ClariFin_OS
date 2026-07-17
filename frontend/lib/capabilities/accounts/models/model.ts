/**
 * Accounts Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

/**
 * Account data for UI consumption
 */
export interface AccountModel {
  id: string
  name: string
  bank: string
  accountType: string
  balancePaise: number
  accountNumberLast4: string | null
  isActive: number
  notes: string | null
  createdAt: string
  updatedAt: string
}

/**
 * Accounts response for UI consumption
 */
export interface AccountsModel {
  accounts: AccountModel[]
  total: number
}