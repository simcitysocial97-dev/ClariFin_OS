/**
 * Behaviour Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts BehaviourViewModel into GraphResult.
 * Maps wellness scores, spending patterns, and debt health to graph nodes and edges.
 *
 * Architecture: BehaviourViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { BehaviourViewModel } from '@/types/behaviour-view-model';

const WORKSPACE = 'behaviour';

/**
 * Adapter for the Behaviour Intelligence Workspace
 */
export class BehaviourGraphAdapter extends BaseAdapter<BehaviourViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: BehaviourViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    // Wellness score node
    nodes.push({
      id: scopedId(WORKSPACE, 'wellness_score'),
      type: 'behaviour_score',
      label: `Wellness Score: ${viewModel.wellness_score.label}`,
      workspace: WORKSPACE,
      confidence: Math.round(viewModel.wellness_score.score / 100), // Convert bps to 0-100
      metadata: {
        score_bps: viewModel.wellness_score.score,
        label: viewModel.wellness_score.label,
        factors: viewModel.wellness_score.factors,
      },
      deep_link: '/behaviour',
    });

    // Spending pattern nodes
    for (const pattern of viewModel.spending_patterns) {
      nodes.push({
        id: scopedId(WORKSPACE, `pattern:${pattern.category}`),
        type: 'spending_pattern',
        label: `Spending: ${pattern.category}`,
        workspace: WORKSPACE,
        value_paise: pattern.amount_paise,
        metadata: {
          percentage: pattern.percentage,
          trend: pattern.trend,
          month_over_month_change: pattern.month_over_month_change,
        },
        deep_link: `/behaviour?category=${encodeURIComponent(pattern.category)}`,
      });
    }

    // Savings rate node
    if (viewModel.savings_rate) {
      nodes.push({
        id: scopedId(WORKSPACE, 'savings_rate'),
        type: 'behaviour_score',
        label: `Savings Rate: ${(viewModel.savings_rate.savings_rate_bps / 100).toFixed(1)}%`,
        workspace: WORKSPACE,
        value_paise: viewModel.savings_rate.savings_paise,
        metadata: {
          savings_rate_bps: viewModel.savings_rate.savings_rate_bps,
          income_paise: viewModel.savings_rate.income_paise,
          period: viewModel.savings_rate.period,
        },
        deep_link: '/behaviour',
      });
    }

    // Debt health node
    if (viewModel.debt_health) {
      nodes.push({
        id: scopedId(WORKSPACE, 'debt_health'),
        type: 'behaviour_score',
        label: `Debt Health: ${(viewModel.debt_health.health_score / 100).toFixed(0)}%`,
        workspace: WORKSPACE,
        value_paise: viewModel.debt_health.total_debt_paise,
        metadata: {
          debt_to_income_bps: viewModel.debt_health.debt_to_income_bps,
          total_income_paise: viewModel.debt_health.total_income_paise,
          health_score: viewModel.debt_health.health_score,
        },
        deep_link: '/behaviour',
      });
    }

    // Wellness radar nodes
    for (const radar of viewModel.wellness_radar) {
      nodes.push({
        id: scopedId(WORKSPACE, `radar:${radar.dimension}`),
        type: 'behaviour_score',
        label: `${radar.dimension}: ${(radar.score / 100).toFixed(0)}%`,
        workspace: WORKSPACE,
        metadata: {
          dimension: radar.dimension,
          score: radar.score,
          max_score: radar.max_score,
        },
        deep_link: '/behaviour',
      });
    }

    return nodes;
  }

  buildEdges(viewModel: BehaviourViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    // Wellness score → Spending patterns
    for (const pattern of viewModel.spending_patterns) {
      const patternNodeId = scopedId(WORKSPACE, `pattern:${pattern.category}`);
      if (nodeIds.has(patternNodeId)) {
        edges.push({
          id: edgeId(scopedId(WORKSPACE, 'wellness_score'), patternNodeId, 'derived_from'),
          source: scopedId(WORKSPACE, 'wellness_score'),
          target: patternNodeId,
          type: 'derived_from',
          label: `Derived from ${pattern.category}`,
          weight: 1,
          metadata: {},
        });
      }
    }

    // Wellness score → Savings rate
    if (viewModel.savings_rate) {
      const savingsNodeId = scopedId(WORKSPACE, 'savings_rate');
      if (nodeIds.has(savingsNodeId)) {
        edges.push({
          id: edgeId(scopedId(WORKSPACE, 'wellness_score'), savingsNodeId, 'derived_from'),
          source: scopedId(WORKSPACE, 'wellness_score'),
          target: savingsNodeId,
          type: 'derived_from',
          label: 'Derived from savings rate',
          weight: 1,
          metadata: {},
        });
      }
    }

    // Wellness score → Debt health
    if (viewModel.debt_health) {
      const debtNodeId = scopedId(WORKSPACE, 'debt_health');
      if (nodeIds.has(debtNodeId)) {
        edges.push({
          id: edgeId(scopedId(WORKSPACE, 'wellness_score'), debtNodeId, 'derived_from'),
          source: scopedId(WORKSPACE, 'wellness_score'),
          target: debtNodeId,
          type: 'derived_from',
          label: 'Derived from debt health',
          weight: 1,
          metadata: {},
        });
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const behaviourGraphAdapter = new BehaviourGraphAdapter();