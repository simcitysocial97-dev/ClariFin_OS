/**
 * Goal Engine - Stage 6 Financial Intelligence Engine
 *
 * Deterministic goal tracking engine.
 * Tracks progress toward financial goals and generates insights.
 *
 * Every goal includes evidence, calculation, confidence, source, and related graph nodes.
 */

import type {
  IntelligenceEngine,
  IntelligenceContext,
  EngineResult,
  Goal,
  Insight,
  EvidenceChain,
} from './types';
import { insightBuilder } from './insight-builder';

export class GoalEngine implements IntelligenceEngine {
  readonly name = 'goal' as const;

  compute(context: IntelligenceContext): EngineResult {
    const goals: Goal[] = [];
    const insights: Insight[] = [];
    const nodes = context.nodes;

    // Extract goal nodes from graph
    const goalNodes = nodes.filter(n => n.type === 'goal' || n.type === 'financial_goal');

    for (const node of goalNodes) {
      const goal = this.buildGoalFromNode(node);
      if (goal) {
        goals.push(goal);

        // Generate insights for off-track goals
        if (!goal.on_track && goal.progress_percentage < 50) {
          const evidence = this.buildGoalEvidence(goal, node);
          const insight = insightBuilder.buildInsight(
            `goal-off-track-${goal.id}`,
            'goal',
            'high',
            2,
            evidence.confidence_score,
            'Goal Progress Below Target',
            `Your ${goal.title} is ${goal.progress_percentage.toFixed(0)}% complete. At current velocity, you may not meet the target.`,
            'Progress = current / target, velocity = (target - current) / months remaining',
            'goal',
            evidence,
            ['Increase monthly contribution', 'Extend target date', 'Review goal feasibility'],
            [node.id],
            { valuePaise: goal.current_paise, scoreBps: Math.round(goal.progress_percentage * 100) },
          );
          insights.push(insight);
        }
      }
    }

    return {
      insights,
      alerts: [],
      recommendations: [],
      risk_scores: [],
      opportunity_scores: [],
      goals,
      health_score: null,
    };
  }

  reset(): void {}

  private buildGoalFromNode(node: IntelligenceContext['nodes'][0]): Goal | null {
    const meta = node.metadata;
    const targetPaise = meta.target_paise as number | undefined;
    const currentPaise = meta.current_paise as number | undefined;
    const startDate = meta.start_date as string | undefined;
    const targetDate = meta.target_date as string | undefined;

    if (targetPaise === undefined || currentPaise === undefined) {
      return null;
    }

    // Calculate velocity
    const start = startDate ? new Date(startDate) : new Date();
    const target = targetDate ? new Date(targetDate) : new Date();
    const monthsRemaining = Math.max(1, (target.getFullYear() - start.getFullYear()) * 12 + (target.getMonth() - start.getMonth()));
    const velocityPaisePerMonth = monthsRemaining > 0 ? (targetPaise - currentPaise) / monthsRemaining : 0;
    const requiredVelocity = monthsRemaining > 0 ? (targetPaise - currentPaise) / monthsRemaining : 0;

    const category = (meta.category as string) || 'savings';

    const evidence = this.buildGoalEvidenceFromNode(node);

    return insightBuilder.buildGoal(
      node.id,
      category as 'emergency_fund' | 'savings' | 'debt_repayment' | 'investment' | 'large_purchase' | 'retirement',
      node.label,
      targetPaise,
      currentPaise,
      startDate || new Date().toISOString(),
      targetDate || new Date().toISOString(),
      Math.max(0, velocityPaisePerMonth),
      Math.max(0, requiredVelocity),
      evidence,
      [node.id],
    );
  }

  private buildGoalEvidence(
    goal: Goal,
    node: IntelligenceContext['nodes'][0],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'goal_progress',
        `${goal.title}: ${goal.progress_percentage.toFixed(0)}% complete`,
        'goal-engine',
        80,
      ),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Calculate Goal Progress',
        'Progress = current / target',
        { current_paise: goal.current_paise, target_paise: goal.target_paise },
        { progress_percentage: goal.progress_percentage },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      `Goal analysis: ${goal.title}`,
      evidence,
      calculationSteps,
      [insightBuilder.createSourceReference(node.id, 'graph_node', node.label, node.date || '')],
      75,
    );
  }

  private buildGoalEvidenceFromNode(
    node: IntelligenceContext['nodes'][0],
  ): EvidenceChain {
    const evidence = [
      insightBuilder.createEvidence(
        'goal_data',
        `Goal: ${node.label}`,
        'goal-engine',
        75,
      ),
    ];
    const calculationSteps = [
      insightBuilder.createCalculationStep(
        'Extract Goal Data',
        'Extract goal fields from graph node',
        { node_id: node.id },
        { extracted: true },
      ),
    ];
    return insightBuilder.buildEvidenceChain(
      `Goal: ${node.label}`,
      evidence,
      calculationSteps,
      [insightBuilder.createSourceReference(node.id, 'graph_node', node.label, node.date || '')],
      70,
    );
  }
}