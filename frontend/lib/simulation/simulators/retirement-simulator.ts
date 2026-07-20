/**
 * Retirement Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic retirement projection engine.
 * Projects retirement corpus based on current savings and SIP.
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

// ===== Retirement Simulator =====
/**
 * Projects retirement corpus based on current savings and SIP contributions.
 */
export class RetirementSimulator implements SimulationEngine {
  readonly name = 'retirement' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = this.getRetirementNodeIds(context.nodes);

    // Extract retirement data
    const retirementData = this.extractRetirementData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      retirementData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'retirement-baseline',
      'Baseline Retirement Projection',
      'Projects retirement corpus based on current savings and SIP',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(retirementData),
      this.buildEvidenceChain(retirementData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_retirement_savings',
        'Current retirement savings',
        { valuePaise: retirementData.currentSavings },
      ),
      simulationBuilder.createOutput(
        'projected_retirement_corpus',
        'Final projected retirement corpus',
        { valuePaise: projections.length > 0 ? projections[projections.length - 1].value_paise : retirementData.currentSavings },
      ),
      simulationBuilder.createOutput(
        'required_sip',
        'Required monthly SIP for target corpus',
        { valuePaise: retirementData.requiredSip },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'retirement',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(retirementData, projections, context.nodes),
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

  private getRetirementNodeIds(nodes: SimulationContext['nodes']): string[] {
    return nodes
      .filter(n => n.type === 'investment' || n.type === 'goal')
      .map(n => n.id);
  }

  private extractRetirementData(nodes: SimulationContext['nodes']): {
    currentSavings: number;
    monthlySip: number;
    expectedReturnBps: number;
    targetCorpus: number;
    yearsToRetirement: number;
    requiredSip: number;
  } {
    let currentSavings = 0;
    let monthlySip = 0;
    let expectedReturnBps = 800; // Default 8%
    let targetCorpus = 1000000000; // Default 1 crore (10 million paise)
    let yearsToRetirement = 25; // Default 25 years

    for (const node of nodes) {
      if (node.type === 'investment' && node.value_paise !== undefined) {
        currentSavings += node.value_paise;
        const contribution = (node.metadata?.monthly_contribution_paise as number) ?? 0;
        monthlySip += contribution;
        const returnRate = (node.metadata?.expected_return_bps as number) ?? 800;
        expectedReturnBps = returnRate;
      }
      if (node.type === 'goal' && node.metadata?.target_paise !== undefined) {
        targetCorpus = node.metadata.target_paise as number;
        const targetDate = (node.metadata?.target_date as string) ?? '';
        if (targetDate) {
          const currentYear = new Date().getFullYear();
          const targetYear = parseInt(targetDate.substring(0, 4), 10);
          yearsToRetirement = Math.max(1, targetYear - currentYear);
        }
      }
    }

    // Calculate required SIP to reach target corpus
    const monthsToRetirement = yearsToRetirement * 12;
    const monthlyReturn = expectedReturnBps / 120000;
    const requiredSip = monthsToRetirement > 0
      ? Math.round((targetCorpus - currentSavings) / ((Math.pow(1 + monthlyReturn, monthsToRetirement) - 1) / monthlyReturn))
      : 0;

    return {
      currentSavings,
      monthlySip,
      expectedReturnBps,
      targetCorpus,
      yearsToRetirement,
      requiredSip,
    };
  }

  private generateProjections(
    retirementData: {
      currentSavings: number;
      monthlySip: number;
      expectedReturnBps: number;
      targetCorpus: number;
      yearsToRetirement: number;
      requiredSip: number;
    },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];
    const monthlyReturn = retirementData.expectedReturnBps / 120000;
    const monthsToRetirement = retirementData.yearsToRetirement * 12;
    const maxMonths = Math.min(horizonMonths, monthsToRetirement);

    let value = retirementData.currentSavings;

    for (let i = 0; i <= maxMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);

      // Compound growth with monthly SIP
      if (i > 0) {
        value = Math.round(value * (1 + monthlyReturn) + retirementData.monthlySip);
      }

      const projection = simulationBuilder.createProjection(
        `retirement-proj-${i}`,
        'retirement_corpus',
        date,
        value,
        65, // 65% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(retirementData: {
    currentSavings: number;
    monthlySip: number;
    expectedReturnBps: number;
    targetCorpus: number;
    yearsToRetirement: number;
    requiredSip: number;
  }): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-returns',
        `Investments return ${retirementData.expectedReturnBps / 100}% annual rate (historical average)`,
        'market',
        retirementData.expectedReturnBps,
        65,
      ),
      simulationBuilder.createAssumption(
        'assumption-sip-consistency',
        'Monthly SIP contributions remain consistent',
        'income',
        retirementData.monthlySip,
        80,
      ),
      simulationBuilder.createAssumption(
        'assumption-retirement-age',
        `Retirement in ${retirementData.yearsToRetirement} years`,
        'behavioral',
        retirementData.yearsToRetirement,
        75,
      ),
    ];
  }

  private buildEvidenceChain(
    retirementData: {
      currentSavings: number;
      monthlySip: number;
      expectedReturnBps: number;
      targetCorpus: number;
      yearsToRetirement: number;
      requiredSip: number;
    },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'retirement_data',
        `Current savings: ${retirementData.currentSavings} paise, target: ${retirementData.targetCorpus} paise`,
        'retirement-simulator',
        85,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Retirement Data',
        'Get current savings, SIP, and target corpus',
        { node_count: nodes.length },
        {
          current_savings_paise: retirementData.currentSavings,
          monthly_sip_paise: retirementData.monthlySip,
          target_corpus_paise: retirementData.targetCorpus,
        },
      ),
      simulationBuilder.createCalculationStep(
        'Project Retirement Corpus',
        `Calculate compound growth for ${projections.length} months`,
        { monthly_return: retirementData.expectedReturnBps / 120000 },
        { final_corpus_paise: projections[projections.length - 1]?.value_paise ?? 0 },
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
      `Retirement projection: ${retirementData.currentSavings} paise growing to ${projections[projections.length - 1]?.value_paise ?? 0} paise`,
      evidence,
      calculationSteps,
      sourceReferences,
      65,
    );
  }
}
