/**
 * Evidence List Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying a list of evidence items.
 */

'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { EvidenceItemComponent } from './evidence-item';
import type { EvidenceItem } from '@/lib/evidence/types';

interface EvidenceListProps {
  evidence: EvidenceItem[];
  loading: boolean;
  error: string | null;
}

/**
 * Evidence List Component
 * Displays evidence items with loading and error states
 */
export function EvidenceList({ evidence, loading, error }: EvidenceListProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          Failed to load evidence: {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (evidence.length === 0) {
    return (
      <p className="text-sm text-muted-foreground text-center py-4">
        No evidence available for this transaction
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-2 max-h-96 overflow-y-auto">
      {evidence.map((item, index) => (
        <EvidenceItemComponent key={index} item={item} />
      ))}
    </div>
  );
}