/**
 * Confidence - Confidence score in basis points (0-10000)
 *
 * All confidence values are integers in basis points (0-10000 = 0-100%).
 * No UI concerns - the UI decides how to display.
 */

/**
 * Confidence in basis points (0-10000)
 * Validated at runtime, not compile time
 */
export type ConfidenceBps = number

/**
 * Confidence for a metric or recommendation
 */
export interface Confidence {
  readonly value: ConfidenceBps
  readonly reason?: string
}

/**
 * Confidence validation
 */
export function isValidConfidenceBps(value: number): value is ConfidenceBps {
  return Number.isInteger(value) && value >= 0 && value <= 10000
}

/**
 * Create a confidence value with validation
 */
export function createConfidence(
  value: number,
  reason?: string,
): Confidence {
  if (!isValidConfidenceBps(value)) {
    throw new Error(`Invalid confidence value: ${value}. Must be integer 0-10000.`)
  }
  return { value, reason }
}
