/**
 * Transaction Timeline Renderer — Architecture Section 7.3 (Timeline mode)
 *
 * Chronological entry for the bottom intelligence shelf timeline.
 * Pure presentational — no business logic.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';

// ===== Transaction Timeline Renderer =====
export function TransactionTimeline({ viewModel, density, onAction }: RendererProps<TransactionViewModel>) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const dotColor = isExpense ? 'bg-[var(--color-negative-500)]' : 'bg-[var(--color-positive-500)]';
  const labelSize = density === 'compact' ? 'text-[11px]' : 'fin-caption';
  const summarySize = density === 'compact' ? 'text-[10px]' : 'fin-body-small';

  return (
    <div
      className={cn(
        'flex items-center gap-2 py-1 px-2 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] cursor-pointer transition-colors',
      )}
      onClick={() => onAction({ type: 'select', payload: { id: viewModel.id } })}
      role="listitem"
      aria-label={`${data.date_formatted ?? data.date}: ${data.description}, ${formatPaise(data.amount.paise)}`}
    >
      {/* Timeline dot */}
      <div className={cn('h-2 w-2 rounded-full shrink-0', dotColor)} />

      {/* Time */}
      <span className={cn('w-16 shrink-0 text-[var(--text-tertiary)] tabular-nums', labelSize)}>
        {data.date_formatted ?? data.date}
      </span>

      {/* Icon */}
      <FinancialIcon
        name={data.category_name?.toLowerCase() ?? 'transaction'}
        size={12}
        className="text-[var(--text-tertiary)] shrink-0"
      />

      {/* Description */}
      <span className={cn('truncate text-[var(--text-primary)] flex-1', summarySize)}>
        {data.description}
      </span>

      {/* Amount */}
      <span className={cn(
        'shrink-0 tabular-nums font-medium',
        isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]',
        labelSize,
      )}>
        {isExpense ? '-' : '+'}{formatPaise(data.amount.paise)}
      </span>
    </div>
  );
}
