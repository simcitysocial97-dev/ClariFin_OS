/**
 * Spending Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic spending intelligence engine.
 * Analyzes spending patterns, detects anomalies, computes trends.
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
  IntelligenceConfig,
} from './types';
import { insightBuilder } from './insight-builder';

// ===== Spending Engine =====
export class SpendingEngine implements IntelligenceEngine {
  readonly name = 'spending' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const alerts: Alert[] = [];
    const nodes = context.nodes;
    const config = context.config;

    // Filter transaction nodes
    const transactionNodes = nodes.filter(n => n.type === 'transaction');
    const debitNodes = transactionNodes.filter(n => (n.value_paise ?? 0) < 0);

    // Analyze spending patterns
    const categorySpending = this.analyzeCategorySpending(nodes);
    const anomalies = this.detectAnomalies(debitNodes, config);
    const trends = this.computeTrends(debitNodes);

    // Generate insights from category analysis
    for (const [category, totalPaise] of Object.entries(categorySpending)) {
      if (totalPaise > config.thresholds.large_transaction_threshold_paise) {
        const evidence = this.buildCategoryEvidence(category, totalPaise, debitNodes);
        const insight = insightBuilder.buildInsight(
          `spending-category-${category.toLowerCase().replace(/\s+/g, '-')}`,
          'spending',
          'medium',
          3,
          evidence.confidence_score,
          `High Spending in ${category}`,
          `Total spending in ${category} is ₹${(totalPaise / 100).toLocaleString('en-IN')}. Review for optimization opportunities.`,
          `Sum of all debit transactions in ${category} category`,
          'spending',
          evidence,
          [`Review ${category} expenses for potential savings`, 'Set a monthly budget for this category'],
          nodes.map(n => n.id),
          { valuePaise: totalPaise },
        );
        insights.push(insight);
      }
    }

    // Generate anomaly alerts
    for (const anomaly of anomalies) {
      const evidence = this.buildAnomalyEvidence(anomaly, nodes);
      const alert = insightBuilder.buildAlert(
        `alert-spending-anomaly-${anomaly.id}`,
        'spending_anomaly',
        'high',
        2,
        'Large Transaction Detected',
        `Transaction of ₹${(Math.abs(anomaly.value_paise) / 100).toLocaleString('en-IN')} in ${anomaly.category || 'unknown category'}`,
        evidence,
        'spending',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
      alerts.push(alert);
    }

    // Generate trend insights
    for (const trend of trends) {
      if (trend.direction === 'increasing' && Math.abs(trend.magnitude) > 0.1) {
        const evidence = this.buildTrendEvidence(trend, nodes);
        const insight = insightBuilder.buildInsight(
          `spending-trend-${trend.category.toLowerCase().replace(/\s+/g, '-')}`,
          'trend',
          trend.magnitude > 0.2 ? 'high' : 'medium',
          trend.magnitude > 0.2 ? 2 : 3,
          evidence.confidence_score,
          `${trend.category} Spending ${trend.direction === 'increasing' ? 'Up' : 'Down'}`,
          `${trend.category} spending has ${trend.direction} by ${(Math.abs(trend.magnitude) * 100).toFixed(0)}%`,
          `Month-over-month comparison of ${trend.category} spending`,
          'spending',
          evidence,
          [trend.direction === 'increasing'
            ? 'Review recent increases in this category'
            : 'Continue the positive trend'],
          nodes.map(n => n.id),
        );
        insights.push(insight);
      }
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

  reset(): void {
    // No state to reset
  }

  // ===== Private Methods =====

  private analyzeCategorySpending(nodes: IntelligenceContext['nodes']): Record<string, number> {
    const categorySpending: Record<string, number> = {};

    for (const node of nodes) {
      if (node.type === 'spending_pattern' && node.value_paise !== undefined) {
        const category = (node.metadata?.category as string) || node.label.replace('Spending: ', '');
        categorySpending[category] = (categorySpending[category] || 0) + Math.abs(node.value_paise);
      }
    }

    // Also check transaction nodes with category metadata
    for (const node of nodes) {
      if (node.type === 'transaction' && node.value_paise && node.value_paise < 0) {
        const category = (node.metadata?.category as string) || 'Uncategorized';
        categorySpending[category] = (categorySpending[category] || 0) + Math.abs(node.value_paise);
      }
    }

    return categorySpending;
  }

  private detectAnomalies(
    debitNodes: IntelligenceContext['nodes'],
    config: IntelligenceConfig,
  ): Array<{ id: string; value_paise: number; category: string; date: string }> {
    const anomalies: Array<{ id: string; value_paise: number; category: string; date: string }> = [];

    for (const node of debitNodes) {
      const value = Math.abs(node.value_paise ?? 0);
      if (value > config.thresholds.large_transaction_threshold_paise) {
        anomalies.push({
          id: node.id,
          value_paise: node.value_paise ?? 0,
          category: (node.metadata?.category as string) || 'Unknown',
          date: node.date || '',
        });
      }
    }

    // Sort by value descending, take top 5
    return anomalies.sort((a, b) => Math.abs(b.value_paise) - Math.abs(a.value_paise)).slice(0, 5);
  }

  private computeTrends(
    debitNodes: IntelligenceContext['nodes'],
  ): Array<{ category: string; direction: 'increasing' | 'decreasing' | 'stable'; magnitude: number }> {
    const trends: Array<{ category: string; direction: 'increasing' | 'decreasing' | 'stable'; magnitude: number }> = [];

    // Group by category
    const categoryNodes: Record<string, IntelligenceContext['nodes']> = {};
    for (const node of debitNodes) {
      const category = (node.metadata?.category as string) || 'Uncategorized';
      if (!categoryNodes[category]) categoryNodes[category] = [];
      categoryNodes[category].push(node);
    }

    // Compute trend for each category
    for (const [category, nodes] of Object.entries(categoryNodes)) {
      if (nodes.length < 2) continue;

      // Sort by date
      const sorted = [...nodes].sort((a, b) => (a.date || '').localeCompare(b.date || ''));

      // Compare first half vs second half
      const mid = Math.floor(sorted.length / 2);
      const firstHalf = sorted.slice(0, mid);
      const secondHalf = sorted.slice(mid);

      const firstAvg = firstHalf.reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0) / firstHalf.length;
      const secondAvg = secondHalf.reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0) / secondHalf.length;

      const magnitude = firstAvg > 0 ? (secondAvg - firstAvg) / firstAvg : 0;
      const direction = magnitude > 0.05 ? 'increasing' : magnitude < -0.05 ? 'decreasing' : 'stable';

      trends.push({ category, direction, magnitude });
    }

    return trends;
  }

  private buildCategoryEvidence(
    category: string,
    totalPaise: number,
    _debitNodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const categoryNodes = _debitNodes.filter(n =>
      (n.metadata?.category as string) === category
    );

    const evidence = [
      insightBuilder.createEvidence(
        'spending_total',
        `Total spending in ${category}: ₹${(totalPaise / 100).toLocaleString('en-IN')}`,
        'spending-engine',
        80,
      ),
      insightBuilder.createEvidence(
        'transaction_count',
        `${categoryNodes.length} transactions in ${category}`,
        'spending-engine',
        70,
      ),
    ];

    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Sum Category Spending',
        `Sum all debit transactions in ${category}`,
        { category, transaction_count: categoryNodes.length },
        { total_paise: totalPaise, total_rupees: totalPaise / 100 },
      ),
    ];

    const sourceReferences = categoryNodes.slice(0, 3).map(n =>
      insightBuilder.createSourceReference(n.id, 'graph_node', n.label, n.date || '')
    );

    return insightBuilder.buildEvidenceChain(
      `Spending analysis for ${category}: ₹${(totalPaise / 100).toLocaleString('en-IN')}`,
      evidence,
      calculationSteps,
      sourceReferences,
      75,
    );
  }

  private buildAnomalyEvidence(
    anomaly: { id: string; value_paise: number; category: string; date: string },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'anomaly',
        `Large transaction: ₹${(Math.abs(anomaly.value_paise) / 100).toLocaleString('en-IN')}`,
        'spending-engine',
        90,
      ),
    ];

    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Detect Anomaly',
        'Compare transaction value against threshold',
        {
          transaction_value_paise: anomaly.value_paise,
          threshold_paise: 5000000, // ₹50,000
        },
        { is_anomaly: true, exceeds_by_paise: Math.abs(anomaly.value_paise) - 5000000 },
      ),
    ];

    return insightBuilder.buildEvidenceChain(
      `Anomalous transaction: ₹${(Math.abs(anomaly.value_paise) / 100).toLocaleString('en-IN')}`,
      evidence,
      calculationSteps,
      [],
      85,
    );
  }

  private buildTrendEvidence(
    trend: { category: string; direction: string; magnitude: number },
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'trend',
        `${trend.category} spending ${trend.direction} by ${(Math.abs(trend.magnitude) * 100).toFixed(0)}%`,
        'spending-engine',
        70,
      ),
    ];

    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Compute Trend',
        'Compare first half vs second half average spending',
        { category: trend.category },
        { direction: trend.direction, magnitude: trend.magnitude },
      ),
    ];

    return insightBuilder.buildEvidenceChain(
      `${trend.category} spending trend: ${trend.direction}`,
      evidence,
      calculationSteps,
      [],
      65,
    );
  }
}