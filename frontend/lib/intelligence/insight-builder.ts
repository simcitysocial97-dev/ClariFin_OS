/**
 * Insight Builder - Stage 6 Financial Intelligence Engine
 *
 * Utility for building evidence chains, calculation steps, and insight objects.
 * Ensures every insight includes evidence, calculation, confidence, source, and related graph nodes.
 *
 * All engines use this builder to produce consistent, explainable insights.
 */

import type {
  EvidenceChain,
  EvidenceItem,
  CalculationStep,
  SourceReference,
  Insight,
  Alert,
  Recommendation,
  RiskScore,
  OpportunityScore,
  Goal,
  HealthScore,
  HealthDimension,
  Severity,
  Priority,
  AlertType,
  RecommendationType,
  RiskCategory,
  OpportunityCategory,
  GoalCategory,
  InsightType,
} from './types';

// ===== Insight Builder =====
export class InsightBuilder {
  /**
   * Build an evidence chain from evidence items and calculation steps
   */
  buildEvidenceChain(
    summary: string,
    evidence: EvidenceItem[],
    calculationSteps: CalculationStep[],
    sourceReferences: SourceReference[],
    confidenceScore: number,
  ): EvidenceChain {
    return {
      summary,
      evidence,
      calculation_steps: calculationSteps,
      source_references: sourceReferences,
      confidence_score: Math.max(0, Math.min(100, confidenceScore)),
    };
  }

  /**
   * Create an evidence item
   */
  createEvidence(
    type: string,
    summary: string,
    source: string,
    confidence?: number,
  ): EvidenceItem {
    return {
      type,
      summary,
      source,
      ...(confidence !== undefined ? { confidence: Math.max(0, Math.min(100, confidence)) } : {}),
    };
  }

  /**
   * Create a calculation step
   */
  createCalculationStep(
    name: string,
    description: string,
    inputs: Record<string, unknown>,
    outputs: Record<string, unknown>,
  ): CalculationStep {
    return {
      name,
      description,
      inputs,
      outputs,
    };
  }

  /**
   * Create a source reference
   */
  createSourceReference(
    id: string,
    type: string,
    label: string,
    timestamp: string,
  ): SourceReference {
    return {
      id,
      type,
      label,
      timestamp,
    };
  }

  /**
   * Build an insight object with all required fields
   */
  buildInsight(
    id: string,
    type: InsightType,
    severity: Severity,
    priority: Priority,
    confidence: number,
    summary: string,
    description: string,
    calculation: string,
    source: string,
    evidence: EvidenceChain,
    recommendedActions: string[],
    relatedNodes: string[],
    options?: {
      deepLink?: string;
      valuePaise?: number;
      scoreBps?: number;
    },
  ): Insight {
    return {
      id,
      type,
      severity,
      priority,
      confidence: Math.max(0, Math.min(100, confidence)),
      summary,
      description,
      evidence,
      calculation,
      source,
      recommended_actions: recommendedActions,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
      ...(options?.valuePaise !== undefined ? { value_paise: options.valuePaise } : {}),
      ...(options?.scoreBps !== undefined ? { score_bps: options.scoreBps } : {}),
    };
  }

  /**
   * Build an alert object
   */
  buildAlert(
    id: string,
    type: AlertType,
    severity: Severity,
    priority: Priority,
    title: string,
    message: string,
    evidence: EvidenceChain,
    source: string,
    relatedNodes: string[],
    options?: {
      deepLink?: string;
      requiresAcknowledgement?: boolean;
      expiresAt?: string;
    },
  ): Alert {
    return {
      id,
      type,
      severity,
      priority,
      title,
      message,
      evidence,
      source,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
      requires_acknowledgement: options?.requiresAcknowledgement ?? false,
      acknowledged: false,
      timestamp: new Date().toISOString(),
      ...(options?.expiresAt ? { expires_at: options.expiresAt } : {}),
    };
  }

  /**
   * Build a recommendation object
   */
  buildRecommendation(
    id: string,
    type: RecommendationType,
    severity: Severity,
    priority: Priority,
    title: string,
    reason: string,
    metric: string,
    suggestedAction: string,
    evidence: EvidenceChain,
    source: string,
    relatedNodes: string[],
    options?: {
      deepLink?: string;
    },
  ): Recommendation {
    return {
      id,
      type,
      severity,
      priority,
      title,
      reason,
      metric,
      suggested_action: suggestedAction,
      evidence,
      source,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
    };
  }

