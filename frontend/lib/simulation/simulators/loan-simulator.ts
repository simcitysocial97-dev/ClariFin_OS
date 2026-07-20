/**
 * Loan Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic loan payoff simulation engine.
 * Projects loan payoff scenarios and prepayment impact.
 *
 * All monetary values in paise (integer).
 * All rates in basis points (integer).
 *
 * Reuses backend loan engine calculations via the graph context.
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

// ===== Loan Simulator =====
/**
 * Simulates loan payoff scenarios and prepayment impact.
 */
export class LoanSimulator implements SimulationEngine {
  readonly name = 'loan' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = this.getLoanNodeIds(context.nodes);

    // Extract loan data
    const loanData = this.extractLoanData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      loanData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'loan-baseline',
      'Baseline Loan Payoff Projection',
      'Projects future loan balance based on current schedule',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(loanData),
      this.buildEvidenceChain(loanData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_outstanding',
        'Current loan outstanding',
        { valuePaise: loanData.currentOutstanding },
      ),
      simulationBuilder.createOutput(
        'projected_outstanding',
        'Final projected loan balance',
        { valuePaise: projections.length > 0 ? projections[projections.length - 1].value_paise : loanData.currentOutstanding },
      ),
      simulationBuilder.createOutput(
        'months_to_payoff',
        'Estimated months to payoff',
        { value: loanData.monthsToPayoff },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'loan',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(loanData, projections, context.nodes),
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

  private getLoanNodeIds(nodes: SimulationContext['nodes']): string[] {
    return nodes
      .filter(n => n.type === 'loan' || n.type === 'amortization_entry')
      .map(n => n.id);
  }

  private extractLoanData(nodes: SimulationContext['nodes']): {
    currentOutstanding: number;
    annualRateBps: number;
    emiPaise: number;
    monthsToPayoff: number;
  } {
    let currentOutstanding = 0;
    let annualRateBps = 850; // Default 8.5%
    let emiPaise = 0;
    let monthsToPayoff = 0;

    for (const node of nodes) {
      if (node.type === 'loan') {
        currentOutstanding = node.value_paise ?? 0;
        annualRateBps = (node.metadata?.annual_rate_bps as number) ?? 850;
        emiPaise = (node.metadata?.emi_paise as number) ?? 0;
        monthsToPayoff = (node.metadata?.tenure_months as number) ?? 0;
      }
    }

    return {
      currentOutstanding,
      annualRateBps,
      emiPaise,
      monthsToPayoff,
    };
  }

  private generateProjections(
    loanData: {
      currentOutstanding: number;
      annualRateBps: number;
      emiPaise: number;
      monthsToPayoff: number;
    },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];
    const monthlyRate = loanData.annualRateBps / 120000; // Convert bps to monthly rate

    let balance = loanData.currentOutstanding;
    const maxMonths = Math.min(horizonMonths, loanData.monthsToPayoff);

    for (let i = 0; i <= maxMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);

      // Calculate interest for this month
      const interest = Math.round((balance * monthlyRate));
      const principal = Math.min(loanData.emiPaise - interest, balance);
      balance = Math.max(0, balance - principal);

      const projection = simulationBuilder.createProjection(
        `loan-proj-${i}`,
        'loan_balance',
        date,
        balance,
        85, // 85% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private getDefaultAssumptions(loanData: {
    currentOutstanding: number;
    annualRateBps: number;
    emiPaise: number;
    monthsToPayoff: number;
  }): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-rate-stability',
        `Interest rate remains at ${loanData.annualRateBps / 100}% for loan term`,
        'rate',
        loanData.annualRateBps,
        90,
      ),
      simulationBuilder.createAssumption(
        'assumption-emi-stability',
        'EMI payments remain consistent',
        'income',
        loanData.emiPaise,
        85,
      ),
    ];
  }

  private buildEvidenceChain(
    loanData: {
      currentOutstanding: number;
      annualRateBps: number;
      emiPaise: number;
      monthsToPayoff: number;
    },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'loan_data',
        `Current loan balance: ${loanData.currentOutstanding} paise at ${loanData.annualRateBps / 100}%`,
        'loan-simulator',
        95,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Loan Parameters',
        'Get current outstanding, rate, and EMI from loan nodes',
        { node_count: nodes.length },
        {
          current_outstanding_paise: loanData.currentOutstanding,
          annual_rate_bps: loanData.annualRateBps,
          emi_paise: loanData.emiPaise,
        },
      ),
      simulationBuilder.createCalculationStep(
        'Project Loan Balance',
        `Calculate amortization for ${projections.length} months`,
        { monthly_rate: loanData.annualRateBps / 120000 },
        { final_balance_paise: projections[projections.length - 1]?.value_paise ?? 0 },
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
      `Loan projection: ${loanData.currentOutstanding} paise outstanding, ${loanData.monthsToPayoff} months to payoff`,
      evidence,
      calculationSteps,
      sourceReferences,
      85,
    );
  }
}