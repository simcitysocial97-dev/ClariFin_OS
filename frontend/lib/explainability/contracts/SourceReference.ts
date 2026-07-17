/**
 * Source Reference - Canonical provenance model for explainability
 *
 * Describes the exact origin of data for full traceability.
 * This is the source of truth for "Where exactly did this number come from?"
 *
 * Business provenance only - no technical implementation details.
 */

/**
 * Source types for provenance tracking
 * Must match backend SourceType in src/models/explanation.py
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
 *
 * Provides business-level traceability for financial data.
 * Mirrors backend SourceReference model exactly.
 */
export interface SourceReference {
  // Source type classification
  type: SourceType

  // Source identifier
  id: string | number

  // Human-readable name
  name?: string | null

  // Source date (for statements)
  date?: string | null
}

/**
 * Source collection for an explanation
 */
export interface SourceCollection {
  readonly sources: SourceReference[]
}
