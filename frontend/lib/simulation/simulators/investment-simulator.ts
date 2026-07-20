/**
 * Investment Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic investment growth projection engine.
 * Projects investment value based on current holdings and expected returns.
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

// ===== Investment Simulator =====
/**
 * Projects investment growth based on current holdings and expected returns.
 */
export class InvestmentSimulator implements SimulationEngine {
  readonly name = 'investment' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = this.getInvestmentNodeIds(context.nodes);

    // Extract investment data
    const investmentData = this.extractInvestmentData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      investmentData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'investment-baseline',
      'Baseline Investment Growth Projection',
      'Projects future investment value based on current holdings',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(investmentData),
      this.buildEvidenceChain(investmentData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_investment_value',
        'Current total investment value',
        { valuePaise: investmentData.currentValue },
      ),
      simulationBuilder.createOutput(
        'projected_investment_value',
        'Final projected investment value',
        { valuePaise: projections.length > 0 ? projections[projections.length - 1].value_paise : investmentData.currentValue },
      ),
      simulationBuilder.createOutput(
        'expected_growth',
        'Expected growth over horizon',
        { valuePaise: (projections.length > 0 ? projections[projections.length - 1].value_paise : 0) - investmentData.currentValue },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'investment',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(investmentData, projections, context.nodes),
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

  private getInvestmentNodeIds(nodes: SimulationContext['nodes']): string[] {
    return nodes
      .filter(n => n.type === 'investment' || n.type === 'holding')
      .map(n => n.id);
  }

  private extractInvestmentData(nodes: SimulationContext['nodes']): {
    currentValue: number;
    monthlyContribution: number;
    expectedReturnBps: number;
  } {
    let currentValue = 0;
    let monthlyContribution = 0;
    let expectedReturnBps = 800; // Default 8%

    for (const node of nodes) {
      if (node.type === 'investment' && node.value_paise !== undefined) {
        currentValue += node.value_paise;
        const contribution = (node.metadata?.monthly_contribution_paise as number) ?? 0;
        monthlyContribution += contribution;
        const returnRate = (node.metadata?.expected_return_bps as number) ?? 800;
        expectedReturnBps = returnRate;
      }
    }

    return {
      currentValue,
      monthlyContribution,
      expectedReturnBps,
    };
  }

  private generateProjections(
    investmentData: {
      currentValue: number;
      monthlyContribution: number;
      expectedReturnBps: number;
    },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];
    const monthlyReturn = investmentData.expectedReturnBps / 120000; // Convert bps to monthly rate

    let value = investmentData.currentValue;

    for (let i = 0; i <= horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);

      // Compound growth with monthly contributions
      if (i > 0) {
        value = Math.round(value * (1 + monthlyReturn) + investmentData.monthlyContribution);
      }

      const projection = simulationBuilder.createProjection(
        `investment-proj-${i}`,
        'investment_value',
        date,
        value,
        70, // 70% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(investmentData: {
    currentValue: number;
    monthlyContribution: number;
    expectedReturnBps: number;
  }): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-returns',
        `Investments return ${investmentData.expectedReturnBps / 100}% annual rate (historical average)`,
        'market',
        investmentData.expectedReturnBps,
        65,
      ),
      simulationBuilder.createAssumption(
        'assumption-contributions',
        'Monthly contributions remain consistent',
        'income',
        investmentData.monthlyContribution,
        80,
      ),
    ];
  }

  private buildEvidenceChain(
    investmentData: {
      currentValue: number;
      monthlyContribution: number;
      expectedReturnBps: number;
    },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'investment_data',
        `Current investment value: ${investmentData.currentValue} paise`,
        'investment-simulator',
        90,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Investment Data',
        'Get current value and contribution from investment nodes',
        { node_count: nodes.length },
        {
          current_value_paise: investmentData.currentValue,
          monthly_contribution_paise: investmentData.monthlyContribution,
          expected_return_bps: investmentData.expectedReturnBps,
        },
      ),
      simulationBuilder.createCalculationStep(
        'Project Investment Value',
        `Calculate compound growth for ${projections.length} months`,
        { monthly_return: investmentData.expectedReturnBps / 120000 },
        { final_value_paise: projections[projections.length - 1]?.value_paise ?? 0 },
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
      `Investment projection: ${investmentData.currentValue} paise growing to ${projections[projections.length - 1]?.value_paise ?? 0} paise`,
      evidence,
      calculationSteps,
      sourceReferences,
      70,
    );
  }
}