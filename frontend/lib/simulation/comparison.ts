/**
 * Scenario Comparison Engine - Stage 7 Simulation & Forecast Engine
 *
 * Compares multiple scenarios to provide insights on best/worst case outcomes.
 *
 * All monetary values in paise (integer).
 * All rates in basis points (integer).
 */

import type {
  SimulationResult,
  Scenario,
} from './types';

// ===== Comparison Result =====
export interface ComparisonResult {
  /** Name of the comparison */
  name: string;
  /** Scenarios being compared */
  scenarios: Scenario[];
  /** Key differences between scenarios */
  differences: ComparisonDifference[];
  /** Best case scenario */
  best_case: Scenario | null;
  /** Worst case scenario */
  worst_case: Scenario | null;
  /** Summary of comparison */
  summary: string;
}

export interface ComparisonDifference {
  /** Metric being compared */
  metric: string;
  /** Value in baseline scenario */
  baseline_value_paise: number;
  /** Value in comparison scenario */
  comparison_value_paise: number;
  /** Difference in paise */
  difference_paise: number;
  /** Percentage difference */
  percentage_difference: number;
}

// ===== Scenario Comparison Engine =====
/**
 * Compares multiple scenarios to identify best/worst outcomes.
 */
export class ScenarioComparisonEngine {
  /**
   * Compare two scenarios.
   */
  compare(
    baseline: SimulationResult,
    alternative: SimulationResult,
    name: string = 'Scenario Comparison',
  ): ComparisonResult {
    const differences = this.calculateDifferences(baseline, alternative);
    const bestCase = this.determineBestCase(baseline, alternative);
    const worstCase = this.determineWorstCase(baseline, alternative);

    return {
      name,
      scenarios: [baseline.scenario, alternative.scenario],
      differences,
      best_case: bestCase,
      worst_case: worstCase,
      summary: this.generateSummary(differences, bestCase, worstCase),
    };
  }

  /**
   * Compare multiple scenarios.
   */
  compareMultiple(
    results: SimulationResult[],
    name: string = 'Multi-Scenario Comparison',
  ): ComparisonResult {
    if (results.length < 2) {
      return {
        name,
        scenarios: results.map(r => r.scenario),
        differences: [],
        best_case: results[0]?.scenario ?? null,
        worst_case: results[0]?.scenario ?? null,
        summary: 'Need at least 2 scenarios to compare',
      };
    }

    // Compare all scenarios against the first (baseline)
    const baseline = results[0];
    const allDifferences: ComparisonDifference[] = [];

    for (let i = 1; i < results.length; i++) {
      allDifferences.push(...this.calculateDifferences(baseline, results[i]));
    }

    // Find best and worst across all scenarios
    const sortedByFinalValue = [...results].sort((a, b) => {
      const aFinal = a.timeline[a.timeline.length - 1]?.value_paise ?? 0;
      const bFinal = b.timeline[b.timeline.length - 1]?.value_paise ?? 0;
      return bFinal - aFinal; // Descending
    });

    return {
      name,
      scenarios: results.map(r => r.scenario),
      differences: allDifferences,
      best_case: sortedByFinalValue[0]?.scenario ?? null,
      worst_case: sortedByFinalValue[sortedByFinalValue.length - 1]?.scenario ?? null,
      summary: this.generateMultiSummary(results),
    };
  }

  /**
   * Find the best case scenario.
   */
  findBestCase(results: SimulationResult[]): SimulationResult | null {
    if (results.length === 0) return null;

    return results.reduce((best, current) => {
      const bestFinal = best.timeline[best.timeline.length - 1]?.value_paise ?? 0;
      const currentFinal = current.timeline[current.timeline.length - 1]?.value_paise ?? 0;
      return currentFinal > bestFinal ? current : best;
    });
  }

  /**
   * Find the worst case scenario.
   */
  findWorstCase(results: SimulationResult[]): SimulationResult | null {
    if (results.length === 0) return null;

    return results.reduce((worst, current) => {
      const worstFinal = worst.timeline[worst.timeline.length - 1]?.value_paise ?? 0;
      const currentFinal = current.timeline[current.timeline.length - 1]?.value_paise ?? 0;
      return currentFinal < worstFinal ? current : worst;
    });
  }

  // ===== Private Methods =====

  private calculateDifferences(
    baseline: SimulationResult,
    comparison: SimulationResult,
  ): ComparisonDifference[] {
    const differences: ComparisonDifference[] = [];

    // Compare final values
    const baselineFinal = baseline.timeline[baseline.timeline.length - 1]?.value_paise ?? 0;
    const comparisonFinal = comparison.timeline[comparison.timeline.length - 1]?.value_paise ?? 0;

    if (baselineFinal !== comparisonFinal) {
      const diff = comparisonFinal - baselineFinal;
      const pctDiff = baselineFinal !== 0 ? (diff / baselineFinal) * 100 : 0;

      differences.push({
        metric: 'final_value',
        baseline_value_paise: baselineFinal,
        comparison_value_paise: comparisonFinal,
        difference_paise: diff,
        percentage_difference: pctDiff,
      });
    }

    // Compare total outputs
    for (const output of comparison.outputs) {
      const baselineOutput = baseline.outputs.find(o => o.name === output.name);
      if (baselineOutput && output.value_paise !== undefined && baselineOutput.value_paise !== undefined) {
        const diff = output.value_paise - baselineOutput.value_paise;
        const pctDiff = baselineOutput.value_paise !== 0 ? (diff / baselineOutput.value_paise) * 100 : 0;

        differences.push({
          metric: output.name,
          baseline_value_paise: baselineOutput.value_paise,
          comparison_value_paise: output.value_paise,
          difference_paise: diff,
          percentage_difference: pctDiff,
        });
      }
    }

    return differences;
  }

  private determineBestCase(
    baseline: SimulationResult,
    alternative: SimulationResult,
  ): Scenario | null {
    const baselineFinal = baseline.timeline[baseline.timeline.length - 1]?.value_paise ?? 0;
    const alternativeFinal = alternative.timeline[alternative.timeline.length - 1]?.value_paise ?? 0;

    return alternativeFinal > baselineFinal ? alternative.scenario : baseline.scenario;
  }

  private determineWorstCase(
    baseline: SimulationResult,
    alternative: SimulationResult,
  ): Scenario | null {
    const baselineFinal = baseline.timeline[baseline.timeline.length - 1]?.value_paise ?? 0;
    const alternativeFinal = alternative.timeline[alternative.timeline.length - 1]?.value_paise ?? 0;

    return alternativeFinal < baselineFinal ? alternative.scenario : baseline.scenario;
  }

  private generateSummary(
    differences: ComparisonDifference[],
    bestCase: Scenario | null,
    worstCase: Scenario | null,
  ): string {
    if (differences.length === 0) {
      return 'Scenarios are equivalent';
    }

    const significantDiffs = differences.filter(d => Math.abs(d.percentage_difference) > 5);

    if (significantDiffs.length === 0) {
      return 'Scenarios have minor differences (<5%)';
    }

    const bestName = bestCase?.name ?? 'Unknown';
    const worstName = worstCase?.name ?? 'Unknown';

    return `Best case: ${bestName}, Worst case: ${worstName}. ${significantDiffs.length} significant differences identified.`;
  }

  private generateMultiSummary(results: SimulationResult[]): string {
    if (results.length === 0) {
      return 'No scenarios to compare';
    }

    const values = results.map(r => r.timeline[r.timeline.length - 1]?.value_paise ?? 0);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const range = max - min;

    return `Compared ${results.length} scenarios. Range: ${range} paise difference between best and worst case.`;
  }
}