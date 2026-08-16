/**
 * Transaction Chart Renderer — Architecture Section 7.3 (Chart mode)
 *
 * Visual data representation for analytics views.
 * Pure presentational — no business logic. Data is consumed from ViewModel.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';

// ===== Props =====
type TransactionChartProps = RendererProps<TransactionViewModel>;

// ===== Transaction Chart Renderer =====
export function TransactionChart({ viewModel, density, onAction }: TransactionChartProps) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const barHeight = Math.min(120, Math.max(8, Math.abs(data.amount.paise) / 10000));
  const medFontSize = density === 'compact' ? 'text-[10px]' : density === 'spacious' ? 'text-[12px]' : 'text-[11px]';
  const labelTruncate = density === 'compact' ? 8 : density === 'spacious' ? 16 : 12;

  return (
    <div
      className={cn(
        'flex flex-col items-center gap-1 px-2 py-1 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] cursor-pointer transition-colors',
      )}
      onClick={() => onAction({ type: 'select', payload: { id: viewModel.id } })}
      role="button"
      tabIndex={0}
      aria-label={`Chart entry: ${data.description}, ${formatPaise(data.amount.paise)}`}
    >
      {/* Bar */}
      <div
        className={cn(
          'w-full rounded-t-sm transition-all',
          isExpense ? 'bg-[var(--color-negative-500)]' : 'bg-[var(--color-positive-500)]',
        )}
        style={{ height: barHeight }}
      />

      {/* Label */}
      <span className={cn('text-[var(--text-secondary)] truncate w-full text-center', medFontSize)}>
        {data.description.length > labelTruncate
          ? data.description.slice(0, labelTruncate) + '…'
          : data.description}
      </span>

      {/* Value */}
      <span className={cn(
        'tabular-nums font-medium',
        isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]',
        medFontSize,
      )}>
        {isExpense ? '-' : '+'}{formatPaise(Math.abs(data.amount.paise))}
      </span>
    </div>
  );
}
