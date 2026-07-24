/**
 * Reconciliation Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts ReconciliationViewModel into GraphResult.
 * Maps statements, discrepancies, and audit trail to graph nodes and edges.
 *
 * Architecture: ReconciliationViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { ReconciliationViewModel } from '@/types/reconciliation-view-model';

const WORKSPACE = 'reconciliation';

/**
 * Adapter for the Reconciliation Intelligence Workspace
 */
export class ReconciliationGraphAdapter extends BaseAdapter<ReconciliationViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: ReconciliationViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    for (const stmt of viewModel.statements) {
      // Statement node
      nodes.push({
        id: scopedId(WORKSPACE, `statement:${stmt.statement_id}`),
        type: 'reconciliation_statement',
        label: `Statement: ${stmt.bank} (${stmt.period_from} - ${stmt.period_to})`,
        workspace: WORKSPACE,
        status: stmt.status,
        metadata: {
          bank: stmt.bank,
          period_from: stmt.period_from,
          period_to: stmt.period_to,
          total_debit_paise: stmt.total_debit_paise,
          total_credit_paise: stmt.total_credit_paise,
          transaction_count: stmt.transaction_count,
          reconciled_count: stmt.reconciled_count,
        },
        deep_link: `/reconciliation?statement=${stmt.statement_id}`,
      });
    }

    // Discrepancy nodes
    for (const disc of viewModel.discrepancies) {
      nodes.push({
        id: scopedId(WORKSPACE, `discrepancy:${disc.id}`),
        type: 'discrepancy',
        label: `Discrepancy: ${disc.type}`,
        workspace: WORKSPACE,
        value_paise: disc.difference_paise,
        status: disc.status,
        metadata: {
          transaction_id: disc.transaction_id,
          statement_id: disc.statement_id,
          discrepancy_type: disc.type,
          expected_paise: disc.expected_paise,
          actual_paise: disc.actual_paise,
        },
        deep_link: `/reconciliation?discrepancy=${disc.id}`,
      });
    }

    return nodes;
  }

  buildEdges(viewModel: ReconciliationViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    // Statement → Discrepancies
    for (const disc of viewModel.discrepancies) {
      const discNodeId = scopedId(WORKSPACE, `discrepancy:${disc.id}`);
      const stmtNodeId = scopedId(WORKSPACE, `statement:${disc.statement_id}`);
      if (nodeIds.has(discNodeId) && nodeIds.has(stmtNodeId)) {
        edges.push({
          id: edgeId(stmtNodeId, discNodeId, 'reconciles'),
          source: stmtNodeId,
          target: discNodeId,
          type: 'reconciles',
          label: `Discrepancy: ${disc.type}`,
          weight: 1,
          metadata: {},
        });
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const reconciliationGraphAdapter = new ReconciliationGraphAdapter();