/**
 * mergeEvidence - Combine multiple evidence arrays
 *
 * Deduplicates by id to avoid duplicate evidence.
 */

import type { Evidence } from './contracts/Evidence'

/**
 * Merge multiple evidence arrays, deduplicating by id
 */
export function mergeEvidence(...evidenceArrays: Evidence[][]): Evidence[] {
  const seen = new Set<string>()
  const result: Evidence[] = []

  for (const evidenceArray of evidenceArrays) {
    for (const evidence of evidenceArray) {
      if (!seen.has(evidence.id)) {
        seen.add(evidence.id)
        result.push(evidence)
      }
    }
  }

  return result
}