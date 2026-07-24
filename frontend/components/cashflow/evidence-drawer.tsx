/**
 * Evidence Drawer - Stage 4 Cashflow Truth Workspace
 *
 * Displays evidence chain for cashflow calculations.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ExternalLink } from 'lucide-react';
import type { CashflowEvidenceChainViewModel } from '@/types/cashflow-view-model';

/**
 * Evidence Drawer Props
 */
interface EvidenceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidenceChain?: CashflowEvidenceChainViewModel;
}

/**
 * Evidence Drawer Component
 *
 * Shows the calculation chain and evidence for cashflow metrics.
 */
export function EvidenceDrawer({ isOpen, onClose, evidenceChain }: EvidenceDrawerProps) {
  if (!evidenceChain) {
    return (
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Evidence</SheetTitle>
          </SheetHeader>
          <p className="text-gray-500 text-sm mt-4">No evidence available</p>
        </SheetContent>
      </Sheet>
    );
  }

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Evidence Chain</SheetTitle>
        </SheetHeader>
        <ScrollArea className="h-[calc(100vh-8rem)] mt-4">
          <div className="space-y-6">
            {/* Summary */}
            <div>
              <h3 className="text-sm font-medium mb-2">Summary</h3>
              <p className="text-sm text-gray-600">{evidenceChain.summary}</p>
            </div>

            {/* Calculation Steps */}
            {evidenceChain.calculation_steps && evidenceChain.calculation_steps.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Calculation Steps</h3>
                <div className="space-y-3">
                  {evidenceChain.calculation_steps.map((step, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <p className="font-medium text-sm">{step.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{step.description}</p>
                      {Object.keys(step.inputs).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs cursor-pointer">Inputs</summary>
                          <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(step.inputs, null, 2)}
                          </pre>
                        </details>
                      )}
                      {Object.keys(step.outputs).length > 0 && (
                        <details className="mt-2">
                          <summary className="text-xs cursor-pointer">Outputs</summary>
                          <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-x-auto">
                            {JSON.stringify(step.outputs, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evidence Items */}
            {evidenceChain.evidence && evidenceChain.evidence.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Evidence Items</h3>
                <div className="space-y-2">
                  {evidenceChain.evidence.map((item, index) => (
                    <div key={index} className="border-l-2 border-blue-500 pl-3 py-1">
                      <p className="text-sm font-medium">{item.type}</p>
                      <p className="text-xs text-gray-600">{item.summary}</p>
                      <p className="text-xs text-gray-400 mt-1">Source: {item.source}</p>
                      {item.confidence !== undefined && (
                        <p className="text-xs text-gray-400">
                          Confidence: {item.confidence}%
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Source References */}
            {evidenceChain.source_references && evidenceChain.source_references.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Source References</h3>
                <ul className="space-y-1">
                  {evidenceChain.source_references.map((ref, index) => (
                    <li key={index} className="text-xs">
                      <a
                        href={ref}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        {ref}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}