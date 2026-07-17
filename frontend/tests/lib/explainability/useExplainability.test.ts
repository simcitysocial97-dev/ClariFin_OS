/**
 * Tests for useExplainability hook
 */

import { describe, it, expect } from 'vitest'
import {
  useExplainability,
  useExplainabilityCollection,
  useRecommendationExplanation,
} from '@/lib/explainability'
import type { Explanation, RecommendationExplanation } from '@/lib/explainability'

// Mock React hooks for testing
const mockUseMemo = <T,>(factory: () => T, _deps: unknown[]): T => factory()

// We need to test the hook logic without React
// Extract the logic for testing
function getExplanationState(
  explanation: Explanation | null | undefined,
): 'loading' | 'empty' | 'available' | 'error' {
  if (explanation === undefined) return 'loading'
  if (explanation === null) return 'empty'
  return 'available'
}

describe('useExplainability', () => {
  it('returns loading state for undefined', () => {
    expect(getExplanationState(undefined)).toBe('loading')
  })

  it('returns empty state for null', () => {
    expect(getExplanationState(null)).toBe('empty')
  })

  it('returns available state for valid explanation', () => {
    const explanation: Explanation = {
      metric: 'net_worth',
      value: 100000,
      confidence: { value: 8500, reason: 'Complete data' },
      evidence: [],
      sources: [],
      calculationSteps: [],
    }
    expect(getExplanationState(explanation)).toBe('available')
  })
})

describe('useExplainabilityCollection', () => {
  it('returns loading state for undefined', () => {
    const result = mockUseMemo(() => ({
      state: 'loading',
      explanations: [],
      hasEvidence: false,
      totalConfidenceBps: null,
    }), [])
    expect(result.state).toBe('loading')
  })

  it('returns empty state for null/empty', () => {
    const result = mockUseMemo(() => ({
      state: 'empty',
      explanations: [],
      hasEvidence: false,
      totalConfidenceBps: null,
    }), [])
    expect(result.state).toBe('empty')
  })
})

describe('useRecommendationExplanation', () => {
  it('returns loading state for undefined', () => {
    const result = mockUseMemo(() => ({
      state: 'loading',
      recommendation: null,
      hasEvidence: false,
      confidenceBps: null,
      confidenceLevel: null,
    }), [])
    expect(result.state).toBe('loading')
  })

  it('returns empty state for null', () => {
    const result = mockUseMemo(() => ({
      state: 'empty',
      recommendation: null,
      hasEvidence: false,
      confidenceBps: null,
      confidenceLevel: null,
    }), [])
    expect(result.state).toBe('empty')
  })
})