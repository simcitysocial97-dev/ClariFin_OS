/**
 * Anomaly Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic anomaly detection engine.
 * Detects unusual patterns in spending, income, and account activity.
 *
 * Every anomaly includes evidence, calculation, confidence, source, and related graph nodes.
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

export class AnomalyEngine implements IntelligenceEngine {
  readonly name = 'anomaly' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const alerts: Alert[] = [];
    const nodes = context.nodes;

    // Detect spending anomalies
    const spendingAnomalies = this.detectSpendingAnomalies(nodes);
    for (const anomaly of spendingAnomalies) {
      const evidence = this.buildAnomalyEvidence(anomaly, nodes);
      const alert = insightBuilder.buildAlert(
        `alert-anomaly-${anomaly.id}`,
        'spending_anomaly',
        'high',
        2,
        'Unusual Spending Pattern Detected',
        `Transaction of ₹${(Math.abs(anomaly.value_paise) / 100).toLocaleString('en-IN')} deviates from normal patterns`,
        evidence,
        'anomaly',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
      alerts.push(alert);
    }

    // Detect income anomalies
    const incomeAnomalies = this.detectIncomeAnomalies(nodes);
    for (const anomaly of incomeAnomalies) {
      const evidence = this.buildIncomeAnomalyEvidence(anomaly, nodes);
      const insight = insightBuilder.buildInsight(
        `anomaly-income-${anomaly.id}`,
        'anomaly',
        'medium',
        3,
        evidence.confidence_score,
        'Unusual Income Pattern',
        `Income of ₹${(anomaly.value_paise / 100).toLocaleString('en-IN')} differs from expected pattern`,
        'Income deviation analysis',
        'anomaly',
        evidence,
        ['Verify income source', 'Update expected income patterns'],
        nodes.map(n => n.id),
        { valuePaise: anomaly.value_paise },
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

  private detectSpendingAnomalies(
    nodes: IntelligenceContext['nodes'],
  ): Array<{ id: string; value_paise: number; category: string; date: string; deviation: number }>{
    const anomalies: Array<{ id: string; value_paise: number; category: string; date: string; deviation: number }> = [];
    const transactionNodes = nodes.filter(n => n.type === 'transaction' && (n.value_paise ?? 0) < 0);

    // Group by category
    const categorySpending: Record<string, number[]> = {};
    for (const node of transactionNodes) {
      const category = (node.metadata?.category as string) || 'Uncategorized';
      if (!categorySpending[category]) categorySpending[category] = [];
      categorySpending[category].push(Math.abs(node.value_paise ?? 0));
    }

    // Detect anomalies (values > 2 std devs from mean)
    for (const node of transactionNodes) {
      const category = (node.metadata?.category as string) || 'Uncategorized';
      const values = categorySpending[category] || [];
      if (values.length < 3) continue;

      const mean = values.reduce((s, v) => s + v, 0) / values.length;
      const variance = values.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / values.length;
      const stdDev = Math.sqrt(variance);

      const value = Math.abs(node.value_paise ?? 0);
      if (stdDev > 0 && Math.abs(value - mean) > 2 * stdDev) {
        anomalies.push({
          id: node.id,
          value_paise: node.value_paise ?? 0,
          category,
          date: node.date || '',
          deviation: (value - mean) / stdDev,
        });
      }
    }

    return anomalies.sort((a, b) => Math.abs(b.deviation) - Math.abs(a.deviation)).slice(0, 10);
  }

  private detectIncomeAnomalies(
    nodes: IntelligenceContext['nodes'],
  ): Array<{ id: string; value_paise: number; date: string; deviation: number }>{
    const anomalies: Array<{ id: string; value_paise: number; date: string; deviation: number }> = [];
    const incomeNodes = nodes.filter(n => n.type === 'transaction' && (n.value_paise ?? 0) > 0);

    if (incomeNodes.length < 3) return anomalies;

    const values = incomeNodes.map(n => n.value_paise ?? 0);
    const mean = values.reduce((s, v) => s + v, 0) / values.length;
    const variance = values.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);

    for (const node of incomeNodes) {
      const value = node.value_paise ?? 0;
      if (stdDev > 0 && Math.abs(value - mean) > 2 * stdDev) {
        anomalies.push({
          id: node.id,
          value_paise: value,
          date: node.date || '',
          deviation: (value - mean) / stdDev,
        });
      }
    }

    return anomalies.sort((a, b) => Math.abs(b.deviation) - Math.abs(a.deviation)).slice(0, 5);
  }

  private buildAnomalyEvidence(
    anomaly: { id: string; value_paise: number; category: string; date: string; deviation: number },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'spending_anomaly',
        `Transaction deviates ${anomaly.deviation.toFixed(1)} standard deviations from category mean`,
        'anomaly-engine',
        85,
      ),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Detect Spending Anomaly',
        'Calculate z-score for transaction against category mean',
        { category: anomaly.category, value_paise: anomaly.value_paise },
        { deviation: anomaly.deviation, is_anomaly: Math.abs(anomaly.deviation) > 2 },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      `Spending anomaly detected: ${anomaly.category}`,
      evidence,
      calculationSteps,
      [],
      80,
    );
  }

  private buildIncomeAnomalyEvidence(
    anomaly: { id: string; value_paise: number; date: string; deviation: number },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'income_anomaly',
        `Income deviates ${anomaly.deviation.toFixed(1)} standard deviations from mean`,
        'anomaly-engine',
        80,
      ),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Detect Income Anomaly',
        'Calculate z-score for income against historical mean',
        { value_paise: anomaly.value_paise },
        { deviation: anomaly.deviation, is_anomaly: Math.abs(anomaly.deviation) > 2 },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      'Income anomaly detected',
      evidence,
      calculationSteps,
      [],
      75,
    );
  }
}