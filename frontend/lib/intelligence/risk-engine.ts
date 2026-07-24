/**
 * Risk Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic risk assessment engine.
 * Computes overall financial risk from multiple dimensions.
 *
 * Every risk score includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  RiskScore,
  RiskFactor,
  EvidenceChain,
  IntelligenceConfig,
} from './types';
import { insightBuilder } from './insight-builder';

export class RiskEngine implements IntelligenceEngine {
  readonly name = 'risk' as const;

  compute(context: IntelligenceContext): EngineResult {
    const riskScores: RiskScore[] = [];
    const nodes = context.nodes;
    const config = context.config;

    // Compute individual risk scores
    const spendingRisk = this.computeSpendingRisk(nodes, config);
    const liquidityRisk = this.computeLiquidityRisk(nodes, config);
    const concentrationRisk = this.computeConcentrationRisk(nodes);

    if (spendingRisk) riskScores.push(spendingRisk);
    if (liquidityRisk) riskScores.push(liquidityRisk);
    if (concentrationRisk) riskScores.push(concentrationRisk);

    // Compute overall financial risk
    if (riskScores.length > 0) {
      const overallScore = Math.round(
        riskScores.reduce((s, r) => s + r.score, 0) / riskScores.length
      );
      const overallFactors: RiskFactor[] = riskScores.flatMap(r => r.factors);
      const overallEvidence = this.buildOverallRiskEvidence(overallScore, riskScores, nodes);

      const overallRisk = insightBuilder.buildRiskScore(
        'risk-overall',
        'overall_financial',
        overallScore,
        overallEvidence.confidence_score,
        overallFactors,
        overallEvidence,
        nodes.map(n => n.id),
      );
      riskScores.unshift(overallRisk);
    }

    return {
      insights: [],
      alerts: [],
      recommendations: [],
      risk_scores: riskScores,
      opportunity_scores: [],
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private computeSpendingRisk(nodes: IntelligenceContext['nodes'], config: IntelligenceConfig): RiskScore | null {
    const factors: RiskFactor[] = [];
    let totalRisk = 0;
    let factorCount = 0;

    // Check for large transactions
    const largeTxns = nodes.filter(n =>
      n.type === 'transaction' &&
      Math.abs(n.value_paise ?? 0) > config.thresholds.large_transaction_threshold_paise
    );

    if (largeTxns.length > 0) {
      factors.push({
        name: 'Large Transaction Frequency',
        contribution: Math.min(100, largeTxns.length * 15),
        description: `${largeTxns.length} transactions exceed ₹${(config.thresholds.large_transaction_threshold_paise / 100).toLocaleString('en-IN')}`,
        current_value: `${largeTxns.length} transactions`,
        threshold: '0 large transactions',
      });
      totalRisk += Math.min(100, largeTxns.length * 15);
      factorCount++;
    }

    // Check spending trend
    const spendingNodes = nodes.filter(n => n.type === 'spending_pattern');
    for (const node of spendingNodes) {
      const trend = node.metadata?.trend as string | undefined;
      if (trend === 'increasing') {
        factors.push({
          name: 'Increasing Spending Trend',
          contribution: 50,
          description: `${node.label} shows increasing trend`,
          current_value: 'increasing',
          threshold: 'stable or decreasing',
        });
        totalRisk += 50;
        factorCount++;
        break;
      }
    }

    if (factorCount === 0) return null;

    const evidence = this.buildSpendingRiskEvidence(factors, nodes);
    return insightBuilder.buildRiskScore(
      'risk-spending',
      'spending',
      Math.round(totalRisk / factorCount),
      evidence.confidence_score,
      factors,
      evidence,
      nodes.map(n => n.id),
    );
  }

  private computeLiquidityRisk(nodes: IntelligenceContext['nodes'], _config: IntelligenceConfig): RiskScore | null {
    const factors: RiskFactor[] = [];
    let totalRisk = 0;
    let factorCount = 0;

    // Check for negative cashflow months
    const negativeMonths = nodes.filter(n =>
      n.type === 'cashflow_month' &&
      (n.metadata?.net_paise as number ?? 0) < 0
    );

    if (negativeMonths.length > 0) {
      factors.push({
        name: 'Negative Cashflow Months',
        contribution: Math.min(100, negativeMonths.length * 20),
        description: `${negativeMonths.length} months with negative cashflow`,
        current_value: `${negativeMonths.length} months`,
        threshold: '0 negative months',
      });
      totalRisk += Math.min(100, negativeMonths.length * 20);
      factorCount++;
    }

    // Check income vs expenses
    const totalIncome = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) > 0)
      .reduce((s, n) => s + (n.value_paise ?? 0), 0);
    const totalExpenses = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) < 0)
      .reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);

    if (totalIncome > 0 && totalExpenses > totalIncome) {
      factors.push({
        name: 'Expenses Exceed Income',
        contribution: 80,
        description: `Total expenses ₹${(totalExpenses / 100).toLocaleString('en-IN')} exceed income ₹${(totalIncome / 100).toLocaleString('en-IN')}`,
        current_value: `₹${(totalExpenses / 100).toLocaleString('en-IN')}`,
        threshold: `₹${(totalIncome / 100).toLocaleString('en-IN')}`,
      });
      totalRisk += 80;
      factorCount++;
    }

    if (factorCount === 0) return null;

    const evidence = this.buildLiquidityRiskEvidence(factors, nodes);
    return insightBuilder.buildRiskScore(
      'risk-liquidity',
      'liquidity',
      Math.round(totalRisk / factorCount),
      evidence.confidence_score,
      factors,
      evidence,
      nodes.map(n => n.id),
    );
  }

  private computeConcentrationRisk(nodes: IntelligenceContext['nodes']): RiskScore | null {
    const factors: RiskFactor[] = [];

    // Check category concentration
    const categorySpending: Record<string, number> = {};
    for (const node of nodes) {
      if (node.type === 'spending_pattern' && node.value_paise !== undefined) {
        const category = (node.metadata?.category as string) || 'Unknown';
        categorySpending[category] = (categorySpending[category] || 0) + Math.abs(node.value_paise);
      }
    }

    const totalSpending = Object.values(categorySpending).reduce((s, v) => s + v, 0);
    if (totalSpending > 0) {
      for (const [category, amount] of Object.entries(categorySpending)) {
        const percentage = (amount / totalSpending) * 100;
        if (percentage > 50) {
          factors.push({
            name: `High ${category} Concentration`,
            contribution: Math.min(100, percentage),
            description: `${category} represents ${percentage.toFixed(0)}% of total spending`,
            current_value: `${percentage.toFixed(0)}%`,
            threshold: '50%',
          });
        }
      }
    }

    if (factors.length === 0) return null;

    const evidence = this.buildConcentrationRiskEvidence(factors, nodes);
    return insightBuilder.buildRiskScore(
      'risk-concentration',
      'concentration',
      Math.round(factors.reduce((s, f) => s + f.contribution, 0) / factors.length),
      evidence.confidence_score,
      factors,
      evidence,
      nodes.map(n => n.id),
    );
  }

  private buildSpendingRiskEvidence(factors: RiskFactor[], _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = factors.map(f =>
      insightBuilder.createEvidence('risk_factor', f.description, 'risk-engine', 70)
    );
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Spending Risk', 'Aggregate spending risk factors', { factor_count: factors.length }, { risk_score: Math.round(factors.reduce((s, f) => s + f.contribution, 0) / factors.length) }),
    ];
    return insightBuilder.buildEvidenceChain('Spending risk assessment', evidence, calculationSteps, [], 70);
  }

  private buildLiquidityRiskEvidence(factors: RiskFactor[], _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = factors.map(f =>
      insightBuilder.createEvidence('risk_factor', f.description, 'risk-engine', 75)
    );
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Liquidity Risk', 'Aggregate liquidity risk factors', { factor_count: factors.length }, { risk_score: Math.round(factors.reduce((s, f) => s + f.contribution, 0) / factors.length) }),
    ];
    return insightBuilder.buildEvidenceChain('Liquidity risk assessment', evidence, calculationSteps, [], 70);
  }

  private buildConcentrationRiskEvidence(factors: RiskFactor[], _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = factors.map(f =>
      insightBuilder.createEvidence('risk_factor', f.description, 'risk-engine', 65)
    );
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Concentration Risk', 'Analyze category spending concentration', { factor_count: factors.length }, { risk_score: Math.round(factors.reduce((s, f) => s + f.contribution, 0) / factors.length) }),
    ];
    return insightBuilder.buildEvidenceChain('Concentration risk assessment', evidence, calculationSteps, [], 60);
  }

  private buildOverallRiskEvidence(overallScore: number, riskScores: RiskScore[], _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = riskScores.map(r =>
      insightBuilder.createEvidence('risk_dimension', `${r.category}: ${r.score}/100`, 'risk-engine', 70)
    );
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute Overall Risk', 'Average of all risk dimension scores', { dimensions: riskScores.map(r => ({ category: r.category, score: r.score })) }, { overall_risk: overallScore }),
    ];
    return insightBuilder.buildEvidenceChain(`Overall financial risk: ${overallScore}/100`, evidence, calculationSteps, [], 70);
  }
}