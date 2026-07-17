/**
 * sortEvidence - Sort evidence by priority
 *
 * Sorts by confidence (descending), then by type priority.
 */

import type { Evidence, EvidenceType } from './contracts/Evidence'

/**
 * Type priority for sorting
 */
const TYPE_PRIORITY: Record<EvidenceType, number> = {
  calculation: 1,
  data: 2,
  source: 3,
}

/**
 * Sort evidence by confidence (descending), then by type priority
 */
export function sortEvidence(evidence: Evidence[]): Evidence[] {
  return [...evidence].sort((a, b) => {
    // Sort by type priority first (calculations before data before sources)
    const priorityDiff = TYPE_PRIORITY[a.type] - TYPE_PRIORITY[b.type]
    if (priorityDiff !== 0) return priorityDiff

    // Then by description for stable sort
    return a.description.localeCompare(b.description)
  })
}