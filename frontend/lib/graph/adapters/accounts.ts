/**
 * Accounts Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts AccountsViewModel into GraphResult.
 * Maps accounts, balance history, and type breakdown to graph nodes and edges.
 *
 * Architecture: AccountsViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { AccountsViewModel } from '@/types/accounts-view-model';

const WORKSPACE = 'accounts';

/**
 * Adapter for the Accounts Intelligence Workspace
 */
export class AccountsGraphAdapter extends BaseAdapter<AccountsViewModel> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: AccountsViewModel): GraphNode[] {
    const nodes: GraphNode[] = [];

    for (const account of viewModel.accounts) {
      // Account node
      nodes.push({
        id: scopedId(WORKSPACE, account.id),
        type: 'account',
        label: account.name,
        workspace: WORKSPACE,
        value_paise: account.balance_paise,
        status: account.status,
        metadata: {
          account_type: account.type,
          institution: account.institution,
          currency: account.currency,
          account_number_last4: account.account_number_last4,
        },
        deep_link: `/accounts?id=${account.id}`,
      });

      // Institution node (deduplicated)
      const institutionId = `institution:${account.institution}`;
      if (!nodes.some(n => n.id === scopedId(WORKSPACE, institutionId))) {
        nodes.push({
          id: scopedId(WORKSPACE, institutionId),
          type: 'institution',
          label: account.institution,
          workspace: WORKSPACE,
          metadata: {},
          deep_link: `/accounts?institution=${encodeURIComponent(account.institution)}`,
        });
      }
    }

    // Balance history nodes
    for (const bh of viewModel.balance_history) {
      nodes.push({
        id: scopedId(WORKSPACE, `balance:${bh.account_id}:${bh.date}`),
        type: 'net_worth_snapshot',
        label: `Balance ${bh.date}`,
        workspace: WORKSPACE,
        value_paise: bh.balance_paise,
        date: bh.date,
        metadata: { account_id: bh.account_id },
        deep_link: `/accounts?id=${bh.account_id}`,
      });
    }

    return nodes;
  }

  buildEdges(viewModel: AccountsViewModel, nodes: GraphNode[]): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    for (const account of viewModel.accounts) {
      const accountNodeId = scopedId(WORKSPACE, account.id);

      // Account → Institution
      const institutionNodeId = scopedId(WORKSPACE, `institution:${account.institution}`);
      if (nodeIds.has(institutionNodeId)) {
        edges.push({
          id: edgeId(accountNodeId, institutionNodeId, 'at_institution'),
          source: accountNodeId,
          target: institutionNodeId,
          type: 'at_institution',
          label: `At ${account.institution}`,
          weight: 1,
          metadata: {},
        });
      }
    }

    // Balance history edges
    for (const bh of viewModel.balance_history) {
      const balanceNodeId = scopedId(WORKSPACE, `balance:${bh.account_id}:${bh.date}`);
      const accountNodeId = scopedId(WORKSPACE, bh.account_id);
      if (nodeIds.has(balanceNodeId) && nodeIds.has(accountNodeId)) {
        edges.push({
          id: edgeId(balanceNodeId, accountNodeId, 'derived_from'),
          source: balanceNodeId,
          target: accountNodeId,
          type: 'derived_from',
          label: `Balance snapshot for ${bh.date}`,
          weight: 1,
          metadata: {},
        });
      }
    }

    return edges;
  }
}

/** Singleton instance */
export const accountsGraphAdapter = new AccountsGraphAdapter();