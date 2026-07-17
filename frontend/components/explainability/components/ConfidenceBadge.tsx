/**
 * ConfidenceBadge - Reusable badge for confidence display
 *
 * Reuses confidenceToBadge utility - no threshold logic duplication.
 */

import { Badge } from '@/components/ui/badge'
import { confidenceToBadge, getBadgeClass } from '@/lib/explainability'
import type { ConfidenceBps } from '@/lib/explainability'

interface ConfidenceBadgeProps {
  value: ConfidenceBps
  reason?: string
}

/**
 * Display confidence as a styled badge
 */
export function ConfidenceBadge({ value, reason }: ConfidenceBadgeProps) {
  const level = confidenceToBadge(value)
  const percentage = (value / 100).toFixed(0)

  return (
    <Badge
      className={getBadgeClass(level)}
      title={reason}
      aria-label={`Confidence: ${percentage}%`}
    >
      {percentage}%
    </Badge>
  )
}