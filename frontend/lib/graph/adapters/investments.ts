/**
 * Investments Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts InvestmentsViewModel into GraphResult.
 * Maps investments, holdings, and asset allocation to graph nodes and edges.
 *
 * Architecture: InvestmentsViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { InvestmentsViewModel } from '@/types/investments-view-model';

const WORKSPACE = 'investments';

/**
 * Adapter for the Investments Intelligence Workspace
 */
export class InvestmentsGraphAdapter extends BaseAdapter<InvestmentsViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: InvestmentsViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    for (const inv of viewModel.investments) {
      // Investment node
      nodes.push({
        id: scopedId(WORKSPACE, inv.id),
        type: 'investment',
        label: inv.name,
        workspace: WORKSPACE,
        value_paise: inv.current_value_paise,
        status: inv.status,
        metadata: {
          investment_type: inv.type,
          institution: inv.institution,
          invested_paise: inv.invested_paise,
          returns_paise: inv.returns_paise,
          returns_percentage: inv.returns_percentage,
          returns_ytd_bps: inv.returns_ytd_bps,
        },
        deep_link: `/investments?id=${inv.id}`,
      });
    }

    // Holding nodes
    for (const holding of viewModel.holdings) {
      nodes.push({
        id: scopedId(WORKSPACE, `holding:${holding.id}`),
        type: 'holding',
        label: holding.name,
        workspace: WORKSPACE,
        value_paise: holding.current_value_paise,
        metadata: {
          investment_type: holding.type,
          symbol: holding.symbol,
          quantity: holding.quantity,
          purchase_price_paise: holding.purchase_price_paise,
          current_price_paise: holding.current_price_paise,
          invested_paise: holding.invested_paise,
          returns_paise: holding.returns_paise,
          returns_percentage: holding.returns_percentage,
        },
        deep_link: `/investments?holding=${holding.id}`,
      });
    }

    return nodes;
  }

  buildEdges(viewModel: InvestmentsViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    // Investment → Holdings
    for (const holding of viewModel.holdings) {
      const holdingNodeId = scopedId(WORKSPACE, `holding:${holding.id}`);
      if (!nodeIds.has(holdingNodeId)) continue;

      // Find parent investment by matching type
      for (const inv of viewModel.investments) {
        if (inv.type === holding.type) {
          const invNodeId = scopedId(WORKSPACE, inv.id);
          if (nodeIds.has(invNodeId)) {
            edges.push({
              id: edgeId(invNodeId, holdingNodeId, 'has_holding'),
              source: invNodeId,
              target: holdingNodeId,
              type: 'has_holding',
              label: `Holds ${holding.name}`,
              weight: 1,
              metadata: {},
            });
          }
        }
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const investmentsGraphAdapter = new InvestmentsGraphAdapter();