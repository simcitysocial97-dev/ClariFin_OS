/**
 * Goal Simulator - Stage 7 Simulation & Forecast Engine
 *
 * Deterministic goal achievement prediction engine.
 * Projects goal progress based on current velocity and target.
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

// ===== Goal Simulator =====
/**
 * Projects goal achievement based on current progress and velocity.
 */
export class GoalSimulator implements SimulationEngine {
  readonly name = 'goal' as const;

  compute(context: SimulationContext, options?: SimulationOptions): SimulationResult {
    const horizonMonths = options?.horizon_months ?? context.config.horizon_months;
    const baseDate = this.getBaseDate(context.nodes);
    const relatedNodes = this.getGoalNodeIds(context.nodes);

    // Extract goal data
    const goalData = this.extractGoalData(context.nodes);

    // Generate projections
    const projections = this.generateProjections(
      goalData,
      baseDate,
      horizonMonths,
      relatedNodes,
    );

    // Build scenario
    const scenario = simulationBuilder.createScenario(
      'goal-baseline',
      'Baseline Goal Progress Projection',
      'Projects goal achievement based on current velocity',
      10000, // 100% probability (deterministic)
      projections,
      this.getDefaultAssumptions(goalData),
      this.buildEvidenceChain(goalData, projections, context.nodes),
    );

    // Build outputs
    const outputs: SimulationOutput[] = [
      simulationBuilder.createOutput(
        'current_progress',
        'Current goal progress percentage',
        { value: goalData.progressPercentage },
      ),
      simulationBuilder.createOutput(
        'projected_progress',
        'Final projected progress percentage',
        { value: projections.length > 0 ? this.calculateProgressPercentage(goalData, projections[projections.length - 1].value_paise) : goalData.progressPercentage },
      ),
      simulationBuilder.createOutput(
        'on_track',
        'Whether goal is on track to achieve target',
        { value: goalData.onTrack },
      ),
    ];

    return simulationBuilder.createSimulationResult(
      'goal',
      scenario,
      projections,
      outputs,
      this.buildEvidenceChain(goalData, projections, context.nodes),
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

  private getGoalNodeIds(nodes: SimulationContext['nodes']): string[] {
    return nodes
      .filter(n => n.type === 'goal' || n.type === 'net_worth_snapshot')
      .map(n => n.id);
  }

  private extractGoalData(nodes: SimulationContext['nodes']): {
    targetPaise: number;
    currentPaise: number;
    velocityPaisePerMonth: number;
    progressPercentage: number;
    onTrack: boolean;
  } {
    let targetPaise = 0;
    let currentPaise = 0;
    let velocityPaisePerMonth = 0;
    let progressPercentage = 0;
    let onTrack = false;

    for (const node of nodes) {
      if (node.type === 'goal') {
        targetPaise = (node.metadata?.target_paise as number) ?? 0;
        currentPaise = (node.metadata?.current_paise as number) ?? 0;
        velocityPaisePerMonth = (node.metadata?.velocity_paise_per_month as number) ?? 0;
        progressPercentage = targetPaise > 0 ? (currentPaise / targetPaise) * 100 : 0;
        onTrack = (node.metadata?.on_track as boolean) ?? false;
      }
    }

    return {
      targetPaise,
      currentPaise,
      velocityPaisePerMonth,
      progressPercentage,
      onTrack,
    };
  }

  private generateProjections(
    goalData: {
      targetPaise: number;
      currentPaise: number;
      velocityPaisePerMonth: number;
      progressPercentage: number;
      onTrack: boolean;
    },
    baseDate: string,
    horizonMonths: number,
    relatedNodes: string[],
  ): SimulationResult['timeline'] {
    const projections: SimulationResult['timeline'] = [];

    let value = goalData.currentPaise;
    const target = goalData.targetPaise;

    for (let i = 0; i <= horizonMonths; i++) {
      const date = simulationBuilder.generateDateFromOffset(baseDate, i);

      // Add velocity each month
      if (i > 0) {
        value = Math.min(target, value + goalData.velocityPaisePerMonth);
      }

      const projection = simulationBuilder.createProjection(
        `goal-proj-${i}`,
        'goal_progress',
        date,
        value,
        75, // 75% confidence
        relatedNodes,
      );
      projections.push(projection);
    }

    return projections;
  }

  private calculateProgressPercentage(
    goalData: { targetPaise: number; currentPaise: number },
    projectedValue: number,
  ): number {
    return goalData.targetPaise > 0 ? Math.min(100, (projectedValue / goalData.targetPaise) * 100) : 0;
  }

  private getDefaultAssumptions(goalData: {
    targetPaise: number;
    currentPaise: number;
    velocityPaisePerMonth: number;
  }): SimulationResult['scenario']['assumptions'] {
    return [
      simulationBuilder.createAssumption(
        'assumption-velocity',
        'Monthly progress velocity remains consistent',
        'behavioral',
        goalData.velocityPaisePerMonth,
        80,
      ),
      simulationBuilder.createAssumption(
        'assumption-target',
        `Target remains ${goalData.targetPaise} paise`,
        'behavioral',
        goalData.targetPaise,
        95,
      ),
    ];
  }

  private buildEvidenceChain(
    goalData: {
      targetPaise: number;
      currentPaise: number;
      velocityPaisePerMonth: number;
      progressPercentage: number;
      onTrack: boolean;
    },
    projections: SimulationResult['timeline'],
    nodes: SimulationContext['nodes'],
  ): SimulationEvidenceChain {
    const evidence = [
      simulationBuilder.createEvidence(
        'goal_data',
        `Goal: ${goalData.currentPaise} / ${goalData.targetPaise} paise (${goalData.progressPercentage.toFixed(1)}%)`,
        'goal-simulator',
        85,
      ),
    ];

    const calculationSteps = [
      simulationBuilder.createCalculationStep(
        'Extract Goal Data',
        'Get target, current value, and velocity from goal nodes',
        { node_count: nodes.length },
        {
          target_paise: goalData.targetPaise,
          current_paise: goalData.currentPaise,
          velocity_paise_per_month: goalData.velocityPaisePerMonth,
        },
      ),
      simulationBuilder.createCalculationStep(
        'Project Goal Progress',
        `Calculate progress for ${projections.length} months`,
        { monthly_velocity: goalData.velocityPaisePerMonth },
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
      `Goal projection: ${goalData.currentPaise} paise progressing to ${projections[projections.length - 1]?.value_paise ?? 0} paise`,
      evidence,
      calculationSteps,
      sourceReferences,
      75,
    );
  }
}