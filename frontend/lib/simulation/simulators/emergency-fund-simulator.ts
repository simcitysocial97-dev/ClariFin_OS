/**
 * Emergency Fund Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic emergency fund projection engine.
 * Projects emergency fund adequacy based on expenses and savings rate.
 *
 * All monetary values in paise (integer).
 * All rates in basis points (integer).
 */

import type {
  SimulationEngine,
  SimulationContext,
  SimulationResult,
  SimulationOptions,
  SimulationEvidenceChain,
  SimulationOutput,
} from '../types';
import { simulationBuilder } from '../insight-builder';

// ===== Emergency Fund Simulator =====
/**
 * Projects emergency fund adequacy based on monthly expenses.
 */
export class EmergencyFundSimulator implements SimulationEngine {
  readonly name = 'emergency_fund' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = this.getEmergencyFundNodeIds(context.nodes);

    // Extract emergency fund data
    const fundData = this.extractFundData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      fundData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'emergency-fund-baseline',
      'Baseline Emergency Fund Projection',
      'Projects emergency fund adequacy based on savings rate',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(fundData),
      this.buildEvidenceChain(fundData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_fund',
        'Current emergency fund',
        { valuePaise: fundData.currentFund },
      ),
      simulationBuilder.createOutput(
        'target_fund',
        'Target emergency fund (3 months expenses)',
        { valuePaise: fundData.targetFund },
      ),
      simulationBuilder.createOutput(
        'months_covered',
        'Months of expenses covered',
        { value: fundData.monthsCovered },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'emergency_fund',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(fundData, projections, context.nodes),
      relatedNodes,
    );
  }

  reset(): void {
    // No state to reset
  }

  // ===== Private Methods =====

  private getBaseDate(nodes: SimulationContext['nodes']): string {
    const dates = nodes
      .map(n => n.date)
      .filter((d): d is string => d !== undefined)
      .sort((a, b) => b.localeCompare(a));

    return dates[0] ?? new Date().toISOString().split('T')[0] ?? '2025-01-01';
  }

  private getEmergencyFundNodeIds(nodes: SimulationContext['nodes']): string[] {
    return nodes
      .filter(n => n.type === 'account' || n.type === 'goal')
      .map(n => n.id);
  }

  private extractFundData(nodes: SimulationContext['nodes']): {
    currentFund: number;
    monthlyExpenses: number;
    monthlySavings: number;
    targetFund: number;
    monthsCovered: number;
  } {
    let currentFund = 0;
    let monthlyExpenses = 0;
    let monthlySavings = 0;

    for (const node of nodes) {
      if (node.type === 'account' && node.value_paise !== undefined) {
        // Assume savings accounts contribute to emergency fund
        const accountType = (node.metadata?.account_type as string) ?? '';
        if (accountType === 'savings') {
          currentFund += node.value_paise;
        }
      }
      if (node.type === 'transaction' && node.value_paise !== undefined) {
        if (node.value_paise < 0) {
          monthlyExpenses += Math.abs(node.value_paise);
        } else {
          monthlySavings += node.value_paise;
        }
      }
    }

    // Assume 3 months of data
    const monthsOfData = 3;
    const avgMonthlyExpenses = Math.round(monthlyExpenses / monthsOfData);
    const targetFund = avgMonthlyExpenses * 3; // 3 months target
    const monthsCovered = avgMonthlyExpenses > 0 ? currentFund / avgMonthlyExpenses : 0;

    return {
      currentFund,
      monthlyExpenses: avgMonthlyExpenses,
      monthlySavings: Math.round(monthlySavings / monthsOfData),
      targetFund,
      monthsCovered,
    };
  }

  private generateProjections(
    fundData: {
      currentFund: number;
      monthlyExpenses: number;
      monthlySavings: number;
      targetFund: number;
      monthsCovered: number;
    },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];

    let value = fundData.currentFund;
    const target = fundData.targetFund;

    for (let i = 0; i <= horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);

      // Add savings each month, cap at target
      if (i > 0) {
        value = Math.min(target, value + fundData.monthlySavings);
      }

      const projection = simulationBuilder.createProjection(
        `emergency-fund-proj-${i}`,
        'emergency_fund',
        date,
        value,
        80, // 80% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(fundData: {
    currentFund: number;
    monthlyExpenses: number;
    monthlySavings: number;
  }): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-savings-rate',
        'Monthly savings rate remains consistent',
        'income',
        fundData.monthlySavings,
        80,
      ),
      simulationBuilder.createAssumption(
        'assumption-expense-stability',
        'Monthly expenses remain stable',
        'expense',
        fundData.monthlyExpenses,
        75,
      ),
    ];
  }

  private buildEvidenceChain(
    fundData: {
      currentFund: number;
      monthlyExpenses: number;
      monthlySavings: number;
      targetFund: number;
      monthsCovered: number;
    },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'fund_data',
        `Emergency fund: ${fundData.currentFund} paise, target: ${fundData.targetFund} paise (${fundData.monthsCovered.toFixed(1)} months covered)`,
        'emergency-fund-simulator',
        85,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Fund Data',
        'Calculate current fund and target from account/transaction data',
        { node_count: nodes.length },
        {
          current_fund_paise: fundData.currentFund,
          target_fund_paise: fundData.targetFund,
          months_covered: fundData.monthsCovered,
        },
      ),
      simulationBuilder.createCalculationStep(
        'Project Emergency Fund',
        `Calculate fund growth for ${projections.length} months`,
        { monthly_savings_paise: fundData.monthlySavings },
        { final_fund_paise: projections[projections.length - 1]?.value_paise ?? 0 },
      ),
    ];

    const sourceReferences = nodes.slice(0, 5).map(n =>
      simulationBuilder.createSourceReference(
        n.id,
        'graph_node',
        n.label,
        n.date ?? new Date().toISOString(),
      ),
    );

    return simulationBuilder.buildEvidenceChain(
      `Emergency fund projection: ${fundData.currentFund} paise growing to ${projections[projections.length - 1]?.value_paise ?? 0} paise`,
      evidence,
      calculationSteps,
      sourceReferences,
      80,
    );
  }
}