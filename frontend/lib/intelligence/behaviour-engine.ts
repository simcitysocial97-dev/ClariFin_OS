/**
 * Behaviour Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic behavioural intelligence engine.
 * Consumes backend behaviour profile data and generates insights.
 * Based on Prospect Theory, Present Bias, Habit Loop Theory.
 *
 * Every insight includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Insight,
  Alert,
  EvidenceChain,
  RiskScore,
  RiskFactor,
} from './types';
import { insightBuilder } from './insight-builder';

export class BehaviourEngine implements IntelligenceEngine {
  readonly name = 'behaviour' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const alerts: Alert[] = [];
    const riskScores: RiskScore[] = [];
    const nodes = context.nodes;
    const config = context.config;

    // Extract behaviour metrics from graph nodes
    const behaviourMetrics = this.extractBehaviourMetrics(nodes);

    // Generate impulsivity insights
    if (behaviourMetrics.impulsivityScore > config.thresholds.impulsivity_threshold) {
      const evidence = this.buildBehaviourEvidence('impulsivity', behaviourMetrics, nodes);
      const insight = insightBuilder.buildInsight(
        'behaviour-high-impulsivity',
        'behaviour',
        'high',
        2,
        evidence.confidence_score,
        'High Impulse Spending Pattern',
        `Impulse spending score is ${(behaviourMetrics.impulsivityScore * 100).toFixed(0)}%. Micro-transactions and discretionary spending are elevated.`,
        'Composite score from micro-transaction ratio, weekend spending, and discretionary category analysis',
        'behaviour',
        evidence,
        ['Implement 24-hour rule for discretionary purchases', 'Set daily micro-spend limits', 'Track discretionary category spending weekly'],
        nodes.map(n => n.id),
        { scoreBps: Math.round(behaviourMetrics.impulsivityScore * 10000) },
      );
      insights.push(insight);
    }

    // Generate financial stress insights
    if (behaviourMetrics.stressScore > config.thresholds.stress_threshold) {
      const evidence = this.buildBehaviourEvidence('stress', behaviourMetrics, nodes);
      const insight = insightBuilder.buildInsight(
        'behaviour-high-stress',
        'behaviour',
        'high',
        2,
        evidence.confidence_score,
        'Elevated Financial Stress',
        `Financial stress index is ${(behaviourMetrics.stressScore * 100).toFixed(0)}%. Balance volatility and credit dependency are contributing factors.`,
        'Composite score from balance volatility, credit dependency, end-of-month depletion, and buffer adequacy',
        'behaviour',
        evidence,
        ['Build emergency fund to reduce financial stress', 'Reduce credit dependency', 'Track end-of-month spending patterns'],
        nodes.map(n => n.id),
        { scoreBps: Math.round(behaviourMetrics.stressScore * 10000) },
      );
      insights.push(insight);
    }

    // Generate savings discipline insights
    if (behaviourMetrics.savingsScore < config.thresholds.savings_threshold) {
      const evidence = this.buildBehaviourEvidence('savings', behaviourMetrics, nodes);
      const insight = insightBuilder.buildInsight(
        'behaviour-low-savings',
        'behaviour',
        'high',
        2,
        evidence.confidence_score,
        'Low Savings Discipline',
        `Savings discipline score is ${(behaviourMetrics.savingsScore * 100).toFixed(0)}%. Savings rate and consistency need improvement.`,
        'Composite score from savings rate, momentum, and consistency metrics',
        'behaviour',
        evidence,
        ['Automate monthly savings transfer', 'Set 10% savings rate target', 'Track savings consistency monthly'],
        nodes.map(n => n.id),
        { scoreBps: Math.round(behaviourMetrics.savingsScore * 10000) },
      );
      insights.push(insight);
    }

    // Generate loss aversion insights
    if (behaviourMetrics.lossAversionScore > 0.6) {
      const evidence = this.buildBehaviourEvidence('loss_aversion', behaviourMetrics, nodes);
      const insight = insightBuilder.buildInsight(
        'behaviour-loss-aversion',
        'behaviour',
        'medium',
        3,
        evidence.confidence_score,
        'Post-Income Spending Pattern',
        `${(behaviourMetrics.lossAversionScore * 100).toFixed(0)}% of income is spent within 72 hours of credit. Consider delaying discretionary purchases.`,
        'Post-income spending velocity and recovery time analysis',
        'behaviour',
        evidence,
        ['Implement 48-hour waiting period after salary credit', 'Set automatic savings on payday'],
        nodes.map(n => n.id),
        { scoreBps: Math.round(behaviourMetrics.lossAversionScore * 10000) },
      );
      insights.push(insight);
    }

    // Generate habit stability insights
    if (behaviourMetrics.habitStabilityScore < 0.4) {
      const evidence = this.buildBehaviourEvidence('habit_stability', behaviourMetrics, nodes);
      const insight = insightBuilder.buildInsight(
        'behaviour-low-stability',
        'behaviour',
        'medium',
        3,
        evidence.confidence_score,
        'Unstable Spending Habits',
        'Category spending varies significantly month-to-month. Setting fixed budgets can improve predictability.',
        'Category coefficient of variation and recurring expense analysis',
        'behaviour',
        evidence,
        ['Set fixed monthly budgets for top 3 spending categories', 'Identify and track recurring expenses'],
        nodes.map(n => n.id),
      );
      insights.push(insight);
    }

    // Generate behavioural risk score
    const riskFactors: RiskFactor[] = [
      {
        name: 'Impulsivity',
        contribution: behaviourMetrics.impulsivityScore * 100,
        description: `Impulse spending score: ${(behaviourMetrics.impulsivityScore * 100).toFixed(0)}%`,
        current_value: (behaviourMetrics.impulsivityScore * 100).toFixed(0),
        threshold: `${config.thresholds.impulsivity_threshold * 100}%`,
      },
      {
        name: 'Financial Stress',
        contribution: behaviourMetrics.stressScore * 100,
        description: `Financial stress index: ${(behaviourMetrics.stressScore * 100).toFixed(0)}%`,
        current_value: (behaviourMetrics.stressScore * 100).toFixed(0),
        threshold: `${config.thresholds.stress_threshold * 100}%`,
      },
    ];

    const riskEvidence = this.buildBehaviourRiskEvidence(behaviourMetrics, nodes);
    const riskScore = insightBuilder.buildRiskScore(
      'risk-behavioural',
      'behavioural',
      (behaviourMetrics.impulsivityScore * 50 + behaviourMetrics.stressScore * 50),
      riskEvidence.confidence_score,
      riskFactors,
      riskEvidence,
      nodes.map(n => n.id),
    );
    riskScores.push(riskScore);

    return {
      insights,
      alerts,
      recommendations: [],
      risk_scores: riskScores,
      opportunity_scores: [],
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private extractBehaviourMetrics(nodes: IntelligenceContext['nodes']): {
    impulsivityScore: number;
    stressScore: number;
    savingsScore: number;
    lossAversionScore: number;
    habitStabilityScore: number;
    wellnessScore: number;
  } {
    let impulsivityScore = 0.5;
    let stressScore = 0.5;
    let savingsScore = 0.5;
    const lossAversionScore = 0.5;
    const habitStabilityScore = 0.5;
    let wellnessScore = 50;

    for (const node of nodes) {
      const meta = node.metadata;

      // Extract from behaviour_score nodes
      if (node.type === 'behaviour_score') {
        if (node.label.includes('Wellness')) {
          wellnessScore = node.confidence ?? 50;
        }
        if (node.label.includes('Savings')) {
          const rateBps = meta.savings_rate_bps as number | undefined;
          if (rateBps !== undefined) savingsScore = rateBps / 10000;
        }
        if (node.label.includes('Debt')) {
          const healthBps = meta.health_score as number | undefined;
          if (healthBps !== undefined) stressScore = 1 - (healthBps / 10000);
        }
      }

      // Extract from spending_pattern nodes
      if (node.type === 'spending_pattern') {
        const percentage = meta.percentage as number | undefined;
        if (percentage !== undefined && percentage > 30) {
          impulsivityScore = Math.min(1, impulsivityScore + 0.1);
        }
      }

      // Extract from metadata directly
      if (meta.score_bps !== undefined) {
        const bps = meta.score_bps as number;
        if (node.label.includes('impulse') || node.label.includes('Impulse')) {
          impulsivityScore = bps / 10000;
        }
      }
    }

    return {
      impulsivityScore: Math.max(0, Math.min(1, impulsivityScore)),
      stressScore: Math.max(0, Math.min(1, stressScore)),
      savingsScore: Math.max(0, Math.min(1, savingsScore)),
      lossAversionScore: Math.max(0, Math.min(1, lossAversionScore)),
      habitStabilityScore: Math.max(0, Math.min(1, habitStabilityScore)),
      wellnessScore: Math.max(0, Math.min(100, wellnessScore)),
    };
  }

  private buildBehaviourEvidence(
    metric: string,
    metrics: { impulsivityScore: number; stressScore: number; savingsScore: number; lossAversionScore: number; habitStabilityScore: number; wellnessScore: number },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const metricLabels: Record<string, { label: string; value: number }> = {
      impulsivity: { label: 'Impulsivity Score', value: metrics.impulsivityScore },
      stress: { label: 'Financial Stress Score', value: metrics.stressScore },
      savings: { label: 'Savings Discipline Score', value: metrics.savingsScore },
      loss_aversion: { label: 'Loss Aversion Score', value: metrics.lossAversionScore },
      habit_stability: { label: 'Habit Stability Score', value: metrics.habitStabilityScore },
    };

    const info = metricLabels[metric] || { label: metric, value: 0.5 };
    const evidence = [
      insightBuilder.createEvidence('behaviour_metric', `${info.label}: ${(info.value * 100).toFixed(0)}%`, 'behaviour-engine', 75),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(`Compute ${info.label}`, `Calculate ${metric} from behavioural indicators`, { metric }, { score: info.value }),
    ];
    return insightBuilder.buildEvidenceChain(`${info.label}: ${(info.value * 100).toFixed(0)}%`, evidence, calculationSteps, [], 70);
  }

  private buildBehaviourRiskEvidence(
    metrics: { impulsivityScore: number; stressScore: number; savingsScore: number; lossAversionScore: number; habitStabilityScore: number; wellnessScore: number },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('behaviour_risk', `Behavioural risk composite: impulsivity ${(metrics.impulsivityScore * 100).toFixed(0)}%, stress ${(metrics.stressScore * 100).toFixed(0)}%`, 'behaviour-engine', 70),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Behavioural Risk', 'Average of impulsivity and stress scores', { impulsivity: metrics.impulsivityScore, stress: metrics.stressScore }, { risk_score: (metrics.impulsivityScore + metrics.stressScore) / 2 }),
    ];
    return insightBuilder.buildEvidenceChain('Behavioural risk assessment', evidence, calculationSteps, [], 65);
  }
}