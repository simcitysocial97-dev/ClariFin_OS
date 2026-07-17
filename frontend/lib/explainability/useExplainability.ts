/**
 * useExplainability - Hook for accessing explanation data
 *
 * Provides consistent access to explanations with state management.
 * No rendering - just data access.
 */

import { useMemo } from 'react'
import type { Explanation, RecommendationExplanation } from './contracts/Explanation'
import type { ConfidenceBps } from './contracts/Confidence'
import { confidenceToBadge } from './confidenceToBadge'
import type { BadgeLevel } from './confidenceToBadge'

/**
 * State of the explanation
 */
export type ExplanationState = 'loading' | 'empty' | 'available' | 'error'

/**
 * Return type for useExplainability
 */
export interface UseExplainabilityResult {
  readonly state: ExplanationState
  readonly explanation: Explanation | null
  readonly hasEvidence: boolean
  readonly confidenceBps: ConfidenceBps | null
  readonly confidenceLevel: BadgeLevel | null
}

/**
 * Hook for accessing a single explanation
 */
export function useExplainability(
  explanation: Explanation | null | undefined,
): UseExplainabilityResult {
  return useMemo(() => {
    if (explanation === undefined) {
      return {
        state: 'loading',
        explanation: null,
        hasEvidence: false,
        confidenceBps: null,
        confidenceLevel: null,
      }
    }

    if (explanation === null) {
      return {
        state: 'empty',
        explanation: null,
        hasEvidence: false,
        confidenceBps: null,
        confidenceLevel: null,
      }
    }

    return {
      state: 'available',
      explanation,
      hasEvidence: explanation.evidence.length > 0,
      confidenceBps: explanation.confidence.value,
      confidenceLevel: confidenceToBadge(explanation.confidence.value),
    }
  }, [explanation])
}

/**
 * Return type for useExplainabilityCollection
 */
export interface UseExplainabilityCollectionResult {
  readonly state: ExplanationState
  readonly explanations: Explanation[]
  readonly hasEvidence: boolean
  readonly totalConfidenceBps: ConfidenceBps | null
}

/**
 * Hook for accessing multiple explanations
 */
export function useExplainabilityCollection(
  explanations: Explanation[] | null | undefined,
): UseExplainabilityCollectionResult {
  return useMemo(() => {
    if (explanations === undefined) {
      return {
        state: 'loading',
        explanations: [],
        hasEvidence: false,
        totalConfidenceBps: null,
      }
    }

    if (explanations === null || explanations.length === 0) {
      return {
        state: 'empty',
        explanations: [],
        hasEvidence: false,
        totalConfidenceBps: null,
      }
    }

    const hasEvidence = explanations.some(e => e.evidence.length > 0)
    const avgConfidence = Math.round(
      explanations.reduce((sum, e) => sum + e.confidence.value, 0) / explanations.length,
    )

    return {
      state: 'available',
      explanations,
      hasEvidence,
      totalConfidenceBps: avgConfidence as ConfidenceBps,
    }
  }, [explanations])
}

/**
 * Return type for useRecommendationExplanation
 */
export interface UseRecommendationExplanationResult {
  readonly state: ExplanationState
  readonly recommendation: RecommendationExplanation | null
  readonly hasEvidence: boolean
  readonly confidenceBps: ConfidenceBps | null
  readonly confidenceLevel: BadgeLevel | null
}

/**
 * Hook for accessing a recommendation explanation
 */
export function useRecommendationExplanation(
  recommendation: RecommendationExplanation | null | undefined,
): UseRecommendationExplanationResult {
  return useMemo(() => {
    if (recommendation === undefined) {
      return {
        state: 'loading',
        recommendation: null,
        hasEvidence: false,
        confidenceBps: null,
        confidenceLevel: null,
      }
    }

    if (recommendation === null) {
      return {
        state: 'empty',
        recommendation: null,
        hasEvidence: false,
        confidenceBps: null,
        confidenceLevel: null,
      }
    }

    return {
      state: 'available',
      recommendation,
      hasEvidence: recommendation.evidence.length > 0,
      confidenceBps: recommendation.confidence.value,
      confidenceLevel: confidenceToBadge(recommendation.confidence.value),
    }
  }, [recommendation])
}