  /**
   * Build a risk score object
   */
  buildRiskScore(
    id: string,
    category: RiskCategory,
    score: number,
    confidence: number,
    factors: RiskScore['factors'],
    evidence: EvidenceChain,
    relatedNodes: string[],
    options?: {
      deepLink?: string;
    },
  ): RiskScore {
    return {
      id,
      category,
      score: Math.max(0, Math.min(100, score)),
      confidence: Math.max(0, Math.min(100, confidence)),
      factors,
      evidence,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
    };
  }

  /**
   * Build an opportunity score object
   */
  buildOpportunityScore(
    id: string,
    category: OpportunityCategory,
    score: number,
    confidence: number,
    potentialImpact: string,
    evidence: EvidenceChain,
    relatedNodes: string[],
    options?: {
      deepLink?: string;
      estimatedBenefitPaise?: number;
    },
  ): OpportunityScore {
    return {
      id,
      category,
      score: Math.max(0, Math.min(100, score)),
      confidence: Math.max(0, Math.min(100, confidence)),
      potential_impact: potentialImpact,
      evidence,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
      ...(options?.estimatedBenefitPaise !== undefined
        ? { estimated_benefit_paise: options.estimatedBenefitPaise }
        : {}),
    };
  }

  /**
   * Build a goal object
   */
  buildGoal(
    id: string,
    category: GoalCategory,
    title: string,
    targetPaise: number,
    currentPaise: number,
    startDate: string,
    targetDate: string,
    velocityPaisePerMonth: number,
    requiredVelocityPaisePerMonth: number,
    evidence: EvidenceChain,
    relatedNodes: string[],
    options?: {
      deepLink?: string;
    },
  ): Goal {
    const progressPercentage = targetPaise > 0
      ? Math.min(100, Math.max(0, (currentPaise / targetPaise) * 100))
      : 0;
    const onTrack = velocityPaisePerMonth >= requiredVelocityPaisePerMonth;

    return {
      id,
      category,
      title,
      target_paise: targetPaise,
      current_paise: currentPaise,
      start_date: startDate,
      target_date: targetDate,
      progress_percentage: Math.round(progressPercentage * 100) / 100,
      velocity_paise_per_month: velocityPaisePerMonth,
      required_velocity_paise_per_month: requiredVelocityPaisePerMonth,
      on_track: onTrack,
      evidence,
      related_nodes: relatedNodes,
      ...(options?.deepLink ? { deep_link: options.deepLink } : {}),
    };
  }

  /**
   * Build a health score object
   */
  buildHealthScore(
    overall: number,
    dimensions: HealthDimension[],
    evidence: EvidenceChain,
    relatedNodes: string[],
  ): HealthScore {
    return {
      overall: Math.max(0, Math.min(100, overall)),
      dimensions,
      evidence,
      related_nodes: relatedNodes,
    };
  }

  /**
   * Build a health dimension
   */
  buildHealthDimension(
    name: string,
    score: number,
    factors: string[],
  ): HealthDimension {
    const clampedScore = Math.max(0, Math.min(100, score));
    let label: string;
    if (clampedScore >= 70) {
      label = 'Healthy';
    } else if (clampedScore >= 40) {
      label = 'Warning';
    } else {
      label = 'Critical';
    }

    return {
      name,
      score: clampedScore,
      label,
      factors,
    };
  }

  /**
   * Determine severity from a score (0-100)
   * Lower scores = higher severity for negative metrics
   * Higher scores = higher severity for positive metrics (if invert is true)
   */
  scoreToSeverity(score: number, invert: boolean = false): Severity {
    const adjustedScore = invert ? 100 - score : score;
    if (adjustedScore >= 80) return 'info';
    if (adjustedScore >= 60) return 'low';
    if (adjustedScore >= 40) return 'medium';
    if (adjustedScore >= 20) return 'high';
    return 'critical';
  }

  /**
   * Determine priority from a score (0-100)
   * Lower scores = higher priority
   */
  scoreToPriority(score: number, invert: boolean = false): Priority {
    const adjustedScore = invert ? 100 - score : score;
    if (adjustedScore >= 80) return 5;
    if (adjustedScore >= 60) return 4;
    if (adjustedScore >= 40) return 3;
    if (adjustedScore >= 20) return 2;
    return 1;
  }
}

// ===== Convenience Export =====
export const insightBuilder = new InsightBuilder();