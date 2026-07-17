/**
 * Evidence - Immutable evidence for financial calculations
 *
 * Evidence represents a single piece of data that contributes to a calculation.
 * It is serializable and framework-independent.
 */

/**
 * Evidence value types - explicit for financial systems
 */
export type EvidenceValue = number | string | boolean | null

/**
 * Evidence types for categorization
 */
export type EvidenceType = 'data' | 'calculation' | 'source'

/**
 * Evidence for a calculation
 */
export interface Evidence {
  readonly id: string
  readonly type: EvidenceType
  readonly description: string
  readonly value: EvidenceValue
  readonly sourceId?: string | number
}

/**
 * Evidence collection
 */
export interface EvidenceCollection {
  readonly evidence: Evidence[]
}
