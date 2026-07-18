/**
 * Evidence Item Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying a single evidence item.
 */

'use client';

import { Badge } from '@/components/ui/badge';
import { EvidenceSourceLink } from './evidence-source-link';
import type { EvidenceItem, EvidenceType } from '@/lib/evidence/types';

interface EvidenceItemProps {
  item: EvidenceItem;
}

const typeColors: Record<EvidenceType, string> = {
  categorization: 'bg-blue-100 text-blue-800',
  import: 'bg-green-100 text-green-800',
  adjustment: 'bg-yellow-100 text-yellow-800',
  balance: 'bg-purple-100 text-purple-800',
  reconciliation: 'bg-indigo-100 text-indigo-800',
};

const typeLabels: Record<EvidenceType, string> = {
  categorization: 'Categorization',
  import: 'Import',
  adjustment: 'Adjustment',
  balance: 'Balance',
  reconciliation: 'Reconciliation',
};

/**
 * Evidence Item Component
 * Displays a single evidence item with type, summary, and source
 */
export function EvidenceItemComponent({ item }: EvidenceItemProps) {
  return (
    <div className="flex flex-col gap-2 rounded-lg border p-3">
      <div className="flex items-start justify-between">
        <Badge 
          variant="secondary" 
          className={`text-xs ${typeColors[item.type]}`}
        >
          {typeLabels[item.type]}
        </Badge>
        
        {item.confidence !== undefined && (
          <span className="text-xs text-muted-foreground">
            {item.confidence}% confidence
          </span>
        )}
      </div>
      
      <p className="text-sm">{item.summary}</p>
      
      <EvidenceSourceLink source={item.source} />
    </div>
  );
}