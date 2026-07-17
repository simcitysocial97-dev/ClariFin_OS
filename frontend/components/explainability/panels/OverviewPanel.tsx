/**
 * OverviewPanel - Overview tab for explainability drawer
 *
 * Displays:
 * - Metric
 * - Current Value
 * - Confidence Badge
 * - Summary
 * - Evidence Count
 * - Calculation Count
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfidenceBadge } from '../components/ConfidenceBadge'
import type { Explanation } from '@/lib/explainability'

interface OverviewPanelProps {
  explanation: Explanation
}

/**
 * Display overview of an explanation
 */
export function OverviewPanel({ explanation }: OverviewPanelProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Metric</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="font-medium">{explanation.metric}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Current Value</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-2xl font-bold">{explanation.value.toLocaleString()}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Confidence</CardTitle>
        </CardHeader>
        <CardContent>
          <ConfidenceBadge
            value={explanation.confidence.value}
            reason={explanation.confidence.reason}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {explanation.confidence.reason ?? 'No summary available'}
          </p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Evidence Count</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{explanation.evidence.length}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Calculation Steps</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{explanation.calculationSteps.length}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}