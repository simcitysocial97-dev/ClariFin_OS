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
 * Responsive: full-width on mobile, side drawer on desktop
 * Accessible: ARIA labels for screen readers
 */
export function EvidenceDrawer({ state, onClose }: EvidenceDrawerProps) {
  return (
    <Sheet open={state.isOpen} onOpenChange={onClose}>
      <SheetContent 
        className="w-full max-w-full sm:max-w-lg md:max-w-xl lg:max-w-2xl"
        aria-label="Transaction Evidence Drawer"
        aria-describedby="evidence-description"
      >
        <SheetHeader>
          <SheetTitle id="evidence-title">Transaction Evidence</SheetTitle>
          <SheetDescription id="evidence-description">
            Explainability and traceability for this transaction. {state.evidence.length} evidence items available.
          </SheetDescription>
        </SheetHeader>
        
        <div 
          className="flex flex-col gap-4 py-4 max-h-[80vh] overflow-y-auto"
          role="region"
          aria-label="Evidence content"
        >
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
