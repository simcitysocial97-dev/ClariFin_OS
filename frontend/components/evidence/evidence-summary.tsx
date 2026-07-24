/**
 * Evidence Summary Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying evidence summary statistics.
 */

'use client';

import { Badge } from '@/components/ui/badge';
import type { EvidenceType } from '@/lib/evidence/types';

interface EvidenceSummaryProps {
  count: number;
  byType: Record<string, number>;
  averageConfidence: number;
}

/**
 * Evidence Summary Component
 * Displays summary statistics for evidence items
 */
export function EvidenceSummary({ count, byType, averageConfidence }: EvidenceSummaryProps) {
  const typeLabels: Record<EvidenceType, string> = {
    categorization: 'Categorization',
    import: 'Import',
    adjustment: 'Adjustment',
    balance: 'Balance',
    reconciliation: 'Reconciliation',
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Total Evidence</span>
        <span className="text-2xl font-bold">{count}</span>
      </div>
      
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Average Confidence</span>
        <span className="text-sm font-medium">{Math.round(averageConfidence)}%</span>
      </div>
      
      <div className="flex flex-wrap gap-1 pt-2">
        {Object.entries(byType).map(([type, typeCount]) => (
          <Badge key={type} variant="secondary" className="text-xs">
            {typeLabels[type as EvidenceType]}: {typeCount}
          </Badge>
        ))}
      </div>
    </div>
  );
}