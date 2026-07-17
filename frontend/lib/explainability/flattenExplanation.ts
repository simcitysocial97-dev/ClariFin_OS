/**
 * flattenExplanation - Flatten nested explanation to linear form
 *
 * Useful for:
 * - Export
 * - Audit logs
 * - PDF generation
 * - Debugging
 * - Search
 */

import type { Explanation, RecommendationExplanation } from './contracts/Explanation'

/**
 * Flattened explanation item
 */
export interface FlattenedItem {
  readonly id: string
  readonly type: 'metric' | 'evidence' | 'source' | 'calculation'
  readonly description: string
  readonly value?: unknown
  readonly order?: number
}

/**
 * Flatten an explanation to a linear array
 */
export function flattenExplanation(
  explanation: Explanation,
): FlattenedItem[] {
  const result: FlattenedItem[] = []

  // Add metric
  result.push({
    id: `metric-${explanation.metric}`,
    type: 'metric',
    description: explanation.metric,
    value: explanation.value,
  })

  // Add evidence
  for (const evidence of explanation.evidence) {
    result.push({
      id: evidence.id,
      type: 'evidence',
      description: evidence.description,
      value: evidence.value,
    })
  }

  // Add sources
  for (const source of explanation.sources) {
    result.push({
      id: `source-${source.sourceType}-${source.recordId ?? source.statementId ?? source.transactionId ?? 'unknown'}`,
      type: 'source',
      description: source.description ?? `${source.sourceType}:${source.recordId ?? source.statementId ?? source.transactionId ?? 'unknown'}`,
    })
  }

  // Add calculation steps
  for (const step of explanation.calculationSteps) {
    result.push({
      id: step.stepId,
      type: 'calculation',
      description: step.description,
      order: step.order,
    })
  }

  return result
}

/**
 * Flatten a recommendation explanation
 */
export function flattenRecommendationExplanation(
  explanation: RecommendationExplanation,
): FlattenedItem[] {
  const result: FlattenedItem[] = []

  // Add recommendation
  result.push({
    id: `recommendation-${explanation.recommendation}`,
    type: 'metric',
    description: explanation.recommendation,
    value: explanation.impact.value,
  })

  // Add evidence
  for (const evidence of explanation.evidence) {
    result.push({
      id: evidence.id,
      type: 'evidence',
      description: evidence.description,
      value: evidence.value,
    })
  }

  // Add sources
  for (const source of explanation.sources) {
    result.push({
      id: `source-${source.sourceType}-${source.recordId ?? source.statementId ?? source.transactionId ?? 'unknown'}`,
      type: 'source',
      description: source.description ?? `${source.sourceType}:${source.recordId ?? source.statementId ?? source.transactionId ?? 'unknown'}`,
    })
  }

  return result
}
