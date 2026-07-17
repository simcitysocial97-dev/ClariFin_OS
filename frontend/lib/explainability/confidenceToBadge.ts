/**
 * confidenceToBadge - Convert confidence BPS to badge level
 *
 * UI concern: Convert raw BPS to display level.
 * Thresholds: 0-3300=low, 3301-6600=medium, 6601-10000=high
 */

import type { ConfidenceBps } from './contracts/Confidence'

/**
 * Badge level for UI display
 */
export type BadgeLevel = 'low' | 'medium' | 'high'

/**
 * Convert confidence BPS to badge level
 */
export function confidenceToBadge(value: ConfidenceBps): BadgeLevel {
  if (value <= 3300) return 'low'
  if (value <= 6600) return 'medium'
  return 'high'
}

/**
 * Get badge styling class (UI helper)
 */
export function getBadgeClass(level: BadgeLevel): string {
  switch (level) {
    case 'high':
      return 'bg-green-100 text-green-800'
    case 'medium':
      return 'bg-yellow-100 text-yellow-800'
    case 'low':
      return 'bg-red-100 text-red-800'
  }
}