/**
 * Alert Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic alert generation engine.
 * Generates prioritized alerts based on financial conditions.
 *
 * Every alert includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Alert,
  EvidenceChain,
} from './types';
import { insightBuilder } from './insight-builder';

export class AlertEngine implements IntelligenceEngine {
  readonly name = 'alert' as const;

  compute(context: IntelligenceContext): EngineResult {
    const alerts: Alert[] = [];
    const nodes = context.nodes;

    // Check for low liquidity
    const liquidityAlert = this.checkLowLiquidity(nodes);
    if (liquidityAlert) alerts.push(liquidityAlert);

    // Check for negative savings
    const savingsAlert = this.checkNegativeSavings(nodes);
    if (savingsAlert) alerts.push(savingsAlert);

    // Check for gambling detection
    const gamblingAlert = this.checkGambling(nodes);
    if (gamblingAlert) alerts.push(gamblingAlert);

    // Check for loan app patterns
    const loanAppAlert = this.checkLoanAppPattern(nodes);
    if (loanAppAlert) alerts.push(loanAppAlert);

    // Check for goal deviation
    const goalAlert = this.checkGoalDeviation(nodes);
    if (goalAlert) alerts.push(goalAlert);

    // Check for reconciliation issues
    const reconciliationAlert = this.checkReconciliation(nodes);
    if (reconciliationAlert) alerts.push(reconciliationAlert);

    // Sort by priority (1 = highest)
    alerts.sort((a, b) => a.priority - b.priority);

    return {
      insights: [],
      alerts,
      recommendations: [],
      risk_scores: [],
      opportunity_scores: [],
      goals: [],
      health_score: null,
    };
  }

  reset(): void {}

  private checkLowLiquidity(nodes: IntelligenceContext['nodes']): Alert | null {
    const totalExpenses = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) < 0)
      .reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);

    const totalIncome = nodes
      .filter(n => n.type === 'transaction' && (n.value_paise ?? 0) > 0)
      .reduce((s, n) => s + (n.value_paise ?? 0), 0);

    if (totalIncome > 0 && totalExpenses > totalIncome * 0.9) {
      const evidence = this.buildAlertEvidence(
        'low_liquidity',
        `Expenses (₹${(totalExpenses / 100).toLocaleString('en-IN')}) are ${((totalExpenses / totalIncome) * 100).toFixed(0)}% of income (₹${(totalIncome / 100).toLocaleString('en-IN')})`,
        nodes,
      );
      return insightBuilder.buildAlert(
        'alert-low-liquidity',
        'low_liquidity',
        'high',
        2,
        'Low Liquidity Warning',
        `Your expenses consume ${((totalExpenses / totalIncome) * 100).toFixed(0)}% of income, leaving minimal buffer for emergencies.`,
        evidence,
        'alert',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
    }
    return null;
  }

  private checkNegativeSavings(nodes: IntelligenceContext['nodes']): Alert | null {
    let savingsRateBps = 0;
    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.savings_rate_bps !== undefined) {
        savingsRateBps = meta.savings_rate_bps as number;
      }
    }

    if (savingsRateBps <= 0) {
      const evidence = this.buildAlertEvidence(
        'negative_savings',
        'Savings rate is zero or negative',
        nodes,
      );
      return insightBuilder.buildAlert(
        'alert-negative-savings',
        'negative_savings',
        'critical',
        1,
        'Negative Savings Rate',
        'Your expenses are exceeding or equal to your income. This is unsustainable long-term.',
        evidence,
        'alert',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
    }
    return null;
  }

  private checkGambling(nodes: IntelligenceContext['nodes']): Alert | null {
    const gamblingKeywords = ['dream11', 'mpl', 'rummy', 'bet', 'casino', 'poker', 'teen patti', 'my11circle', 'fantasy', 'betting', 'gambl'];
    const gamblingNodes = nodes.filter(n => {
      const label = n.label.toLowerCase();
      const desc = ((n.metadata?.description as string) || '').toLowerCase();
      return gamblingKeywords.some(kw => label.includes(kw) || desc.includes(kw));
    });

    if (gamblingNodes.length > 0) {
      const totalGambling = gamblingNodes.reduce((s, n) => s + Math.abs(n.value_paise ?? 0), 0);
      const evidence = this.buildAlertEvidence(
        'gambling_detected',
        `${gamblingNodes.length} gambling transactions totaling ₹${(totalGambling / 100).toLocaleString('en-IN')}`,
        nodes,
      );
      return insightBuilder.buildAlert(
        'alert-gambling',
        'gambling_detected',
        'high',
        1,
        'Gambling Transactions Detected',
        `${gamblingNodes.length} transactions linked to gaming/gambling platforms totaling ₹${(totalGambling / 100).toLocaleString('en-IN')}. Monitor for addictive patterns.`,
        evidence,
        'alert',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
    }
    return null;
  }

  private checkLoanAppPattern(nodes: IntelligenceContext['nodes']): Alert | null {
    const loanKeywords = ['loan', 'nbfc', 'credit', 'lend', 'finance', 'cash', 'instant'];
    const loanNodes = nodes.filter(n => {
      const label = n.label.toLowerCase();
      const desc = ((n.metadata?.description as string) || '').toLowerCase();
      return loanKeywords.some(kw => label.includes(kw) || desc.includes(kw));
    });

    if (loanNodes.length >= 2) {
      const evidence = this.buildAlertEvidence(
        'loan_app_pattern',
        `${loanNodes.length} loan-related transactions detected`,
        nodes,
      );
      return insightBuilder.buildAlert(
        'alert-loan-app',
        'loan_app_pattern',
        'high',
        1,
        'Loan App Activity Detected',
        `${loanNodes.length} loan-related credits detected. Multiple loan apps may indicate financial stress.`,
        evidence,
        'alert',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
    }
    return null;
  }

  private checkGoalDeviation(nodes: IntelligenceContext['nodes']): Alert | null {
    // Check for any goal-related nodes that show deviation
    const goalNodes = nodes.filter(n =>
      n.type === 'behaviour_score' &&
      n.label.toLowerCase().includes('goal')
    );

    if (goalNodes.length > 0) {
      for (const node of goalNodes) {
        if (node.confidence !== undefined && node.confidence < 30) {
          const evidence = this.buildAlertEvidence(
            'goal_deviation',
            `Goal progress is below target: ${node.label}`,
            nodes,
          );
          return insightBuilder.buildAlert(
            `alert-goal-deviation-${node.id}`,
            'goal_deviation',
            'medium',
            3,
            'Goal Progress Alert',
            `Your goal "${node.label}" is behind schedule. Review and adjust your plan.`,
            evidence,
            'alert',
            nodes.map(n => n.id),
            { requiresAcknowledgement: false },
          );
        }
      }
    }
    return null;
  }

  private checkReconciliation(nodes: IntelligenceContext['nodes']): Alert | null {
    const discrepancyNodes = nodes.filter(n => n.type === 'discrepancy');

    if (discrepancyNodes.length > 0) {
      const evidence = this.buildAlertEvidence(
        'reconciliation_issue',
        `${discrepancyNodes.length} reconciliation discrepancies found`,
        nodes,
      );
      return insightBuilder.buildAlert(
        'alert-reconciliation',
        'reconciliation_issue',
        'high',
        2,
        'Reconciliation Discrepancies',
        `${discrepancyNodes.length} discrepancies found between your records and bank statements. Review and resolve.`,
        evidence,
        'alert',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
    }
    return null;
  }

  private buildAlertEvidence(type: string, detail: string, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('alert_trigger', detail, 'alert-engine', 80),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Generate Alert', `Evaluate ${type} conditions`, { alert_type: type }, { triggered: true }),
    ];
    return insightBuilder.buildEvidenceChain(`Alert: ${type}`, evidence, calculationSteps, [], 75);
  }
}