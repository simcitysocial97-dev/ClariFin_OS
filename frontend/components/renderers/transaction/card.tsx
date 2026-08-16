/**
 * Transaction Card Renderer — Architecture Section 7.3 (Card mode)
 *
 * Pure presentational component. Consumes RenderableViewModel<TransactionViewModel>.
 * No business logic. No API calls. No local domain state.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';

// ===== Transaction Card Renderer =====
export function TransactionCard({ viewModel, density, onAction }: RendererProps<TransactionViewModel>) {
  const data = viewModel.data;
  const isSelected = viewModel.selectionState?.isSelected ?? false;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const isAdjusted = data.is_adjusted ?? false;

  // Density-based sizing
  const heightClass = density === 'compact' ? 'py-2 px-3' : density === 'spacious' ? 'py-4 px-4' : 'py-3 px-4';
  const iconSize = density === 'compact' ? 14 : density === 'spacious' ? 20 : 16;
  const textSize = density === 'compact' ? 'fin-caption' : density === 'spacious' ? 'fin-label' : 'fin-body-small';
  const amountSize = density === 'compact' ? 'text-[11px]' : density === 'spacious' ? 'text-[15px]' : 'text-[13px]';

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-[var(--radius-md)] border transition-colors cursor-pointer',
        heightClass,
        isSelected
          ? 'border-[var(--color-selection)] bg-[var(--surface-selected)]'
          : 'border-[var(--border-subtle)] bg-[var(--surface-default)] hover:bg-[var(--surface-interactive)]',
        isAdjusted && 'opacity-60',
      )}
      onClick={() => onAction({ type: 'select', payload: { id: viewModel.id } })}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onAction({ type: 'select', payload: { id: viewModel.id } }); }}
      role="button"
      tabIndex={0}
      aria-label={`Transaction: ${data.description}, ${formatPaise(data.amount.paise)}`}
    >
      {/* Category icon */}
      <div className={cn(
        'h-8 w-8 rounded-full flex items-center justify-center shrink-0',
        isExpense ? 'bg-[var(--color-negative-100)] text-[var(--color-negative-500)]' : 'bg-[var(--color-positive-100)] text-[var(--color-positive-500)]',
      )}>
        <FinancialIcon
          name={data.category_name?.toLowerCase() ?? 'transaction'}
          size={iconSize}
        />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className={cn('font-medium truncate', textSize, 'text-[var(--text-primary)]')}>
          {data.description}
        </div>
        <div className={cn('text-[var(--text-tertiary)] truncate', density === 'compact' ? 'text-[10px]' : 'fin-caption')}>
          {data.category_path ?? data.category_name ?? 'Uncategorized'}
          {data.date_formatted && ` · ${data.date_formatted}`}
        </div>
      </div>

      {/* Amount */}
      <div className="text-right shrink-0">
        <div className={cn('font-semibold tabular-nums', amountSize, isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]')}>
          {isExpense ? '-' : '+'}{formatPaise(data.amount.paise)}
        </div>
        {data.balance && (
          <div className={cn('text-[var(--text-tertiary)] tabular-nums', density === 'compact' ? 'text-[10px]' : 'fin-caption')}>
            {formatPaise(data.balance.paise)}
          </div>
        )}
      </div>
    </div>
  );
}
