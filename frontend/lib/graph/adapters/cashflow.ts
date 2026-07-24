/**
 * Cashflow Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts CashflowViewModel into GraphResult.
 * Maps monthly cashflow, categories, and transactions to graph nodes and edges.
 *
 * Architecture: CashflowViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { CashflowViewModel } from '@/types/cashflow-view-model';

const WORKSPACE = 'cashflow';

/**
 * Adapter for the Cashflow Truth Workspace
 */
export class CashflowGraphAdapter extends BaseAdapter<CashflowViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: CashflowViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    // Monthly cashflow nodes
    for (const month of viewModel.monthly) {
      nodes.push({
        id: scopedId(WORKSPACE, `month:${month.month}`),
        type: 'cashflow_month',
        label: `Cashflow ${month.month}`,
        workspace: WORKSPACE,
        value_paise: month.net_paise,
        date: month.month,
        metadata: {
          income_paise: month.income_paise,
          expenses_paise: month.expenses_paise,
          transaction_count: month.transaction_count,
        },
        deep_link: `/cashflow?month=${month.month}`,
      });
    }

    // Category nodes
    for (const cat of viewModel.categories) {
      nodes.push({
        id: scopedId(WORKSPACE, `category:${cat.category_id}`),
        type: 'cashflow_category',
        label: cat.category_name,
        workspace: WORKSPACE,
        value_paise: cat.amount_paise,
        metadata: {
          percentage: cat.percentage,
          transaction_count: cat.transaction_count,
        },
        deep_link: `/cashflow?category=${cat.category_id}`,
      });
    }

    return nodes;
  }

  buildEdges(viewModel: CashflowViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    // Connect monthly nodes sequentially
    const sortedMonths = [...viewModel.monthly].sort((a, b) =>
      a.month.localeCompare(b.month),
    );
    for (let i = 1; i < sortedMonths.length; i++) {
      const prevId = scopedId(WORKSPACE, `month:${sortedMonths[i - 1].month}`);
      const currId = scopedId(WORKSPACE, `month:${sortedMonths[i].month}`);
      if (nodeIds.has(prevId) && nodeIds.has(currId)) {
        edges.push({
          id: edgeId(prevId, currId, 'related_to'),
          source: prevId,
          target: currId,
          type: 'related_to',
          label: 'Month-over-month',
          weight: 1,
          metadata: {},
        });
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const cashflowGraphAdapter = new CashflowGraphAdapter();