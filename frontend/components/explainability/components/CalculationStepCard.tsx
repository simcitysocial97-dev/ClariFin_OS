/**
 * CalculationStepCard - Display a single calculation step
 */

import {
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion'
import type { CalculationStep } from '@/lib/explainability'

interface CalculationStepCardProps {
  step: CalculationStep
}

/**
 * Get operation label for display
 */
function getOperationLabel(operation: string): string {
  const labels: Record<string, string> = {
    ADD: '+',
    SUBTRACT: '−',
    MULTIPLY: '×',
    DIVIDE: '÷',
    AVERAGE: 'avg',
    LOOKUP: 'lookup',
    FILTER: 'filter',
    GROUP: 'group',
    MATCH: 'match',
  }
  return labels[operation] ?? operation
}

/**
 * Display a single calculation step with expandable details
 */
export function CalculationStepCard({ step }: CalculationStepCardProps) {
  return (
    <AccordionItem value={step.stepId}>
      <AccordionTrigger>
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
            {getOperationLabel(step.operation)}
          </span>
          <span className="text-sm font-medium">{step.description}</span>
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <div className="space-y-2 pl-4">
          {step.inputIds.length > 0 && (
            <div>
              <p className="text-xs font-medium text-muted-foreground">Inputs:</p>
              <ul className="text-sm pl-4">
                {step.inputIds.map((id) => (
                  <li key={id} className="text-muted-foreground">
                    {id}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div>
            <p className="text-xs font-medium text-muted-foreground">Output:</p>
            <p className="text-sm">{step.outputId}</p>
          </div>
        </div>
      </AccordionContent>
    </AccordionItem>
  )
}