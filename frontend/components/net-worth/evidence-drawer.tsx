/**
 * Net Worth Evidence Drawer - Stage 4 Net Worth Intelligence Workspace
 *
 * Shows explainability evidence for net worth calculations.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel → Capability → Workspace → Components → Page
 */

import { X, FileText, Calculator, Link } from 'lucide-react';
import type { NetWorthViewModel, NetWorthEvidenceChainViewModel } from '@/types/net-worth-view-model';

/**
 * Net Worth Evidence Drawer Props
 */
interface EvidenceDrawerProps {
  netWorth: NetWorthViewModel | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Evidence Item Component
 */
function EvidenceItem({ item }: { item: { type: string; summary: string; source: string; confidence?: number } }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-start gap-2">
        <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium">{item.summary}</p>
          <p className="text-xs text-gray-500 mt-1">Source: {item.source}</p>
          {item.confidence !== undefined && (
            <p className="text-xs text-gray-400">Confidence: {item.confidence}%</p>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Calculation Step Component
 */
function CalculationStep({ step }: { step: { name: string; description: string; inputs: Record<string, unknown>; outputs: Record<string, unknown> } }) {
  return (
    <div className="border-b pb-3 mb-3 last:border-0 last:pb-0 last:mb-0">
      <div className="flex items-start gap-2">
        <Calculator className="h-4 w-4 text-gray-400 mt-0.5" />
        <div className="flex-1">
          <p className="text-sm font-medium">{step.name}</p>
          <p className="text-xs text-gray-500 mt-1">{step.description}</p>
        </div>
      </div>
    </div>
  );
}

/**
 * Net Worth Evidence Drawer Component
 */
export function EvidenceDrawer({ netWorth, isOpen, onClose }: EvidenceDrawerProps) {
  if (!isOpen) return null;

  const evidenceChain: NetWorthEvidenceChainViewModel | undefined = netWorth?.evidence_chain;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex justify-end" onClick={onClose}>
      <div
        className="bg-white w-full max-w-md h-full overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Net worth evidence drawer"
      >
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Evidence</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 rounded"
              aria-label="Close evidence drawer"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {evidenceChain ? (
            <div className="space-y-4">
              {/* Summary */}
              <div>
                <h3 className="text-sm font-medium mb-2">Summary</h3>
                <p className="text-sm text-gray-600">{evidenceChain.summary}</p>
              </div>

              {/* Evidence Items */}
              {evidenceChain.evidence.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Evidence</h3>
                  <div className="space-y-2">
                    {evidenceChain.evidence.map((item, index) => (
                      <EvidenceItem key={index} item={item} />
                    ))}
                  </div>
                </div>
              )}

              {/* Calculation Steps */}
              {evidenceChain.calculation_steps.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Calculation Steps</h3>
                  <div className="space-y-2">
                    {evidenceChain.calculation_steps.map((step, index) => (
                      <CalculationStep key={index} step={step} />
                    ))}
                  </div>
                </div>
              )}

              {/* Source References */}
              {evidenceChain.source_references.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium mb-2">Sources</h3>
                  <div className="space-y-1">
                    {evidenceChain.source_references.map((source, index) => (
                      <div key={index} className="flex items-center gap-2 text-xs">
                        <Link className="h-3 w-3 text-gray-400" />
                        <span className="text-gray-600">{source}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confidence Score */}
              <div className="pt-4 border-t">
                <p className="text-sm font-medium">
                  Confidence Score: {evidenceChain.confidence_score}%
                </p>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No evidence available for this calculation.</p>
          )}
        </div>
      </div>
    </div>
  );
}