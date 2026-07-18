/**
 * Evidence Drawer Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying transaction evidence in a slide-out drawer.
 */

'use client';

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { EvidenceSummary } from './evidence-summary';
import { EvidenceList } from './evidence-list';
import type { EvidenceState } from '@/lib/evidence/types';

interface EvidenceDrawerProps {
  state: EvidenceState;
  onClose: () => void;
}

/**
 * Evidence Drawer Component
 * Displays evidence items for a selected transaction
 */
export function EvidenceDrawer({ state, onClose }: EvidenceDrawerProps) {
  return (
    <Sheet open={state.isOpen} onOpenChange={onClose}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Transaction Evidence</SheetTitle>
          <SheetDescription>
            Explainability and traceability for this transaction
          </SheetDescription>
        </SheetHeader>
        
        <div className="flex flex-col gap-4 py-4">
          <EvidenceSummary 
            count={state.evidence.length}
            byType={state.evidence.reduce((acc, e) => {
              acc[e.type] = (acc[e.type] || 0) + 1;
              return acc;
            }, {} as Record<string, number>)}
            averageConfidence={state.evidence.reduce((sum, e) => sum + (e.confidence || 0), 0) / (state.evidence.length || 1)}
          />
          
          <EvidenceList 
            evidence={state.evidence}
            loading={state.loading}
            error={state.error}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}