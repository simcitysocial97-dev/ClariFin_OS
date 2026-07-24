/**
 * Investment Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic investment intelligence engine.
 * Analyzes investment patterns, portfolio allocation, and investment health.
 *
 * Every insight includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Insight,
  RiskScore,
  RiskFactor,
  OpportunityScore,
  EvidenceChain,
} from './types';
import { insightBuilder } from './insight-builder';

export class InvestmentEngine implements IntelligenceEngine {
  readonly name = 'investment' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const riskScores: RiskScore[] = [];
    const opportunityScores: OpportunityScore[] = [];
    const nodes = context.nodes;

    // Analyze investment patterns
    const investmentNodes = nodes.filter(n => n.type === 'investment' || n.type === 'investment_transaction');
    const portfolioNodes = nodes.filter(n => n.type === 'portfolio' || n.type === 'asset_allocation');

    // Generate investment insights
    const diversificationOpp = this.analyzeDiversification(investmentNodes, portfolioNodes);
    if (diversificationOpp) opportunityScores.push(diversificationOpp);

    const riskScore = this.computeInvestmentRisk(investmentNodes, portfolioNodes);
    if (riskScore) riskScores.push(riskScore);

    return {
      insights,
      alerts: [],
      recommendations: [],
      risk_scores: riskScores,
      opportunity_scores: opportunityScores,
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private analyzeDiversification(
    _investmentNodes: IntelligenceContext['nodes'],
    portfolioNodes: IntelligenceContext['nodes'],
  ): OpportunityScore | null {
    // Check for concentration in single asset class
    const categoryAllocation: Record<string, number> = {};
    for (const node of portfolioNodes) {
      if (node.value_paise !== undefined) {
        const category = (node.metadata?.category as string) || 'Unknown';
        categoryAllocation[category] = (categoryAllocation[category] || 0) + Math.abs(node.value_paise);
      }
    }

    const totalAllocation = Object.values(categoryAllocation).reduce((s, v) => s + v, 0);
    if (totalAllocation > 0) {
      for (const [category, amount] of Object.entries(categoryAllocation)) {
        const percentage = (amount / totalAllocation) * 100;
        if (percentage > 60) {
          // High concentration - opportunity to diversify
          const evidence = this.buildDiversificationEvidence(category, percentage, portfolioNodes);
          return insightBuilder.buildOpportunityScore(
            `opportunity-diversification-${category.toLowerCase().replace(/\s+/g, '-')}`,
            'investment_potential',
            70,
            evidence.confidence_score,
            `${category} represents ${percentage.toFixed(0)}% of portfolio - consider diversification`,
            evidence,
            portfolioNodes.map(n => n.id),
            { estimatedBenefitPaise: Math.round(amount * 0.1) },
          );
        }
      }
    }

    return null;
  }

  private computeInvestmentRisk(
    investmentNodes: IntelligenceContext['nodes'],
    portfolioNodes: IntelligenceContext['nodes'],
  ): RiskScore | null {
    const factors: RiskFactor[] = [];
    let totalRisk = 0;
    let factorCount = 0;

    // Check for high-risk investments
    const highRiskNodes = investmentNodes.filter(n => {
      const riskLevel = (n.metadata?.risk_level as string) || 'medium';
      return riskLevel === 'high';
    });

    if (highRiskNodes.length > 0) {
      factors.push({
        name: 'High-Risk Investments',
        contribution: Math.min(100, highRiskNodes.length * 20),
        description: `${highRiskNodes.length} high-risk investment positions identified`,
        current_value: `${highRiskNodes.length} positions`,
        threshold: '0 high-risk positions',
      });
      totalRisk += Math.min(100, highRiskNodes.length * 20);
      factorCount++;
    }

    // Check for lack of diversification
    const totalValue = portfolioNodes.reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);
    if (totalValue > 0) {
      const categoryCount = new Set(
        portfolioNodes.map(n => (n.metadata?.category as string) || 'Unknown')
      ).size;

      if (categoryCount < 3) {
        factors.push({
          name: 'Low Diversification',
          contribution: 60,
          description: `Only ${categoryCount} asset categories in portfolio`,
          current_value: `${categoryCount} categories`,
          threshold: '3+ categories',
        });
        totalRisk += 60;
        factorCount++;
      }
    }

    if (factorCount === 0) return null;

    const evidence = this.buildInvestmentRiskEvidence(factors, investmentNodes);
    return insightBuilder.buildRiskScore(
      'risk-investment',
      'investment',
      Math.round(totalRisk / factorCount),
      evidence.confidence_score,
      factors,
      evidence,
      investmentNodes.map(n => n.id),
    );
  }

  private buildDiversificationEvidence(
    category: string,
    percentage: number,
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'diversification_opportunity',
        `${category} represents ${percentage.toFixed(0)}% of total portfolio`,
        'investment-engine',
        70,
      ),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Analyze Portfolio Allocation',
        `Calculate percentage allocation per asset category`,
        { category },
        { percentage },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      `Diversification opportunity: ${category}`,
      evidence,
      calculationSteps,
      [],
      70,
    );
  }

  private buildInvestmentRiskEvidence(
    factors: RiskFactor[],
    _nodes: IntelligenceContext['nodes'],
  ): EvidenceChain {
    const evidence = factors.map(f =>
      insightBuilder.createEvidence('risk_factor', f.description, 'investment-engine', 70)
    );
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Compute Investment Risk',
        'Aggregate investment risk factors',
        { factor_count: factors.length },
        { risk_score: Math.round(factors.reduce((s, f) => s + f.contribution, 0) / factors.length) },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      'Investment risk assessment',
      evidence,
      calculationSteps,
      [],
      70,
    );
  }
}