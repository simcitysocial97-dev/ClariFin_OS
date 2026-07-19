/**
 * Recommendation Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic recommendation engine.
 * Generates prioritized, evidence-based financial recommendations.
 *
 * Every recommendation includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Recommendation,
  EvidenceChain,
  IntelligenceConfig,
} from './types';
import { insightBuilder } from './insight-builder';

export class RecommendationEngine implements IntelligenceEngine {
  readonly name = 'recommendation' as const;

  compute(context: IntelligenceContext): EngineResult {
    const recommendations: Recommendation[] = [];
    const nodes = context.nodes;
    const config = context.config;

    // Check debt management
    const debtRec = this.checkDebtManagement(nodes, config);
    if (debtRec) recommendations.push(debtRec);

    // Check savings improvement
    const savingsRec = this.checkSavingsImprovement(nodes, config);
    if (savingsRec) recommendations.push(savingsRec);

    // Check spending reduction
    const spendingRec = this.checkSpendingReduction(nodes, config);
    if (spendingRec) recommendations.push(spendingRec);

    // Check emergency fund
    const emergencyRec = this.checkEmergencyFund(nodes);
    if (emergencyRec) recommendations.push(emergencyRec);

    // Check subscription review
    const subRec = this.checkSubscriptions(nodes);
    if (subRec) recommendations.push(subRec);

    // Check budget setting
    const budgetRec = this.checkBudgetSetting(nodes);
    if (budgetRec) recommendations.push(budgetRec);

    // Sort by priority (1 = highest)
    recommendations.sort((a, b) => a.priority - b.priority);

    return {
      insights: [],
      alerts: [],
      recommendations,
      risk_scores: [],
      opportunity_scores: [],
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private checkDebtManagement(nodes: IntelligenceContext['nodes'], config: IntelligenceConfig): Recommendation | null {
    let dtiBps = 0;
    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.debt_to_income_bps !== undefined) {
        dtiBps = meta.debt_to_income_bps as number;
      }
    }

    const dtiRatio = dtiBps / 10000;
    if (dtiRatio > config.thresholds.debt_to_income_threshold) {
      const evidence = this.buildRecommendationEvidence(
        'debt_management',
        `DTI ratio ${(dtiRatio * 100).toFixed(1)}% exceeds ${(config.thresholds.debt_to_income_threshold * 100).toFixed(0)}% threshold`,
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-debt-management',
        'debt_management',
        dtiRatio > 0.6 ? 'critical' : 'high',
        dtiRatio > 0.6 ? 1 : 2,
        'Reduce Debt-to-Income Ratio',
        `Your DTI ratio of ${(dtiRatio * 100).toFixed(1)}% exceeds the recommended ${(config.thresholds.debt_to_income_threshold * 100).toFixed(0)}%`,
        `DTI: ${(dtiRatio * 100).toFixed(1)}%`,
        'Create a debt repayment plan focusing on high-interest debt first. Consider debt consolidation for better rates.',
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private checkSavingsImprovement(nodes: IntelligenceContext['nodes'], _config: IntelligenceConfig): Recommendation | null {
    let savingsRateBps = 0;
    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.savings_rate_bps !== undefined) {
        savingsRateBps = meta.savings_rate_bps as number;
      }
    }

    const savingsRate = savingsRateBps / 100;
    if (savingsRate < 10) {
      const evidence = this.buildRecommendationEvidence(
        'savings_improvement',
        `Savings rate ${savingsRate.toFixed(1)}% is below 10% target`,
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-savings-improvement',
        'savings_improvement',
        savingsRate < 5 ? 'high' : 'medium',
        savingsRate < 5 ? 2 : 3,
        'Increase Savings Rate',
        `Your savings rate of ${savingsRate.toFixed(1)}% is below the recommended 10% minimum`,
        `Savings rate: ${savingsRate.toFixed(1)}%`,
        'Set up automatic transfer of 10% of income to savings on payday. Start with a smaller amount and increase gradually.',
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private checkSpendingReduction(nodes: IntelligenceContext['nodes'], config: IntelligenceConfig): Recommendation | null {
    const categorySpending: Record<string, number> = {};
    for (const node of nodes) {
      if (node.type === 'spending_pattern' && node.value_paise !== undefined) {
        const category = (node.metadata?.category as string) || 'Unknown';
        categorySpending[category] = Math.abs(node.value_paise);
      }
    }

    const topCategory = Object.entries(categorySpending)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 1);

    if (topCategory.length > 0 && topCategory[0][1] > config.thresholds.large_transaction_threshold_paise) {
      const evidence = this.buildRecommendationEvidence(
        'spending_reduction',
        `High spending in ${topCategory[0][0]}: ₹${(topCategory[0][1] / 100).toLocaleString('en-IN')}`,
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-spending-reduction',
        'spending_reduction',
        'medium',
        3,
        `Review ${topCategory[0][0]} Spending`,
        `Your spending in ${topCategory[0][0]} is ₹${(topCategory[0][1] / 100).toLocaleString('en-IN')}. Review for potential reductions.`,
        `${topCategory[0][0]}: ₹${(topCategory[0][1] / 100).toLocaleString('en-IN')}`,
        `Set a monthly budget for ${topCategory[0][0]} and track expenses weekly to identify savings opportunities.`,
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private checkEmergencyFund(nodes: IntelligenceContext['nodes']): Recommendation | null {
    const totalExpenses = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) < 0)
      .reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);

    const totalIncome = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) > 0)
      .reduce((s, n) => s + (n.value_paise ?? 0), 0);

    if (totalIncome > 0 && totalExpenses > totalIncome * 0.8) {
      const evidence = this.buildRecommendationEvidence(
        'emergency_fund',
        'High expense-to-income ratio indicates need for emergency fund',
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-emergency-fund',
        'emergency_fund',
        'high',
        2,
        'Build Emergency Fund',
        'Your expenses are close to your income level. An emergency fund is critical for financial security.',
        'Expense-to-income ratio is high',
        'Build an emergency fund covering 3-6 months of essential expenses. Start with a 1-month target.',
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private checkSubscriptions(nodes: IntelligenceContext['nodes']): Recommendation | null {
    const subscriptionKeywords = ['netflix', 'spotify', 'amazon', 'prime', 'youtube', 'subscription', 'membership'];
    const subscriptionNodes = nodes.filter(n => {
      const label = n.label.toLowerCase();
      const desc = ((n.metadata?.description as string) || '').toLowerCase();
      return subscriptionKeywords.some(kw => label.includes(kw) || desc.includes(kw));
    });

    if (subscriptionNodes.length >= 3) {
      const totalSubCost = subscriptionNodes.reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);
      const evidence = this.buildRecommendationEvidence(
        'subscription_review',
        `${subscriptionNodes.length} subscription services detected totaling ₹${(totalSubCost / 100).toLocaleString('en-IN')}`,
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-subscription-review',
        'subscription_review',
        'medium',
        3,
        'Review Subscription Services',
        `You have ${subscriptionNodes.length} active subscription services totaling ₹${(totalSubCost / 100).toLocaleString('en-IN')}`,
        `${subscriptionNodes.length} subscriptions`,
        'Audit your subscriptions monthly. Cancel unused services and consolidate overlapping ones.',
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private checkBudgetSetting(nodes: IntelligenceContext['nodes']): Recommendation | null {
    const categoryCount = new Set(
      nodes
        .filter(n => n.type === 'spending_pattern')
        .map(n => n.metadata?.category as string)
        .filter(Boolean)
    ).size;

    if (categoryCount >= 3) {
      const evidence = this.buildRecommendationEvidence(
        'budget_setting',
        `${categoryCount} spending categories identified for budget setting`,
        nodes,
      );
      return insightBuilder.buildRecommendation(
        'rec-budget-setting',
        'budget_setting',
        'low',
        4,
        'Set Category Budgets',
        `You have ${categoryCount} spending categories. Setting budgets helps control spending and achieve savings goals.`,
        `${categoryCount} categories`,
        'Set monthly budgets for your top 3 spending categories. Review and adjust quarterly.',
        evidence,
        'recommendation',
        nodes.map(n => n.id),
      );
    }
    return null;
  }

  private buildRecommendationEvidence(type: string, detail: string, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('recommendation_trigger', detail, 'recommendation-engine', 75),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Generate Recommendation', `Evaluate ${type} conditions`, { type }, { triggered: true }),
    ];
    return insightBuilder.buildEvidenceChain(`Recommendation: ${type}`, evidence, calculationSteps, [], 70);
  }
}
