/**
 * Source Reference - Business provenance for explainability
 *
 * Describes the business source of data, not implementation details.
 * Same source can support multiple evidence items.
 */

/**
 * Source types for financial data
 */
export type SourceType =
  | 'statement'
  | 'account'
  | 'loan'
  | 'investment'
  | 'transaction'
  | 'recommendation_engine'
  | 'cashflow_engine'
  | 'behaviour_engine'
  | 'user_input'

/**
 * Source reference for evidence provenance
 */
export interface SourceReference {
  readonly type: SourceType
  readonly id: string | number
  readonly name?: string
  readonly date?: string
}

/**
 * Source collection for an explanation
 */
export interface SourceCollection {
  readonly sources: SourceReference[]
}