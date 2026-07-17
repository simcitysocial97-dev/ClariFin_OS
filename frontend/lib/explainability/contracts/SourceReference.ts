/**
 * Source Reference - Canonical provenance model for explainability
 *
 * Describes the exact origin of data for full traceability.
 * This is the source of truth for "Where exactly did this number come from?"
 */

/**
 * Source types for provenance tracking
 */
export type SourceType =
  | 'database'
  | 'engine'
  | 'service'
  | 'repository'
  | 'statement'
  | 'transaction'
  | 'manual'
  | 'external'

/**
 * Source reference for evidence provenance
 *
 * Provides full traceability from UI to source code.
 */
export interface SourceReference {
  // Source type classification
  sourceType: SourceType

  // Database provenance
  table?: string
  recordId?: string | number

  // Backend layer provenance
  repository?: string
  service?: string
  engine?: string

  // API provenance
  router?: string
  endpoint?: string

  // Code-level provenance
  function?: string
  file?: string
  line?: number

  // Statement/transaction provenance
  statementId?: string
  transactionId?: string

  // Human-readable description
  description?: string
}

/**
 * Source collection for an explanation
 */
export interface SourceCollection {
  readonly sources: SourceReference[]
}