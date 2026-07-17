/**
 * createExplanation - Factory for creating Explanation objects
 *
 * Creates immutable, serializable explanations.
 */

import type { Explanation, RecommendationExplanation } from './contracts/Explanation'
import type { Evidence } from './contracts/Evidence'
import type { SourceReference } from './contracts/SourceReference'
import type { CalculationStep } from './contracts/CalculationStep'
import { createConfidence } from './contracts/Confidence'

/**
 * Create an explanation for a financial metric
 */
export function createExplanation(
  metric: string,
  value: number,
  confidenceBps: number,
  options?: {
    confidenceReason?: string
    evidence?: Evidence[]
    sources?: SourceReference[]
    calculationSteps?: CalculationStep[]
  },
): Explanation {
  const confidence = createConfidence(confidenceBps, options?.confidenceReason)

  return {
    metric,
    value,
    confidence,
    evidence: options?.evidence ?? [],
    sources: options?.sources ?? [],
    calculationSteps: options?.calculationSteps ?? [],
  }
}

/**
 * Create a recommendation explanation
 */
export function createRecommendationExplanation(
  recommendation: string,
  rationale: string,
  confidenceBps: number,
  impact: { value: number; unit: 'paise' | 'bps' | 'count' },
  options?: {
    confidenceReason?: string
    evidence?: Evidence[]
    sources?: SourceReference[]
  },
): RecommendationExplanation {
  const confidence = createConfidence(confidenceBps, options?.confidenceReason)

  return {
    recommendation,
    rationale,
    confidence,
    evidence: options?.evidence ?? [],
    sources: options?.sources ?? [],
    impact,
  }
}