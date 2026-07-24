/**
 * Loans Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts LoansViewModel into GraphResult.
 * Maps loans, amortization schedules, and payment progress to graph nodes and edges.
 *
 * Architecture: LoansViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { LoansViewModel } from '@/types/loans-view-model';

const WORKSPACE = 'loans';

/**
 * Adapter for the Loans Intelligence Workspace
 */
export class LoansGraphAdapter extends BaseAdapter<LoansViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: LoansViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    for (const loan of viewModel.loans) {
      // Loan node
      nodes.push({
        id: scopedId(WORKSPACE, loan.id),
        type: 'loan',
        label: loan.name,
        workspace: WORKSPACE,
        value_paise: loan.outstanding_paise,
        status: loan.status,
        metadata: {
          loan_type: loan.type,
          lender: loan.lender,
          original_amount_paise: loan.original_amount_paise,
          interest_rate_bps: loan.interest_rate_bps,
          tenure_months: loan.tenure_months,
          remaining_months: loan.remaining_months,
          emi_paise: loan.emi_paise,
        },
        deep_link: `/loans?id=${loan.id}`,
      });

      // Amortization entry nodes
      for (const entry of viewModel.amortization) {
        if (entry.payment_number <= 12) { // Limit to first 12 for graph size
          nodes.push({
            id: scopedId(WORKSPACE, `amort:${loan.id}:${entry.payment_number}`),
            type: 'amortization_entry',
            label: `Payment #${entry.payment_number}`,
            workspace: WORKSPACE,
            value_paise: entry.emi_paise,
            date: entry.date,
            metadata: {
              loan_id: loan.id,
              principal_paise: entry.principal_paise,
              interest_paise: entry.interest_paise,
              balance_paise: entry.balance_paise,
            },
            deep_link: `/loans?id=${loan.id}&payment=${entry.payment_number}`,
          });
        }
      }
    }

    return nodes;
  }

  buildEdges(viewModel: LoansViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    for (const loan of viewModel.loans) {
      const loanNodeId = scopedId(WORKSPACE, loan.id);

      // Loan → Amortization entries
      for (const entry of viewModel.amortization) {
        if (entry.payment_number > 12) continue;
        const amortNodeId = scopedId(WORKSPACE, `amort:${loan.id}:${entry.payment_number}`);
        if (nodeIds.has(amortNodeId)) {
          edges.push({
            id: edgeId(loanNodeId, amortNodeId, 'amortizes'),
            source: loanNodeId,
            target: amortNodeId,
            type: 'amortizes',
            label: `Payment #${entry.payment_number}`,
            weight: 1,
            metadata: {},
          });
        }
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const loansGraphAdapter = new LoansGraphAdapter();