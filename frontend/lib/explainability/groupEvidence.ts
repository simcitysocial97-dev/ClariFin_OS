/**
 * groupEvidence - Group evidence by type
 */

import type { Evidence, EvidenceType } from './contracts/Evidence'

/**
 * Group evidence by type
 */
export function groupEvidence(
  evidence: Evidence[],
): Record<EvidenceType, Evidence[]> {
  const groups: Record<EvidenceType, Evidence[]> = {
    data: [],
    calculation: [],
    source: [],
  }

  for (const item of evidence) {
    groups[item.type].push(item)
  }

  return groups
}