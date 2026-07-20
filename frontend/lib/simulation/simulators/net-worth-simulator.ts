/**
 * Net Worth Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic net worth projection engine.
 * Projects future net worth based on account balances and cashflow.
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

// ===== Net Worth Simulator =====
/**
 * Projects future net worth based on current assets, liabilities, and cashflow.
 */
export class NetWorthSimulator implements SimulationEngine {
  readonly name = 'net_worth' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = options?.focus_node_ids ?? context.nodes.map(n => n.id);

    // Extract current net worth
    const currentNetWorth = this.extractNetWorth(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      currentNetWorth,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'net-worth-baseline',
      'Baseline Net Worth Projection',
      'Projects future net worth based on current assets and cashflow trends',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(),
      this.buildEvidenceChain(currentNetWorth, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_net_worth',
        'Current net worth',
        { valuePaise: currentNetWorth },
      ),
      simulationBuilder.createOutput(
        'projected_net_worth',
        'Final projected net worth',
        { valuePaise: projections.length > 0 ? projections[projections.length - 1].value_paise : currentNetWorth },
      ),
      simulationBuilder.createOutput(
        'net_worth_growth',
        'Projected net worth growth',
        { valuePaise: (projections.length > 0 ? projections[projections.length - 1].value_paise : 0) - currentNetWorth },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'net_worth',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(currentNetWorth, projections, context.nodes),
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

  private extractNetWorth(nodes: SimulationContext['nodes']): number {
    let total = 0;

    for (const node of nodes) {
      if (node.value_paise !== undefined) {
        // Accounts and investments contribute positively
        if (node.type === 'account' || node.type === 'investment' || node.type === 'holding') {
          total += node.value_paise;
        }
        // Loans and credit cards contribute negatively (liabilities)
        else if (node.type === 'loan' || node.type === 'credit_card') {
          total -= node.value_paise;
        }
      }
    }

    return total;
  }

  private generateProjections(
    currentNetWorth: number,
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];
    // Assume 5% annual growth (600 bps) for net worth
    const monthlyGrowthBps = 50; // ~0.5% monthly

    for (let i = 0; i <= horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);
      // Compound growth
      const projectedValue = Math.round(currentNetWorth * Math.pow(1 + monthlyGrowthBps / 10000, i));

      const projection = simulationBuilder.createProjection(
        `net-worth-proj-${i}`,
        'net_worth',
        date,
        projectedValue,
        75, // 75% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-net-worth-growth',
        'Net worth grows at 5% annual rate (historical average)',
        'growth',
        500, // 5% in bps
        70,
      ),
      simulationBuilder.createAssumption(
        'assumption-investment-returns',
        'Investments return 8% annual rate (historical average)',
        'market',
        800, // 8% in bps
        65,
      ),
    ];
  }

  private buildEvidenceChain(
    currentNetWorth: number,
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'account_data',
        `Current net worth calculated from ${nodes.length} graph nodes`,
        'net-worth-simulator',
        90,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Current Net Worth',
        'Sum all account balances and subtract liabilities',
        { node_count: nodes.length },
        { current_net_worth_paise: currentNetWorth },
      ),
      simulationBuilder.createCalculationStep(
        'Project Net Worth',
        `Project net worth for ${projections.length} months with compound growth`,
        { growth_rate_bps: 50 },
        { final_net_worth_paise: projections[projections.length - 1]?.value_paise ?? 0 },
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
      `Net worth projection: ${currentNetWorth} paise current, growing to ${projections[projections.length - 1]?.value_paise ?? 0} paise`,
      evidence,
      calculationSteps,
      sourceReferences,
      75,
    );
  }
}