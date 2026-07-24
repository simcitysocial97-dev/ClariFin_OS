/**
 * Cashflow Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic cashflow intelligence engine.
 * Analyzes cashflow patterns, detects gaps, computes stability metrics.
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
} from './types';
import { insightBuilder } from './insight-builder';

export class CashflowEngine implements IntelligenceEngine {
  readonly name = 'cashflow' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const alerts: Alert[] = [];
    const nodes = context.nodes;

    // Analyze cashflow
    const cashflowMonths = this.extractCashflowMonths(nodes);
    const gaps = this.detectCashflowGaps(cashflowMonths);
    const stability = this.computeCashflowStability(cashflowMonths);

    // Generate cashflow gap alerts
    for (const gap of gaps) {
      const evidence = this.buildGapEvidence(gap, nodes);
      const alert = insightBuilder.buildAlert(
        `alert-cashflow-gap-${gap.month}`,
        'cashflow_gap',
        'high',
        2,
        'Negative Cashflow Month',
        `Month ${gap.month} had negative cashflow of ₹${(Math.abs(gap.net_paise) / 100).toLocaleString('en-IN')}`,
        evidence,
        'cashflow',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
      alerts.push(alert);
    }

    // Generate stability insights
    if (stability.score < 40) {
      const evidence = this.buildStabilityEvidence(stability, nodes);
      const insight = insightBuilder.buildInsight(
        'cashflow-stability-low',
        'cashflow',
        'high',
        2,
        evidence.confidence_score,
        'Unstable Cashflow Pattern',
        'Your cashflow shows significant month-to-month variability. Consider building a consistent income base.',
        'Coefficient of variation of monthly net cashflow',
        'cashflow',
        evidence,
        ['Build an emergency fund to smooth cashflow gaps', 'Review irregular income sources'],
        nodes.map(n => n.id),
      );
      insights.push(insight);
    }

    return {
      insights,
      alerts,
      recommendations: [],
      risk_scores: [],
      opportunity_scores: [],
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private extractCashflowMonths(nodes: IntelligenceContext['nodes']): Array<{ month: string; income_paise: number; expenses_paise: number; net_paise: number }> {
    const monthly: Record<string, { income_paise: number; expenses_paise: number }> = {};

    for (const node of nodes) {
      if (node.type === 'transaction' && node.date) {
        const month = node.date.substring(0, 7); // YYYY-MM
        const value = node.value_paise ?? 0;
        if (!monthly[month]) monthly[month] = { income_paise: 0, expenses_paise: 0 };

        if (value > 0) monthly[month].income_paise += value;
        else monthly[month].expenses_paise += Math.abs(value);
      }

      // Also check cashflow_month nodes
      if (node.type === 'cashflow_month') {
        const month = node.label;
        const meta = node.metadata;
        if (!monthly[month]) monthly[month] = { income_paise: 0, expenses_paise: 0 };
        if (meta.income_paise !== undefined) monthly[month].income_paise += meta.income_paise as number;
        if (meta.expenses_paise !== undefined) monthly[month].expenses_paise += meta.expenses_paise as number;
      }
    }

    return Object.entries(monthly)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([month, data]) => ({
        month,
        income_paise: data.income_paise,
        expenses_paise: data.expenses_paise,
        net_paise: data.income_paise - data.expenses_paise,
      }));
  }

  private detectCashflowGaps(months: Array<{ month: string; net_paise: number }>): Array<{ month: string; net_paise: number }> {
    return months.filter(m => m.net_paise < 0);
  }

  private computeCashflowStability(months: Array<{ month: string; net_paise: number }>): { score: number; cv: number; avg_net: number } {
    if (months.length < 2) return { score: 50, cv: 0, avg_net: 0 };

    const nets = months.map(m => Math.abs(m.net_paise));
    const avg = nets.reduce((s, v) => s + v, 0) / nets.length;
    if (avg === 0) return { score: 50, cv: 0, avg_net: 0 };

    const variance = nets.reduce((s, v) => s + (v - avg) ** 2, 0) / nets.length;
    const std = Math.sqrt(variance);
    const cv = std / avg;

    // Lower CV = more stable
    const score = Math.max(0, Math.min(100, 100 - cv * 100));
    return { score: Math.round(score), cv, avg_net: avg };
  }

  private buildGapEvidence(gap: { month: string; net_paise: number }, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('cashflow_gap', `Month ${gap.month}: negative cashflow ₹${(Math.abs(gap.net_paise) / 100).toLocaleString('en-IN')}`, 'cashflow-engine', 80),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Net Cashflow', 'Subtract expenses from income', { month: gap.month }, { net_paise: gap.net_paise }),
    ];
    return insightBuilder.buildEvidenceChain(`Cashflow gap in ${gap.month}`, evidence, calculationSteps, [], 75);
  }

  private buildStabilityEvidence(stability: { score: number; cv: number; avg_net: number }, nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('cashflow_stability', `Cashflow CV: ${(stability.cv * 100).toFixed(1)}%`, 'cashflow-engine', 70),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Stability', 'Calculate coefficient of variation of monthly net cashflow', { months_analyzed: nodes.length }, { cv: stability.cv, score: stability.score }),
    ];
    return insightBuilder.buildEvidenceChain(`Cashflow stability score: ${stability.score}/100`, evidence, calculationSteps, [], 65);
  }
}