/**
 * Opportunity Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic opportunity detection engine.
 * Identifies savings, investment, debt optimization, and cashflow improvement opportunities.
 *
 * Every opportunity score includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  OpportunityScore,
  EvidenceChain,
} from './types';
import { insightBuilder } from './insight-builder';

export class OpportunityEngine implements IntelligenceEngine {
  readonly name = 'opportunity' as const;

  compute(context: IntelligenceContext): EngineResult {
    const opportunities: OpportunityScore[] = [];
    const nodes = context.nodes;

    // Detect savings opportunities
    const savingsOpp = this.detectSavingsOpportunity(nodes);
    if (savingsOpp) opportunities.push(savingsOpp);

    // Detect debt optimization opportunities
    const debtOpp = this.detectDebtOptimization(nodes);
    if (debtOpp) opportunities.push(debtOpp);

    // Detect cashflow improvement opportunities
    const cashflowOpp = this.detectCashflowImprovement(nodes);
    if (cashflowOpp) opportunities.push(cashflowOpp);

    return {
      insights: [],
      alerts: [],
      recommendations: [],
      risk_scores: [],
      opportunity_scores: opportunities,
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private detectSavingsOpportunity(nodes: IntelligenceContext['nodes']): OpportunityScore | null {
    // Look for high spending categories where savings could be made
    const categorySpending: Record<string, number> = {};
    for (const node of nodes) {
      if (node.type === 'spending_pattern' && node.value_paise !== undefined) {
        const category = (node.metadata?.category as string) || 'Unknown';
        categorySpending[category] = Math.abs(node.value_paise);
      }
    }

    const topCategory = Object.entries(categorySpending)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 3);

    if (topCategory.length > 0 && topCategory[0][1] > 200000) { // > ₹2,000
      const totalPotential = Math.round(topCategory[0][1] * 0.1); // 10% savings potential
      const evidence = this.buildSavingsEvidence(topCategory[0][0], topCategory[0][1], totalPotential, nodes);
      return insightBuilder.buildOpportunityScore(
        'opportunity-savings',
        'savings_potential',
        65,
        evidence.confidence_score,
        `Potential 10% savings in ${topCategory[0][0]} by optimizing spending`,
        evidence,
        nodes.map(n => n.id),
        { estimatedBenefitPaise: totalPotential },
      );
    }

    return null;
  }

  private detectDebtOptimization(nodes: IntelligenceContext['nodes']): OpportunityScore | null {
    let totalDebtPaise = 0;
    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.total_debt_paise !== undefined) {
        totalDebtPaise = meta.total_debt_paise as number;
      }
    }

    if (totalDebtPaise > 0) {
      const potentialSavings = Math.round(totalDebtPaise * 0.02); // 2% refinancing savings
      const evidence = this.buildDebtEvidence(totalDebtPaise, potentialSavings, nodes);
      return insightBuilder.buildOpportunityScore(
        'opportunity-debt-optimization',
        'debt_optimization',
        55,
        evidence.confidence_score,
        'Potential savings through debt refinancing or prepayment',
        evidence,
        nodes.map(n => n.id),
        { estimatedBenefitPaise: potentialSavings },
      );
    }

    return null;
  }

  private detectCashflowImprovement(nodes: IntelligenceContext['nodes']): OpportunityScore | null {
    const negativeMonths = nodes.filter(n =>
      n.type === 'cashflow_month' &&
      (n.metadata?.net_paise as number ?? 0) < 0
    );

    if (negativeMonths.length > 0) {
      const evidence = this.buildCashflowEvidence(negativeMonths.length, nodes);
      return insightBuilder.buildOpportunityScore(
        'opportunity-cashflow',
        'cashflow_improvement',
        60,
        evidence.confidence_score,
        `${negativeMonths.length} months with negative cashflow - opportunity to stabilize through budgeting`,
        evidence,
        nodes.map(n => n.id),
      );
    }

    return null;
  }

  private buildSavingsEvidence(category: string, currentSpend: number, potentialSavings: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('savings_opportunity', `10% savings potential in ${category}: ₹${(potentialSavings / 100).toLocaleString('en-IN')}`, 'opportunity-engine', 65),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Estimate Savings Potential', '10% of current category spending', { category, current_spend_paise: currentSpend }, { potential_savings_paise: potentialSavings }),
    ];
    return insightBuilder.buildEvidenceChain(`Savings opportunity: ${category}`, evidence, calculationSteps, [], 60);
  }

  private buildDebtEvidence(totalDebtPaise: number, potentialSavings: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('debt_opportunity', `2% refinancing savings: ₹${(potentialSavings / 100).toLocaleString('en-IN')}`, 'opportunity-engine', 50),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Estimate Debt Optimization', '2% of total debt for refinancing savings', { total_debt_paise: totalDebtPaise }, { potential_savings_paise: potentialSavings }),
    ];
    return insightBuilder.buildEvidenceChain('Debt optimization opportunity', evidence, calculationSteps, [], 50);
  }

  private buildCashflowEvidence(negativeMonthCount: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('cashflow_opportunity', `${negativeMonthCount} negative cashflow months identified`, 'opportunity-engine', 55),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Identify Cashflow Improvement', 'Count negative cashflow months', { negative_month_count: negativeMonthCount }, { improvement_needed: true }),
    ];
    return insightBuilder.buildEvidenceChain('Cashflow improvement opportunity', evidence, calculationSteps, [], 50);
  }
}