/**
 * Evidence Calculation View Component - Stage 3 Transaction Intelligence Workspace
 *
 * UI component for displaying calculation chain for evidence.
 */

'use client';

import { ChevronDown, ChevronRight, Calculator } from 'lucide-react';
import { useState } from 'react';
import type { CalculationStep } from '@/types/transaction-view-model';

interface EvidenceCalculationViewProps {
  steps: CalculationStep[];
}

/**
 * Evidence Calculation View Component
 * Displays the calculation chain for a transaction
 */
export function EvidenceCalculationView({ steps }: EvidenceCalculationViewProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  const toggleStep = (stepName: string) => {
    setExpandedSteps(prev => {
      const next = new Set(prev);
      if (next.has(stepName)) {
        next.delete(stepName);
      } else {
        next.add(stepName);
      }
      return next;
    });
  };

  if (steps.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-sm font-medium">
        <Calculator className="h-4 w-4" />
        <span>Calculation Chain</span>
      </div>
      
      <div className="flex flex-col gap-1">
        {steps.map((step) => {
          const isExpanded = expandedSteps.has(step.name);
          
          return (
            <div key={step.name} className="rounded border">
              <button
                onClick={() => toggleStep(step.name)}
                className="flex w-full items-center justify-between p-2 text-left text-sm hover:bg-accent"
              >
                <div className="flex items-center gap-2">
                  {isExpanded ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                  <span className="font-medium">{step.name}</span>
                </div>
              </button>
              
              {isExpanded && (
                <div className="border-t p-2 text-xs">
                  <p className="text-muted-foreground mb-2">{step.description}</p>
                  
                  {Object.keys(step.inputs).length > 0 && (
                    <div className="mb-2">
                      <span className="font-medium">Inputs:</span>
                      <pre className="mt-1 text-xs bg-muted p-1 rounded">
                        {JSON.stringify(step.inputs, null, 2)}
                      </pre>
                    </div>
                  )}
                  
                  {Object.keys(step.outputs).length > 0 && (
                    <div>
                      <span className="font-medium">Outputs:</span>
                      <pre className="mt-1 text-xs bg-muted p-1 rounded">
                        {JSON.stringify(step.outputs, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}