/**
 * EvidenceCard - Display a single evidence item
 */

import { Card, CardContent } from '@/components/ui/card'
import type { Evidence } from '@/lib/explainability'

interface EvidenceCardProps {
  evidence: Evidence
}

/**
 * Format evidence value for display
 */
function formatEvidenceValue(value: unknown): string {
  if (value === null) return '—'
  if (typeof value === 'number') return value.toLocaleString()
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

/**
 * Display a single evidence item
 */
export function EvidenceCard({ evidence }: EvidenceCardProps) {
  return (
    <Card className="border-l-4 border-l-blue-500">
      <CardContent className="p-4">
        <div className="space-y-1">
          <p className="text-sm font-medium">{evidence.description}</p>
          <p className="text-sm text-muted-foreground">{formatEvidenceValue(evidence.value)}</p>
          {evidence.sourceId && (
            <p className="text-xs text-muted-foreground">Source: {evidence.sourceId}</p>
          )}
        </div>
      </CardContent>
    </Card>
  )
}