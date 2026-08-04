/**
 * Transaction Graph Node Renderer — Architecture Section 7.3 (Graph-node mode)
 *
 * Compact node representation for graph overlay / context panel.
 * Pure presentational — no business logic.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';

// ===== Props =====
type TransactionGraphNodeProps = RendererProps<TransactionViewModel>;

// ===== Transaction Graph Node Renderer =====
export function TransactionGraphNode({ viewModel, density, onAction }: TransactionGraphNodeProps) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const nodeSize = density === 'compact' ? 32 : density === 'spacious' ? 48 : 40;
  const fontSize = density === 'compact' ? 'text-[9px]' : density === 'spacious' ? 'text-[11px]' : 'text-[10px]';
  const hasEvidence = viewModel.evidence && viewModel.evidence.length > 0;
  const lowConfidence = data.confidence !== undefined && data.confidence < 80;

  return (
    <div
      className={cn(
        'relative flex flex-col items-center gap-0.5 cursor-pointer transition-all hover:scale-105',
        lowConfidence && 'opacity-75',
      )}
      style={{ width: nodeSize, height: nodeSize + 24 }}
      onClick={() => onAction({ type: 'select', payload: { id: viewModel.id } })}
      title={data.description}
      role="button"
      tabIndex={0}
      aria-label={`Graph node: ${data.description}`}
    >
      {/* Node circle */}
      <div
        className={cn(
          'rounded-full flex items-center justify-center border-2 transition-colors',
          isExpense
            ? 'bg-[var(--color-negative-100)] border-[var(--color-negative-500)] text-[var(--color-negative-500)]'
            : 'bg-[var(--color-positive-100)] border-[var(--color-positive-500)] text-[var(--color-positive-500)]',
          lowConfidence && 'border-dashed',
        )}
        style={{ width: nodeSize, height: nodeSize }}
      >
        {/* Transaction icon placeholder */}
        <span className={fontSize}>T</span>
      </div>

      {/* Evidence badge */}
      {hasEvidence && (
        <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-[var(--color-info-500)] flex items-center justify-center">
          <span className="text-white text-[7px] font-bold">{viewModel.evidence!.length}</span>
        </div>
      )}

      {/* Label */}
      <span className={cn('text-[var(--text-secondary)] truncate w-full text-center px-0.5', fontSize)}>
        {data.description.length > 12 ? data.description.slice(0, 12) + '…' : data.description}
      </span>
    </div>
  );
}
