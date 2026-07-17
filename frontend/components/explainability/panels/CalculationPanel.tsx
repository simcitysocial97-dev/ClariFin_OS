/**
 * CalculationPanel - Calculation tab for explainability drawer
 *
 * Renders CalculationStep timeline with expandable details.
 */

import {
  Accordion,
} from '@/components/ui/accordion'
import { CalculationStepCard } from '../components/CalculationStepCard'
import type { Explanation } from '@/lib/explainability'

interface CalculationPanelProps {
  explanation: Explanation
}

/**
 * Display calculation steps as a timeline
 */
export function CalculationPanel({ explanation }: CalculationPanelProps) {
  const steps = explanation.calculationSteps

  if (steps.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No calculation steps available for this metric.
      </p>
    )
  }

  return (
    <Accordion type="multiple" className="w-full">
      {steps.map((step) => (
        <CalculationStepCard key={step.stepId} step={step} />
      ))}
    </Accordion>
  )
}