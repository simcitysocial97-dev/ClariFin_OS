/**
 * Debt Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic debt intelligence engine.
 * Analyzes debt structure, computes DTI, detects risky patterns.
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

export class DebtEngine implements IntelligenceEngine {
  readonly name = 'debt' as const;

  compute(context: IntelligenceContext): EngineResult {
    const insights: Insight[] = [];
    const alerts: Alert[] = [];
    const riskScores: RiskScore[] = [];
    const nodes = context.nodes;
    const config = context.config;

    // Extract debt metrics
    const debtMetrics = this.extractDebtMetrics(nodes);
    const dtiRatio = this.computeDTI(debtMetrics);
    const emiBurden = this.computeEMIBurden(nodes);

    // Generate debt risk score
    const riskFactors: RiskFactor[] = [];
    if (dtiRatio > 0) {
      riskFactors.push({
        name: 'Debt-to-Income Ratio',
        contribution: Math.min(100, dtiRatio * 100),
        description: `DTI ratio is ${(dtiRatio * 100).toFixed(1)}%`,
        current_value: `${(dtiRatio * 100).toFixed(1)}%`,
        threshold: `${(config.thresholds.debt_to_income_threshold * 100).toFixed(0)}%`,
      });
    }
    if (emiBurden > 0) {
      riskFactors.push({
        name: 'EMI Burden',
        contribution: Math.min(100, emiBurden * 100),
        description: `EMI burden is ${(emiBurden * 100).toFixed(1)}% of income`,
        current_value: `${(emiBurden * 100).toFixed(1)}%`,
        threshold: `${(config.thresholds.emi_ratio_threshold * 100).toFixed(0)}%`,
      });
    }

    if (riskFactors.length > 0) {
      const evidence = this.buildDebtRiskEvidence(dtiRatio, emiBurden, nodes);
      const riskScore = insightBuilder.buildRiskScore(
        'risk-debt',
        'debt',
        Math.min(100, riskFactors.reduce((s, f) => s + f.contribution, 0) / riskFactors.length),
        evidence.confidence_score,
        riskFactors,
        evidence,
        nodes.map(n => n.id),
      );
      riskScores.push(riskScore);
    }

    // Generate alerts for high DTI
    if (dtiRatio > config.thresholds.debt_to_income_threshold) {
      const evidence = this.buildDTIAlertEvidence(dtiRatio, nodes);
      const alert = insightBuilder.buildAlert(
        'alert-debt-high-dti',
        'debt_risk',
        dtiRatio > 0.6 ? 'critical' : 'high',
        dtiRatio > 0.6 ? 1 : 2,
        'High Debt-to-Income Ratio',
        `Your DTI ratio is ${(dtiRatio * 100).toFixed(1)}%. Recommended maximum is ${(config.thresholds.debt_to_income_threshold * 100).toFixed(0)}%.`,
        evidence,
        'debt',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
      alerts.push(alert);
    }

    // Generate alerts for high EMI burden
    if (emiBurden > config.thresholds.emi_ratio_threshold) {
      const evidence = this.buildEMIAlertEvidence(emiBurden, nodes);
      const alert = insightBuilder.buildAlert(
        'alert-debt-emi-burden',
        'emi_burden',
        emiBurden > 0.5 ? 'critical' : 'high',
        emiBurden > 0.5 ? 1 : 2,
        'High EMI Burden',
        `EMI payments are ${(emiBurden * 100).toFixed(1)}% of income. Recommended maximum is ${(config.thresholds.emi_ratio_threshold * 100).toFixed(0)}%.`,
        evidence,
        'debt',
        nodes.map(n => n.id),
        { requiresAcknowledgement: true },
      );
      alerts.push(alert);
    }

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

  private extractDebtMetrics(nodes: IntelligenceContext['nodes']): { total_debt_paise: number; total_income_paise: number } {
    let totalDebtPaise = 0;
    let totalIncomePaise = 0;

    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.total_debt_paise !== undefined) totalDebtPaise = meta.total_debt_paise as number;
      if (meta.total_income_paise !== undefined) totalIncomePaise = meta.total_income_paise as number;
      if (meta.debt_to_income_bps !== undefined) {
        // Already have DTI, extract from it
      }
    }

    return { total_debt_paise: totalDebtPaise, total_income_paise: totalIncomePaise };
  }

  private computeDTI(metrics: { total_debt_paise: number; total_income_paise: number }): number {
    if (metrics.total_income_paise <= 0) return 0;
    return metrics.total_debt_paise / metrics.total_income_paise;
  }

  private computeEMIBurden(nodes: IntelligenceContext['nodes']): number {
    let totalEMIPaise = 0;
    let totalIncomePaise = 0;

    for (const node of nodes) {
      const meta = node.metadata;
      if (meta.emi_total_paise !== undefined) totalEMIPaise = meta.emi_total_paise as number;
      if (meta.income_paise !== undefined) totalIncomePaise = meta.income_paise as number;
    }

    if (totalIncomePaise <= 0) return 0;
    return totalEMIPaise / totalIncomePaise;
  }

  private buildDebtRiskEvidence(dti: number, emi: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence('dti_ratio', `DTI ratio: ${(dti * 100).toFixed(1)}%`, 'debt-engine', 80),
      insightBuilder.createEvidence('emi_burden', `EMI burden: ${(emi * 100).toFixed(1)}%`, 'debt-engine', 70),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep('Compute DTI', 'Total debt divided by total income', { total_debt_paise: 0, total_income_paise: 0 }, { dti_ratio: dti }),
      insightBuilder.createCalculationStep('Compute EMI Burden', 'Total EMI divided by total income', { emi_total_paise: 0, income_paise: 0 }, { emi_ratio: emi }),
    ];
    return insightBuilder.buildEvidenceChain(`Debt risk assessment: DTI ${(dti * 100).toFixed(1)}%, EMI ${(emi * 100).toFixed(1)}%`, evidence, calculationSteps, [], 75);
  }

  private buildDTIAlertEvidence(dti: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [insightBuilder.createEvidence('dti_alert', `DTI ratio ${(dti * 100).toFixed(1)}% exceeds threshold`, 'debt-engine', 85)];
    const calculationSteps = [insightBuilder.createCalculationStep('Check DTI Threshold', 'Compare DTI against threshold', { dti, threshold: 0.4 }, { exceeds_threshold: true })];
    return insightBuilder.buildEvidenceChain(`DTI alert: ${(dti * 100).toFixed(1)}%`, evidence, calculationSteps, [], 80);
  }

  private buildEMIAlertEvidence(emi: number, _nodes: IntelligenceContext['nodes']): EvidenceChain {
    const evidence = [insightBuilder.createEvidence('emi_alert', `EMI burden ${(emi * 100).toFixed(1)}% exceeds threshold`, 'debt-engine', 85)];
    const calculationSteps = [insightBuilder.createCalculationStep('Check EMI Threshold', 'Compare EMI ratio against threshold', { emi, threshold: 0.4 }, { exceeds_threshold: true })];
    return insightBuilder.buildEvidenceChain(`EMI alert: ${(emi * 100).toFixed(1)}%`, evidence, calculationSteps, [], 80);
  }
}