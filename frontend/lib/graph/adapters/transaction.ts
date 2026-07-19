/**
 * Transaction Graph Adapter - Stage 4B Financial Graph Runtime
 *
 * Converts TransactionViewModel into GraphResult.
 * Maps transactions, categories, merchants, and accounts to graph nodes and edges.
 *
 * Architecture: TransactionViewModel → Adapter → GraphResult
 */

import { BaseAdapter, scopedId, edgeId } from '../adapter';
import type { GraphNode, GraphEdge } from '../types';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const WORKSPACE = 'transactions';

/**
 * Adapter for the Transaction Intelligence Workspace
 */
export class TransactionGraphAdapter extends BaseAdapter<{
  transactions: TransactionViewModel[];
}> {
  readonly name = WORKSPACE;

  buildNodes(viewModel: { transactions: TransactionViewModel[] }): GraphNode[] {
    const nodes: GraphNode[] = [];
    const categoryIds = new Set<string>();
    const merchantIds = new Set<string>();
    const accountIds = new Set<string>();

    for (const tx of viewModel.transactions) {
      // Transaction node
      nodes.push({
        id: scopedId(WORKSPACE, tx.id),
        type: 'transaction',
        label: tx.description,
        workspace: WORKSPACE,
        value_paise: tx.amount.paise,
        date: tx.date,
        status: tx.transaction_type,
        confidence: tx.confidence,
        metadata: {
          category: tx.category_name,
          merchant: tx.merchant_name,
          account: tx.account_name,
          bank: tx.bank,
          reference: tx.reference_number,
          is_adjusted: tx.is_adjusted,
          reconciliation_status: tx.reconciliation_status,
        },
        deep_link: `/transactions?id=${tx.id}`,
      });

      // Category node (deduplicated)
      if (tx.category_id && !categoryIds.has(tx.category_id)) {
        categoryIds.add(tx.category_id);
        nodes.push({
          id: scopedId(WORKSPACE, `category:${tx.category_id}`),
          type: 'category',
          label: tx.category_name ?? tx.category_id,
          workspace: WORKSPACE,
          metadata: {
            category_path: tx.category_path,
            subcategory: tx.subcategory,
          },
          deep_link: `/transactions?category=${tx.category_id}`,
        });
      }

      // Merchant node (deduplicated)
      if (tx.merchant_id && !merchantIds.has(tx.merchant_id)) {
        merchantIds.add(tx.merchant_id);
        nodes.push({
          id: scopedId(WORKSPACE, `merchant:${tx.merchant_id}`),
          type: 'merchant',
          label: tx.merchant_name ?? tx.merchant_id,
          workspace: WORKSPACE,
          metadata: {
            merchant_category: tx.merchant_category,
          },
          deep_link: `/transactions?merchant=${tx.merchant_id}`,
        });
      }

      // Account node (deduplicated)
      if (tx.account_id && !accountIds.has(tx.account_id)) {
        accountIds.add(tx.account_id);
        nodes.push({
          id: scopedId(WORKSPACE, `account:${tx.account_id}`),
          type: 'account',
          label: tx.account_name ?? tx.account_id,
          workspace: WORKSPACE,
          metadata: { bank: tx.bank },
          deep_link: `/accounts?id=${tx.account_id}`,
        });
      }
    }

    return nodes;
  }

  buildEdges(
    viewModel: { transactions: TransactionViewModel[] },
    nodes: GraphNode[],
  ): GraphEdge[] {
    const edges: GraphEdge[] = [];
    const nodeIds = new Set(nodes.map(n => n.id));

    for (const tx of viewModel.transactions) {
      const txId = scopedId(WORKSPACE, tx.id);

      // Transaction → Account
      if (tx.account_id) {
        const accountNodeId = scopedId(WORKSPACE, `account:${tx.account_id}`);
        if (nodeIds.has(accountNodeId)) {
          edges.push({
            id: edgeId(txId, accountNodeId, 'belongs_to'),
            source: txId,
            target: accountNodeId,
            type: 'belongs_to',
            label: `Belongs to ${tx.account_name ?? tx.account_id}`,
            weight: 1,
            metadata: {},
          });
        }
      }

      // Transaction → Category
      if (tx.category_id) {
        const categoryNodeId = scopedId(WORKSPACE, `category:${tx.category_id}`);
        if (nodeIds.has(categoryNodeId)) {
          edges.push({
            id: edgeId(txId, categoryNodeId, 'categorized_as'),
            source: txId,
            target: categoryNodeId,
            type: 'categorized_as',
            label: `Categorized as ${tx.category_name ?? tx.category_id}`,
            weight: 1,
            metadata: {},
          });
        }
      }

      // Transaction → Merchant
      if (tx.merchant_id) {
        const merchantNodeId = scopedId(WORKSPACE, `merchant:${tx.merchant_id}`);
        if (nodeIds.has(merchantNodeId)) {
          edges.push({
            id: edgeId(txId, merchantNodeId, 'from_merchant'),
            source: txId,
            target: merchantNodeId,
            type: 'from_merchant',
            label: `From ${tx.merchant_name ?? tx.merchant_id}`,
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
export const transactionGraphAdapter = new TransactionGraphAdapter();