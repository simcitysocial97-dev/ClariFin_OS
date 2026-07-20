/**
 * Cashflow Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic cashflow projection engine.
 * Projects future income and expenses based on historical patterns.
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

// ===== Cashflow Simulator =====
/**
 * Projects future cashflow based on historical transaction patterns.
 */
export class CashflowSimulator implements SimulationEngine {
  readonly name = 'cashflow' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = options?.focus_node_ids ?? context.nodes.map(n => n.id);

    // Extract historical cashflow data
    const historicalData = this.extractCashflowData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      historicalData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'cashflow-baseline',
      'Baseline Cashflow Projection',
      'Projects future cashflow based on historical patterns',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(),
      this.buildEvidenceChain(historicalData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'projected_net_cashflow',
        'Total projected net cashflow over horizon',
        { valuePaise: projections.reduce((sum, p) => sum + p.value_paise, 0) },
      ),
      simulationBuilder.createOutput(
        'projected_income',
        'Total projected income over horizon',
        { valuePaise: projections.reduce((sum, p) => sum + (p.value_paise > 0 ? p.value_paise : 0), 0) },
      ),
      simulationBuilder.createOutput(
        'projected_expenses',
        'Total projected expenses over horizon',
        { valuePaise: Math.abs(projections.reduce((sum, p) => sum + (p.value_paise < 0 ? p.value_paise : 0), 0)) },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'cashflow',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(historicalData, projections, context.nodes),
      relatedNodes,
    );
  }

  reset(): void {
    // No state to reset
  }

  // ===== Private Methods =====

  private getBaseDate(nodes: SimulationContext['nodes']): string {
    // Find the most recent date from nodes
    const dates = nodes
      .map(n => n.date)
      .filter((d): d is string => d !== undefined)
      .sort((a, b) => b.localeCompare(a));

    return dates[0] ?? new Date().toISOString().split('T')[0] ?? '2025-01-01';
  }

  private extractCashflowData(nodes: SimulationContext['nodes']): {
    monthlyIncome: number;
    monthlyExpenses: number;
    transactionCount: number;
  } {
    let totalIncome = 0;
    let totalExpenses = 0;
    let transactionCount = 0;

    for (const node of nodes) {
      if (node.type === 'transaction' && node.value_paise !== undefined) {
        transactionCount++;
        if (node.value_paise > 0) {
          totalIncome += node.value_paise;
        } else {
          totalExpenses += Math.abs(node.value_paise);
        }
      }
    }

    // Assume 3 months of data for monthly average
    const monthsOfData = 3;
    return {
      monthlyIncome: Math.round(totalIncome / monthsOfData),
      monthlyExpenses: Math.round(totalExpenses / monthsOfData),
      transactionCount,
    };
  }

  private generateProjections(
    data: { monthlyIncome: number; monthlyExpenses: number; transactionCount: number },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];
    const netCashflow = data.monthlyIncome - data.monthlyExpenses;

    for (let i = 0; i < horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);
      const projection = simulationBuilder.createProjection(
        `cashflow-proj-${i}`,
        'cashflow',
        date,
        netCashflow,
        80, // 80% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-income-stability',
        'Income remains stable at historical average',
        'income',
        80,
      ),
      simulationBuilder.createAssumption(
        'assumption-expense-stability',
        'Expenses remain stable at historical average',
        'expense',
        70,
      ),
    ];
  }

  private buildEvidenceChain(
    data: { monthlyIncome: number; monthlyExpenses: number; transactionCount: number },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'historical_data',
        `Analyzed ${data.transactionCount} transactions for cashflow patterns`,
        'cashflow-simulator',
        85,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Monthly Average',
        'Calculate average monthly income and expenses from transactions',
        { transaction_count: data.transactionCount },
        { monthly_income_paise: data.monthlyIncome, monthly_expenses_paise: data.monthlyExpenses },
      ),
      simulationBuilder.createCalculationStep(
        'Generate Projections',
        `Project cashflow for ${projections.length} months`,
        { horizon_months: projections.length },
        { projection_count: projections.length },
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
      `Cashflow projection: ${data.monthlyIncome - data.monthlyExpenses} paise net monthly`,
      evidence,
      calculationSteps,
      sourceReferences,
      80,
    );
  }
}