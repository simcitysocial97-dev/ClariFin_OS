/**
 * Transaction Renderable ViewModel Adapter
 *
 * Adapts the existing TransactionViewModel to the RenderableViewModel
 * interface required by the Renderer Registry.
 *
 * This adapter lives in the renderers layer — it is NOT business logic.
 * It only shapes existing ViewModel data into the contract that all
 * 7 renderer modes consume.
 */

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type {
  RenderableViewModel,
  MonetaryValue,
  EvidenceLink,
  EntityReference,
  SelectionState,
} from '../types';

// ===== Transaction Renderable Adapter =====
export function adaptTransaction(viewModel: TransactionViewModel): RenderableViewModel<TransactionViewModel> {
  const isExpense = viewModel.amount.paise < 0 || viewModel.transaction_type === 'debit';
  const amountPaise = Math.abs(viewModel.amount.paise);

  const monetaryValues: MonetaryValue[] = [
    {
      label: 'Amount',
      valuePaise: amountPaise,
      isPositive: !isExpense,
      format: 'currency',
    },
  ];

  if (viewModel.balance) {
    monetaryValues.push({
      label: 'Balance',
      valuePaise: Math.abs(viewModel.balance.paise),
      isPositive: viewModel.balance.paise >= 0,
      format: 'currency',
    });
  }

  const evidence: EvidenceLink[] | undefined = viewModel.evidence?.map((item) => ({
    label: item.summary,
    sourceType: 'transaction',
    sourceId: item.source.api_endpoint ?? item.source.file_id ?? '',
    confidence: item.confidence ?? 0,
  }));

  const relationships: EntityReference[] | undefined = [];
  if (viewModel.category_id) {
    relationships.push({
      entityId: viewModel.category_id,
      entityType: 'category',
      label: viewModel.category_name ?? viewModel.category_path ?? 'Category',
      relationshipType: 'CATEGORIZED_AS',
    });
  }
  if (viewModel.account_id) {
    relationships.push({
      entityId: viewModel.account_id,
      entityType: 'account',
      label: viewModel.account_name ?? viewModel.bank ?? 'Account',
      relationshipType: 'APPEARS_IN',
    });
  }

  const selectionState: SelectionState | undefined = viewModel.selected !== undefined
    ? {
        isSelected: viewModel.selected,
        isHighlighted: false,
        isFocused: false,
      }
    : undefined;

  return {
    id: viewModel.id,
    type: 'transaction',
    label: viewModel.description ?? viewModel.id,
    data: viewModel,
    monetaryValues,
    temporalContext: viewModel.date_formatted
      ? { date: viewModel.date, period: viewModel.month_key }
      : undefined,
    relationships: relationships.length > 0 ? relationships : undefined,
    evidence: evidence && evidence.length > 0 ? evidence : undefined,
    selectionState,
  };
}
