/**
 * Transaction Table Renderer — Architecture Section 7.3 (Table mode)
 *
 * Dense tabular display for transactions.
 * Pure presentational — no business logic.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps, RendererAction } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';

// ===== Props =====
type TransactionTableProps = RendererProps<TransactionViewModel>;

// ===== Column config per density =====
const COLUMNS: Record<string, readonly string[]> = {
  compact: ['date', 'description', 'category', 'amount'],
  comfortable: ['date', 'description', 'category', 'account', 'amount'],
  spacious: ['date', 'description', 'category', 'account', 'merchant', 'amount'],
};

// ===== Transaction Table Row =====
function TransactionTableRow({
  data,
  isExpense,
  isSelected,
  density,
  onAction,
}: {
  data: TransactionViewModel;
  isExpense: boolean;
  isSelected: boolean;
  density: string;
  onAction: (action: RendererAction) => void;
}) {
  const cols = COLUMNS[density as keyof typeof COLUMNS] ?? COLUMNS.comfortable;
  const showAccount = cols.includes('account');
  const showMerchant = cols.includes('merchant');
  const cellPadding = density === 'compact' ? 'px-2 py-1.5' : 'px-3 py-2';
  const dateFmt = data.date_formatted ?? data.date;

  return (
    <div
      className={cn(
        'flex items-center gap-2 border-b border-[var(--border-subtle)] hover:bg-[var(--surface-interactive)] cursor-pointer transition-colors',
        isSelected && 'bg-[var(--surface-selected)]',
        cellPadding,
      )}
      onClick={() => onAction({ type: 'select', payload: { id: data.id } })}
      role="row"
      aria-selected={isSelected}
    >
      {/* Date */}
      {cols.includes('date') && (
        <div className={cn('w-20 shrink-0 text-[var(--text-secondary)] tabular-nums', density === 'compact' ? 'text-[11px]' : 'fin-caption')}>
          {dateFmt}
        </div>
      )}

      {/* Description + icon */}
      <div className="flex items-center gap-1.5 min-w-0 flex-1">
        <FinancialIcon
          name={data.category_name?.toLowerCase() ?? 'transaction'}
          size={density === 'compact' ? 12 : 14}
          className="text-[var(--text-tertiary)] shrink-0"
        />
        <span className={cn('truncate text-[var(--text-primary)]', density === 'compact' ? 'text-[11px]' : 'fin-body-small')}>
          {data.description}
        </span>
      </div>

      {/* Category */}
      {cols.includes('category') && (
        <div className={cn('w-28 shrink-0 text-[var(--text-secondary)] truncate', density === 'compact' ? 'text-[11px]' : 'fin-caption')}>
          {data.category_path ?? data.category_name ?? '—'}
        </div>
      )}

      {/* Account */}
      {showAccount && (
        <div className={cn('w-24 shrink-0 text-[var(--text-tertiary)] truncate', density === 'compact' ? 'text-[11px]' : 'fin-caption')}>
          {data.account_name ?? data.bank ?? '—'}
        </div>
      )}

      {/* Merchant */}
      {showMerchant && (
        <div className={cn('w-28 shrink-0 text-[var(--text-tertiary)] truncate', density === 'compact' ? 'text-[11px]' : 'fin-caption')}>
          {data.merchant_name ?? '—'}
        </div>
      )}

      {/* Amount */}
      <div className={cn('w-24 text-right shrink-0 tabular-nums font-medium', isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]')}>
        <span className={density === 'compact' ? 'text-[11px]' : 'fin-body-small'}>
          {isExpense ? '-' : '+'}{formatPaise(data.amount.paise)}
        </span>
      </div>
    </div>
  );
}

// ===== Transaction Table Renderer =====
export function TransactionTable({ viewModel, density, onAction }: TransactionTableProps) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const isSelected = viewModel.selectionState?.isSelected ?? false;

  return (
    <div className="w-full">
      {/* Header */}
      <div className={cn(
        'flex items-center gap-2 border-b border-[var(--border-default)] font-semibold text-[var(--text-secondary)] uppercase tracking-wider',
        density === 'compact' ? 'px-2 py-1 text-[10px]' : 'px-3 py-1.5 fin-caption',
      )}>
        {(COLUMNS[density as keyof typeof COLUMNS] ?? COLUMNS.comfortable).map(col => (
          <div key={col} className="capitalize">
            {col}
          </div>
        ))}
      </div>

      {/* Row */}
      <TransactionTableRow
        data={data}
        isExpense={isExpense}
        isSelected={isSelected}
        density={density}
        onAction={onAction}
      />
    </div>
  );
}
