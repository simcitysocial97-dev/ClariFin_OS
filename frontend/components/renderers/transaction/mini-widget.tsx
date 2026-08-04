/**
 * Transaction Mini Widget Renderer — Architecture Section 7.3 (Mini-widget mode)
 *
 * Compact summary for dashboard cards and status bars.
 * Pure presentational — no business logic.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';

// ===== Props =====
type TransactionMiniWidgetProps = RendererProps<TransactionViewModel>;

// ===== Transaction Mini Widget Renderer =====
export function TransactionMiniWidget({ viewModel, density, onAction }: TransactionMiniWidgetProps) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const compact = density === 'compact';
  const medFontSize = compact ? 'text-[11px]' : 'fin-caption';
  const lgFontSize = compact ? 'text-[13px]' : 'fin-label';

  return (
    <div
      className={cn(
        'flex items-center gap-2 px-2 py-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] cursor-pointer transition-colors',
      )}
      onClick={() => onAction({ type: 'select', payload: { id: viewModel.id } })}
      role="button"
      tabIndex={0}
      aria-label={`Transaction widget: ${data.description}, ${formatPaise(data.amount.paise)}`}
    >
      {/* Dot indicator */}
      <div className={cn(
        'h-2 w-2 rounded-full shrink-0',
        isExpense ? 'bg-[var(--color-negative-500)]' : 'bg-[var(--color-positive-500)]',
      )} />

      {/* Label */}
      <span className={cn('truncate flex-1 text-[var(--text-primary)]', medFontSize)}>
        {data.description.length > 20 ? data.description.slice(0, 20) + '…' : data.description}
      </span>

      {/* Amount */}
      <span className={cn(
        'shrink-0 tabular-nums font-medium',
        isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]',
        lgFontSize,
      )}>
        {isExpense ? '-' : '+'}{formatPaise(Math.abs(data.amount.paise))}
      </span>
    </div>
  );
}
