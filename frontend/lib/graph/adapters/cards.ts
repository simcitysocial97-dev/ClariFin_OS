/**
 * Credit Cards Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts CreditCardsViewModel into GraphResult.
 * Maps credit cards, statements, and utilization to graph nodes and edges.
 *
 * Architecture: CreditCardsViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { CreditCardsViewModel } from '@/types/credit-cards-view-model';

const WORKSPACE = 'cards';

/**
 * Adapter for the Credit Cards Intelligence Workspace
 */
export class CardsGraphAdapter extends BaseAdapter<CreditCardsViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: CreditCardsViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    for (const card of viewModel.cards) {
      // Credit card node
      nodes.push({
        id: scopedId(WORKSPACE, card.id),
        type: 'credit_card',
        label: card.name,
        workspace: WORKSPACE,
        value_paise: card.current_balance_paise,
        status: card.status,
        metadata: {
          bank: card.bank,
          card_number_last4: card.card_number_last4,
          credit_limit_paise: card.credit_limit_paise,
          available_paise: card.available_paise,
          min_due_paise: card.min_due_paise,
          total_due_paise: card.total_due_paise,
          due_date: card.due_date,
          reward_points: card.reward_points,
        },
        deep_link: `/cards?id=${card.id}`,
      });

      // Statement nodes
      for (const stmt of viewModel.statements) {
        if (stmt.card_id === card.id) {
          nodes.push({
            id: scopedId(WORKSPACE, `statement:${stmt.id}`),
            type: 'credit_card_statement',
            label: `Statement ${stmt.period_from} to ${stmt.period_to}`,
            workspace: WORKSPACE,
            value_paise: stmt.total_due_paise,
            date: stmt.period_to,
            status: stmt.status,
            metadata: {
              card_id: stmt.card_id,
              min_due_paise: stmt.min_due_paise,
              total_payment_paise: stmt.total_payment_paise,
              payment_date: stmt.payment_date,
            },
            deep_link: `/cards?id=${card.id}&statement=${stmt.id}`,
          });
        }
      }
    }

    return nodes;
  }

  buildEdges(viewModel: CreditCardsViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    for (const card of viewModel.cards) {
      const cardNodeId = scopedId(WORKSPACE, card.id);

      // Card → Statements
      for (const stmt of viewModel.statements) {
        if (stmt.card_id === card.id) {
          const stmtNodeId = scopedId(WORKSPACE, `statement:${stmt.id}`);
          if (nodeIds.has(stmtNodeId)) {
            edges.push({
              id: edgeId(cardNodeId, stmtNodeId, 'has_statement'),
              source: cardNodeId,
              target: stmtNodeId,
              type: 'has_statement',
              label: `Statement ${stmt.period_from}`,
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
export const cardsGraphAdapter = new CardsGraphAdapter();