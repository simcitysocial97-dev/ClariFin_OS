/**
 * Behavior Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 *
 * IMPORTANT: The explanation is PRESERVED from the backend, not generated.
 * The backend is the source of truth for all explainability data.
 */

import type {
  WellnessScoreResponseDto,
  BehaviorInsightsResponseDto,
  PatternsResponseDto,
  RecommendationsResponseDto,
} from '../contracts/api/behavior'
import type {
  WellnessScoreModel,
  BehaviorInsightsModel,
  PatternsModel,
  RecommendationsModel,
} from '../models/behavior'

/**
 * Map WellnessScore DTO to Model
 *
 * Transformation rules:
 * - Convert from basis points (0-10000) to score (0-100)
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapWellnessScoreToModel(dto: WellnessScoreResponseDto): WellnessScoreModel {
  return {
    // Convert from basis points (0-10000) to score (0-100)
    score: dto.score / 100,
    band: dto.band,
    components: dto.components.map((c) => ({
      name: c.name,
      // Convert from basis points (0-10000) to score (0-100)
      score: c.score / 100,
      weight: c.weight,
    })),
    snapshotDate: dto.snapshot_date,
    version: dto.version,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

/**
 * Map BehaviorInsights DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapBehaviorInsightsToModel(dto: BehaviorInsightsResponseDto): BehaviorInsightsModel {
  return {
    insights: dto.insights.map((i) => ({
      type: i.type,
      title: i.title,
      message: i.message,
      metric: i.metric,
      value: i.value,
    })),
    nudges: dto.nudges.map((n) => ({
      type: n.type,
      title: n.title,
      message: n.message,
      priority: n.priority,
    })),
    topNudge: dto.top_nudge
      ? {
          type: dto.top_nudge.type,
          title: dto.top_nudge.title,
          message: dto.top_nudge.message,
          priority: dto.top_nudge.priority,
        }
      : null,
    summary: dto.summary,
    financialHealthScore: dto.financial_health_score,
    confidence: dto.confidence,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

/**
 * Map Patterns DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapPatternsToModel(dto: PatternsResponseDto): PatternsModel {
  return {
    patterns: dto.patterns.map((p) => ({
      patternType: p.pattern_type,
      patternKey: p.pattern_key,
      strengthBps: p.strength_bps,
      transactionCount: p.transaction_count,
      totalAmountPaise: p.total_amount_paise,
      firstObserved: p.first_observed,
      lastObserved: p.last_observed,
    })),
    totalPatterns: dto.total_patterns,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

/**
 * Map Recommendations DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapRecommendationsToModel(dto: RecommendationsResponseDto): RecommendationsModel {
  return {
    recommendations: dto.recommendations.map((r) => ({
      title: r.title,
      reason: r.reason,
      metric: r.metric,
      severity: r.severity,
      suggestedAction: r.suggested_action,
    })),
    totalCount: dto.total_count,
    snapshotDate: dto.snapshot_date,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { WellnessScoreModel, BehaviorInsightsModel, PatternsModel, RecommendationsModel }