/**
 * Budget Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic budget scenario simulation engine.
 * Simulates budget scenarios with category spending limits.
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

// ===== Budget Simulator =====
/**
 * Simulates budget scenarios with category spending limits.
 */
export class BudgetSimulator implements SimulationEngine {
  readonly name = 'budget' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = options?.focus_node_ids ?? context.nodes.map(n => n.id);

    // Extract spending patterns
    const spendingPatterns = this.extractSpendingPatterns(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      spendingPatterns,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'budget-baseline',
      'Baseline Budget Projection',
      'Projects future budget based on current spending patterns',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(),
      this.buildEvidenceChain(spendingPatterns, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'total_monthly_spending',
        'Total monthly spending',
        { valuePaise: spendingPatterns.totalMonthlySpending },
      ),
      simulationBuilder.createOutput(
        'spending_by_category',
        'Spending breakdown by category',
        { value: JSON.stringify(spendingPatterns.categorySpending) },
      ),
      simulationBuilder.createOutput(
        'potential_savings',
        'Potential savings if spending reduced by 10%',
        { valuePaise: Math.round(spendingPatterns.totalMonthlySpending * 0.1) },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'budget',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(spendingPatterns, projections, context.nodes),
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

  private extractSpendingPatterns(nodes: SimulationContext['nodes']): {
    totalMonthlySpending: number;
    categorySpending: Record<string, number>;
  } {
    const categorySpending: Record<string, number> = {};
    let totalSpending = 0;

    for (const node of nodes) {
      if (node.type === 'transaction' && node.value_paise !== undefined && node.value_paise < 0) {
        const category = (node.metadata?.category as string) ?? 'other';
        const absValue = Math.abs(node.value_paise);
        categorySpending[category] = (categorySpending[category] ?? 0) + absValue;
        totalSpending += absValue;
      }
    }

    // Assume 3 months of data
    const monthsOfData = 3;
    return {
      totalMonthlySpending: Math.round(totalSpending / monthsOfData),
      categorySpending: this.averageByCategory(categorySpending, monthsOfData),
    };
  }

  private averageByCategory(
    categorySpending: Record<string, number>,
    months: number,
  ): Record<string, number> {
    const result: Record<string, number> = {};
    for (const [category, amount] of Object.entries(categorySpending)) {
      result[category] = Math.round(amount / months);
    }
    return result;
  }

  private generateProjections(
    patterns: { totalMonthlySpending: number; categorySpending: Record<string, number> },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];

    for (let i = 0; i < horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);
      const projection = simulationBuilder.createProjection(
        `budget-proj-${i}`,
        'cashflow',
        date,
        -patterns.totalMonthlySpending, // Negative for spending
        70, // 70% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-spending-patterns',
        'Spending patterns remain consistent with historical data',
        'behavioral',
        70,
      ),
      simulationBuilder.createAssumption(
        'assumption-inflation',
        'Inflation affects spending at 3% annual rate',
        'inflation',
        300, // 3% in bps
        80,
      ),
    ];
  }

  private buildEvidenceChain(
    patterns: { totalMonthlySpending: number; categorySpending: Record<string, number> },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'spending_data',
        `Analyzed spending patterns across ${Object.keys(patterns.categorySpending).length} categories`,
        'budget-simulator',
        80,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Spending Patterns',
        'Calculate average monthly spending by category',
        { node_count: nodes.length },
        { total_monthly_spending_paise: patterns.totalMonthlySpending },
      ),
      simulationBuilder.createCalculationStep(
        'Generate Budget Projections',
        `Project spending for ${projections.length} months`,
        { categories: Object.keys(patterns.categorySpending) },
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
      `Budget projection: ${patterns.totalMonthlySpending} paise monthly spending`,
      evidence,
      calculationSteps,
      sourceReferences,
      70,
    );
  }
}