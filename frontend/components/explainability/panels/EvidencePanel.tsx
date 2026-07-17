/**
 * EvidencePanel - Evidence tab for explainability drawer
 *
 * Groups evidence by type (data, calculation, source)
 * Uses runtime grouping utilities.
 */

import { groupEvidence } from '@/lib/explainability'
import { EvidenceCard } from '../components/EvidenceCard'
import { Separator } from '@/components/ui/separator'
import type { Explanation } from '@/lib/explainability'

interface EvidencePanelProps {
  explanation: Explanation
}

/**
 * Display evidence grouped by type
 */
export function EvidencePanel({ explanation }: EvidencePanelProps) {
  const grouped = groupEvidence(explanation.evidence)

  return (
    <div className="space-y-4">
      {grouped.data.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2">Data Evidence ({grouped.data.length})</h3>
          <div className="space-y-2">
            {grouped.data.map((evidence) => (
              <EvidenceCard key={evidence.id} evidence={evidence} />
            ))}
          </div>
        </div>
      )}

      {grouped.calculation.length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">Calculation Evidence ({grouped.calculation.length})</h3>
            <div className="space-y-2">
              {grouped.calculation.map((evidence) => (
                <EvidenceCard key={evidence.id} evidence={evidence} />
              ))}
            </div>
          </div>
        </>
      )}

      {grouped.source.length > 0 && (
        <>
          <Separator />
          <div>
            <h3 className="text-sm font-medium mb-2">Source Evidence ({grouped.source.length})</h3>
            <div className="space-y-2">
              {grouped.source.map((evidence) => (
                <EvidenceCard key={evidence.id} evidence={evidence} />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}