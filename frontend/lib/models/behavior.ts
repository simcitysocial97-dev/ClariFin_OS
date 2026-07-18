/**
 * Behavior Model - Domain-friendly ViewModel for UI consumption
 *
 * IMPORTANT: This model contains only raw numeric values and UI flags.
 * Formatting is handled by components using formatINR() etc.
 * This keeps the mapper pure and presentation-agnostic.
 */

import type { Explanation } from '@/lib/explainability'

/**
 * Wellness component for UI consumption
 */
export interface WellnessComponentModel {
  name: string
  score: number
  weight: number
}

/**
 * Wellness score response for UI consumption
 */
export interface WellnessScoreModel {
  score: number
  band: 'Excellent' | 'Healthy' | 'Developing' | 'Risk' | 'Critical'
  components: WellnessComponentModel[]
  snapshotDate: string
  version: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}

/**
 * Behavior insight for UI consumption
 */
export interface BehaviorInsightModel {
  type: string
  title: string
  message: string
  metric: string
  value: number | null
}

/**
 * Nudge for UI consumption
 */
export interface NudgeModel {
  type: string
  title: string
  message: string
  priority: number
}

/**
 * Behavior insights response for UI consumption
 */
export interface BehaviorInsightsModel {
  insights: BehaviorInsightModel[]
  nudges: NudgeModel[]
  topNudge: NudgeModel | null
  summary: string
  financialHealthScore: number | null
  confidence: number | null
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}

/**
 * Pattern summary for UI consumption
 */
export interface PatternSummaryModel {
  patternType: string
  patternKey: string
  strengthBps: number
  transactionCount: number
  totalAmountPaise: number
  firstObserved: string
  lastObserved: string
}

/**
 * Patterns response for UI consumption
 */
export interface PatternsModel {
  patterns: PatternSummaryModel[]
  totalPatterns: number
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}

/**
 * Recommendation for UI consumption
 */
export interface RecommendationModel {
  title: string
  reason: string
  metric: string
  severity: string
  suggestedAction: string
}

/**
 * Recommendations response for UI consumption
 */
export interface RecommendationsModel {
  recommendations: RecommendationModel[]
  totalCount: number
  snapshotDate: string
  isPartial: boolean
  partialReason: string | null
  lastUpdated: string | null
  explanation: Explanation | null
}