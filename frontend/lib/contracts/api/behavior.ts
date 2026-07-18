/**
 * Behavior API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 */

import { z } from 'zod'

// Re-export shared schemas from networth (they are canonical)
export type {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
} from './networth'

// Wellness component schema
const WellnessComponentSchema = z.object({
  name: z.string(),
  score: z.number().int(),
  weight: z.number(),
})

// Wellness score response schema
export const WellnessScoreResponseSchema = z.object({
  score: z.number().int(),
  band: z.enum(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']),
  components: z.array(WellnessComponentSchema),
  snapshot_date: z.string(),
  version: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

// Behavior insight schema
const BehaviorInsightSchema = z.object({
  type: z.string(),
  title: z.string(),
  message: z.string(),
  metric: z.string(),
  value: z.number().nullable(),
})

// Nudge schema
const NudgeSchema = z.object({
  type: z.string(),
  title: z.string(),
  message: z.string(),
  priority: z.number().int(),
})

// Behavior insights response schema
export const BehaviorInsightsResponseSchema = z.object({
  insights: z.array(BehaviorInsightSchema),
  nudges: z.array(NudgeSchema),
  top_nudge: NudgeSchema.nullable(),
  summary: z.string(),
  financial_health_score: z.number().int().nullable(),
  confidence: z.number().int().nullable(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

// Pattern summary schema
const PatternSummarySchema = z.object({
  pattern_type: z.string(),
  pattern_key: z.string(),
  strength_bps: z.number().int(),
  transaction_count: z.number().int(),
  total_amount_paise: z.number().int(),
  first_observed: z.string(),
  last_observed: z.string(),
})

// Patterns response schema
export const PatternsResponseSchema = z.object({
  patterns: z.array(PatternSummarySchema),
  total_patterns: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

// Recommendation response schema
const RecommendationResponseSchema = z.object({
  title: z.string(),
  reason: z.string(),
  metric: z.string(),
  severity: z.string(),
  suggested_action: z.string(),
})

// Recommendations response schema
export const RecommendationsResponseSchema = z.object({
  recommendations: z.array(RecommendationResponseSchema),
  total_count: z.number().int(),
  snapshot_date: z.string(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: z.any().optional(),
})

export type WellnessComponentDto = z.infer<typeof WellnessComponentSchema>
export type WellnessScoreResponseDto = z.infer<typeof WellnessScoreResponseSchema>
export type BehaviorInsightDto = z.infer<typeof BehaviorInsightSchema>
export type NudgeDto = z.infer<typeof NudgeSchema>
export type BehaviorInsightsResponseDto = z.infer<typeof BehaviorInsightsResponseSchema>
export type PatternSummaryDto = z.infer<typeof PatternSummarySchema>
export type PatternsResponseDto = z.infer<typeof PatternsResponseSchema>
export type RecommendationResponseDto = z.infer<typeof RecommendationResponseSchema>
export type RecommendationsResponseDto = z.infer<typeof RecommendationsResponseSchema>