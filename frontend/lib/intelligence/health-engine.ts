/**
 * Health Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic financial health scoring engine.
 * Computes overall health score from multiple dimensions:
 * - Savings discipline
 * - Spending stability
 * - Liquidity adequacy
 * - Debt health
 * - Income stability
 *
 * Every score includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Insight,
  HealthDimension,
  EvidenceChain,
  EvidenceItem,
  CalculationStep,
  SourceReference,
} from './types';
import { insightBuilder } from './insight-builder';

// ===== Health Engine =====
export class HealthEngine implements IntelligenceEngine {
  readonly name = 'health' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const nodes = context.nodes;

    // Extract financial metrics from graph nodes
    const metrics = this.extractMetrics(nodes);

    // Compute dimension scores
    const savingsDimension = this.computeSavingsDimension(metrics, nodes);
    const stabilityDimension = this.computeStabilityDimension(metrics, nodes);
    const liquidityDimension = this.computeLiquidityDimension(metrics, nodes);
    const debtDimension = this.computeDebtDimension(metrics, nodes);
    const incomeDimension = this.computeIncomeDimension(metrics, nodes);

    const dimensions: HealthDimension[] = [
      savingsDimension,
      stabilityDimension,
      liquidityDimension,
      debtDimension,
      incomeDimension,
    ];

    // Compute overall health score (weighted average)
    const overall = this.computeOverallScore(dimensions);

    // Build evidence chain
    const evidence = this.buildHealthEvidence(dimensions, overall, nodes);
    const relatedNodes = nodes.map(n => n.id);

    const healthScore = insightBuilder.buildHealthScore(
      overall,
      dimensions,
      evidence,
      relatedNodes,
    );

    // Generate insights from health dimensions
    for (const dim of dimensions) {
      if (dim.score < 40) {
        const insight = insightBuilder.buildInsight(
          `health-${dim.name.toLowerCase().replace(/\s+/g, '-')}`,
          'health',
          dim.score < 20 ? 'critical' : 'high',
          dim.score < 20 ? 1 : 2,
          evidence.confidence_score,
          `${dim.name} Needs Attention`,
          `Your ${dim.name.toLowerCase()} score is ${dim.score.toFixed(0)}/100. ${dim.factors.join('. ')}`,
          `Weighted average of ${dim.name.toLowerCase()} factors`,
          'health',
          evidence,
          [`Improve ${dim.name.toLowerCase()} by addressing contributing factors`],
          relatedNodes,
          { scoreBps: Math.round(dim.score * 100) },
        );
        insights.push(insight);
      } else if (dim.score >= 70) {
        const insight = insightBuilder.buildInsight(
          `health-${dim.name.toLowerCase().replace(/\s+/g, '-')}-positive`,
          'health',
          'info',
          5,
          evidence.confidence_score,
          `Strong ${dim.name}`,
          `Your ${dim.name.toLowerCase()} score is ${dim.score.toFixed(0)}/100. Maintain this healthy behavior.`,
          `Weighted average of ${dim.name.toLowerCase()} factors`,
          'health',
          evidence,
          ['Continue current financial habits'],
          relatedNodes,
          { scoreBps: Math.round(dim.score * 100) },
        );
        insights.push(insight);
      }
    }

    return {
      insights,
      alerts: [],
      recommendations: [],
      risk_scores: [],
      opportunity_scores: [],
      goals: [],
      health_score: healthScore,
    };
  }

  reset(): void {
    // No state to reset
  }

  // ===== Private Methods =====

  private extractMetrics(nodes: IntelligenceContext['nodes']): Record<string, number> {
    const metrics: Record<string, number> = {};

    for (const node of nodes) {
      const meta = node.metadata;

      // Extract savings rate
      if (meta.savings_rate_bps !== undefined) {
        metrics.savingsRateBps = meta.savings_rate_bps as number;
      }
      if (meta.savings_paise !== undefined) {
        metrics.savingsPaise = meta.savings_paise as number;
      }
      if (meta.income_paise !== undefined) {
        metrics.incomePaise = meta.income_paise as number;
      }

      // Extract debt metrics
      if (meta.debt_to_income_bps !== undefined) {
        metrics.debtToIncomeBps = meta.debt_to_income_bps as number;
      }
      if (meta.total_debt_paise !== undefined) {
        metrics.totalDebtPaise = meta.total_debt_paise as number;
      }
      if (meta.health_score !== undefined) {
        metrics.debtHealthScore = meta.health_score as number;
      }

      // Extract spending patterns
      if (meta.percentage !== undefined) {
        metrics.spendingPercentage = meta.percentage as number;
      }
      if (meta.trend !== undefined) {
        metrics.spendingTrend = typeof meta.trend === 'string'
          ? (meta.trend === 'increasing' ? 1 : meta.trend === 'decreasing' ? -1 : 0)
          : (meta.trend as number);
      }

      // Extract behaviour scores
      if (meta.score_bps !== undefined) {
        metrics.behaviourScoreBps = meta.score_bps as number;
      }
      if (meta.score !== undefined) {
        metrics.behaviourScore = meta.score as number;
      }

      // Extract wellness factors
      if (meta.factors !== undefined && Array.isArray(meta.factors)) {
        metrics.wellnessFactorCount = meta.factors.length;
      }
    }

    return metrics;
  }

  private computeSavingsDimension(
    metrics: Record<string, number>,
    _nodes: IntelligenceContext['nodes'],
  ): HealthDimension {
    const factors: string[] = [];
    let score = 50; // Default neutral score

    // Savings rate (bps: 0-10000)
    if (metrics.savingsRateBps !== undefined) {
      const rate = metrics.savingsRateBps / 100; // Convert to percentage
      if (rate >= 20) {
        score = 80;
        factors.push(`Savings rate of ${rate.toFixed(1)}% exceeds 20% target`);
      } else if (rate >= 10) {
        score = 60;
        factors.push(`Savings rate of ${rate.toFixed(1)}% is moderate`);
      } else if (rate > 0) {
        score = 40;
        factors.push(`Savings rate of ${rate.toFixed(1)}% is below 10% target`);
      } else {
        score = 20;
        factors.push('No positive savings rate detected');
      }
    } else {
      factors.push('Insufficient data for savings rate calculation');
    }

    // Savings consistency
    if (metrics.behaviourScore !== undefined) {
      const behaviourScore = metrics.behaviourScore;
      if (behaviourScore > 0.6) {
        score = Math.min(100, score + 10);
        factors.push('Consistent savings behavior detected');
      } else if (behaviourScore < 0.3) {
        score = Math.max(0, score - 10);
        factors.push('Inconsistent savings behavior');
      }
    }

    return insightBuilder.buildHealthDimension('Savings', score, factors);
  }

  private computeStabilityDimension(
    metrics: Record<string, number>,
    _nodes: IntelligenceContext['nodes'],
  ): HealthDimension {
    const factors: string[] = [];
    let score = 50;

    // Spending stability
    if (metrics.spendingTrend !== undefined) {
      if (metrics.spendingTrend === 0) {
        score = 70;
        factors.push('Spending patterns are stable');
      } else if (metrics.spendingTrend < 0) {
        score = 60;
        factors.push('Spending is decreasing, which is positive');
      } else {
        score = 40;
        factors.push('Spending is increasing, monitor for sustainability');
      }
    } else {
      factors.push('Insufficient data for stability analysis');
    }

    // Behaviour score as proxy for stability
    if (metrics.behaviourScoreBps !== undefined) {
      const bps = metrics.behaviourScoreBps;
      if (bps >= 7000) {
        score = Math.min(100, score + 15);
        factors.push('Strong behavioral stability indicators');
      } else if (bps < 4000) {
        score = Math.max(0, score - 15);
        factors.push('Behavioral stability needs improvement');
      }
    }

    return insightBuilder.buildHealthDimension('Stability', score, factors);
  }

  private computeLiquidityDimension(
    _metrics: Record<string, number>,
    nodes: IntelligenceContext['nodes'],
  ): HealthDimension {
    const factors: string[] = [];
    let score = 50;

    // Look for liquidity-related nodes
    const liquidityNodes = nodes.filter(n =>
      n.type === 'behaviour_score' &&
      n.metadata?.score_bps !== undefined
    );

    if (liquidityNodes.length > 0) {
      // Use behaviour score as proxy for liquidity
      const avgScore = liquidityNodes.reduce((sum, n) => sum + (n.confidence ?? 50), 0) / liquidityNodes.length;
      if (avgScore >= 70) {
        score = 70;
        factors.push('Adequate financial buffer detected');
      } else if (avgScore >= 40) {
        score = 45;
        factors.push('Moderate financial buffer');
      } else {
        score = 25;
        factors.push('Low financial buffer, consider building emergency fund');
      }
    } else {
      factors.push('Insufficient data for liquidity assessment');
    }

    return insightBuilder.buildHealthDimension('Liquidity', score, factors);
  }

  private computeDebtDimension(
    metrics: Record<string, number>,
    _nodes: IntelligenceContext['nodes'],
  ): HealthDimension {
    const factors: string[] = [];
    let score = 50;

    // Debt-to-income ratio
    if (metrics.debtToIncomeBps !== undefined) {
      const dti = metrics.debtToIncomeBps / 100; // Convert to percentage
      if (dti <= 20) {
        score = 80;
        factors.push(`Debt-to-income ratio of ${dti.toFixed(1)}% is healthy`);
      } else if (dti <= 40) {
        score = 55;
        factors.push(`Debt-to-income ratio of ${dti.toFixed(1)}% is manageable`);
      } else if (dti <= 60) {
        score = 35;
        factors.push(`Debt-to-income ratio of ${dti.toFixed(1)}% is elevated`);
      } else {
        score = 20;
        factors.push(`Debt-to-income ratio of ${dti.toFixed(1)}% is critical`);
      }
    } else {
      factors.push('No debt data available');
    }

    // Debt health score
    if (metrics.debtHealthScore !== undefined) {
      const health = metrics.debtHealthScore;
      if (health >= 7000) {
        score = Math.min(100, score + 10);
        factors.push('Debt health indicators are positive');
      } else if (health < 4000) {
        score = Math.max(0, score - 10);
        factors.push('Debt health needs attention');
      }
    }

    return insightBuilder.buildHealthDimension('Debt', score, factors);
  }

  private computeIncomeDimension(
    metrics: Record<string, number>,
    nodes: IntelligenceContext['nodes'],
  ): HealthDimension {
    const factors: string[] = [];
    let score = 50;

    // Income sufficiency
    if (metrics.incomePaise !== undefined && metrics.savingsPaise !== undefined) {
      const savingsRate = metrics.incomePaise > 0
        ? metrics.savingsPaise / metrics.incomePaise
        : 0;

      if (savingsRate > 0.2) {
        score = 75;
        factors.push('Income comfortably exceeds expenses');
      } else if (savingsRate > 0) {
        score = 55;
        factors.push('Income exceeds expenses with modest savings');
      } else {
        score = 30;
        factors.push('Expenses may exceed income');
      }
    } else {
      factors.push('Insufficient income data');
    }

    // Income stability from transaction patterns
    const incomeNodes = nodes.filter(n => n.type === 'transaction' && n.value_paise && n.value_paise > 0);
    if (incomeNodes.length >= 3) {
      score = Math.min(100, score + 10);
      factors.push('Regular income pattern detected');
    }

    return insightBuilder.buildHealthDimension('Income', score, factors);
  }

  private computeOverallScore(dimensions: HealthDimension[]): number {
    if (dimensions.length === 0) return 0;

    // Weights: Savings 25%, Stability 20%, Liquidity 20%, Debt 20%, Income 15%
    const weights: Record<string, number> = {
      'Savings': 0.25,
      'Stability': 0.20,
      'Liquidity': 0.20,
      'Debt': 0.20,
      'Income': 0.15,
    };

    let weightedSum = 0;
    let totalWeight = 0;

    for (const dim of dimensions) {
      const weight = weights[dim.name] ?? 0.2;
      weightedSum += dim.score * weight;
      totalWeight += weight;
    }

    return totalWeight > 0 ? Math.round(weightedSum / totalWeight) : 0;
  }

  private buildHealthEvidence(
    dimensions: HealthDimension[],
    overall: number,
    nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence: EvidenceItem[] = [];
    const calculationSteps: CalculationStep[] = [];
    const sourceReferences: SourceReference[] = [];

    // Add evidence for each dimension
    for (const dim of dimensions) {
      evidence.push(insightBuilder.createEvidence(
        'health_dimension',
        `${dim.name}: ${dim.score.toFixed(0)}/100 - ${dim.label}`,
        'health-engine',
        dim.score,
      ));

      calculationSteps.push(insightBuilder.createCalculationStep(
        `Compute ${dim.name}`,
        `Calculate ${dim.name.toLowerCase()} health dimension score`,
        { factors: dim.factors },
        { score: dim.score, label: dim.label },
      ));
    }

    // Add overall calculation
    calculationSteps.push(insightBuilder.createCalculationStep(
      'Compute Overall Health',
      'Weighted average of all health dimensions',
      {
        dimensions: dimensions.map(d => ({ name: d.name, score: d.score })),
        weights: { Savings: 0.25, Stability: 0.20, Liquidity: 0.20, Debt: 0.20, Income: 0.15 },
      },
      { overall_score: overall },
    ));

    // Add source references
    for (const node of nodes.slice(0, 5)) {
      sourceReferences.push(insightBuilder.createSourceReference(
        node.id,
        'graph_node',
        node.label,
        node.date ?? new Date().toISOString(),
      ));
    }

    return insightBuilder.buildEvidenceChain(
      `Financial health score: ${overall.toFixed(0)}/100 across ${dimensions.length} dimensions`,
      evidence,
      calculationSteps,
      sourceReferences,
      overall,
    );
  }
}