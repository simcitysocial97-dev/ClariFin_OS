/**
 * Transaction Inspector Renderer — Architecture Section 7.3 (Inspector mode)
 *
 * Full-detail view for the Right Context Panel inspector.
 * Pure presentational — no business logic.
 */

'use client';

import type { TransactionViewModel } from '@/types/transaction-view-model';
import type { RendererProps } from '@/lib/renderers/types';
import { cn } from '@/lib/utils';
import { formatPaise } from '@/lib/formatters';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { Surface } from '@/components/primitives/surface/surface';
import { Stack } from '@/components/primitives/layout/stack';
import { ChevronRight, Link as LinkIcon, ShieldCheck } from 'lucide-react';

// ===== Props =====
type TransactionInspectorProps = RendererProps<TransactionViewModel>;

// ===== Section helper =====
function InspectorSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
}) {
  return (
    <Surface variant="raised" density="compact" className="border-0 border-b border-[var(--border-subtle)] last:border-b-0 fin-inspector-section">
      <div className="flex items-center gap-1.5 px-2 py-1 border-b border-[var(--border-subtle)]">
        {icon && <FinancialIcon name={icon} size={10} className="text-[var(--text-tertiary)]" />}
        <span className="fin-caption font-semibold uppercase tracking-wider text-[var(--text-secondary)]">{title}</span>
      </div>
      <div className="px-2 py-1.5 space-y-1">
        {children}
      </div>
    </Surface>
  );
}

// ===== Detail Row =====
function DetailRow({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2 py-0.5">
      <span className="fin-caption text-[var(--text-tertiary)] w-20 shrink-0 pt-0.5">{label}</span>
      <span className={cn('fin-body-small text-[var(--text-primary)] truncate', mono && 'tabular-nums font-mono')}>
        {value}
      </span>
    </div>
  );
}

// ===== Transaction Inspector Renderer =====
export function TransactionInspector({ viewModel, onAction }: TransactionInspectorProps) {
  const data = viewModel.data;
  const isExpense = data.amount.paise < 0 || data.transaction_type === 'debit';
  const hasConfidence = data.confidence !== undefined;
  const confidenceLevel = hasConfidence
    ? (data.confidence ?? 0) >= 90 ? 'high' : (data.confidence ?? 0) >= 70 ? 'medium' : 'low'
    : null;

  return (
    <div className="space-y-0">
      {/* Amount & Status */}
      <InspectorSection title="Overview">
        <div className="flex items-center justify-between">
          <span className={cn('fin-h3 font-bold tabular-nums', isExpense ? 'text-[var(--color-negative-500)]' : 'text-[var(--color-positive-500)]')}>
            {isExpense ? '-' : '+'}{formatPaise(Math.abs(data.amount.paise))}
          </span>
          {data.reconciliation_status && (
            <span className={cn(
              'fin-caption px-1.5 py-0.5 rounded-full',
              data.reconciliation_status === 'confirmed' ? 'bg-[var(--color-positive-100)] text-[var(--color-positive-700)]' :
              data.reconciliation_status === 'rejected' ? 'bg-[var(--color-negative-100)] text-[var(--color-negative-700)]' :
              'bg-[var(--color-warning-100)] text-[var(--color-warning-700)]',
            )}>
              {data.reconciliation_status}
            </span>
          )}
        </div>
      </InspectorSection>

      {/* Details */}
      <InspectorSection title="Details" icon="receipt">
        <Stack gap={1}>
          <DetailRow label="Date" value={data.date_formatted ?? data.date} />
          <DetailRow label="Description" value={data.description} />
          {data.category_name && (
            <DetailRow label="Category" value={data.category_path ?? data.category_name} />
          )}
          {data.account_name && (
            <DetailRow label="Account" value={data.account_name} />
          )}
          {data.merchant_name && (
            <DetailRow label="Merchant" value={data.merchant_name} />
          )}
          {data.reference_number && (
            <DetailRow label="Reference" value={data.reference_number} />
          )}
          {data.balance && (
            <DetailRow label="Balance" value={formatPaise(data.balance.paise)} mono />
          )}
        </Stack>
      </InspectorSection>

      {/* Confidence */}
      {confidenceLevel && (
        <InspectorSection title="Confidence" icon="check-circle">
          <div className="flex items-center gap-2">
            <ShieldCheck className={cn(
              'h-3.5 w-3.5',
              confidenceLevel === 'high' ? 'text-[var(--color-positive-500)]' :
              confidenceLevel === 'medium' ? 'text-[var(--color-warning-500)]' :
              'text-[var(--color-negative-500)]',
            )} />
            <span className="fin-body-small text-[var(--text-primary)]">
              {data.confidence}% automated categorization
            </span>
          </div>
        </InspectorSection>
      )}

      {/* Actions */}
      <InspectorSection title="Actions">
        <div className="space-y-0.5">
          <button
            className="flex items-center gap-2 w-full text-left fin-body-small text-[var(--text-link)] hover:underline py-1"
            onClick={() => onAction({ type: 'navigate', payload: { route: `/transactions?id=${data.id}` } })}
          >
            <LinkIcon className="h-2.5 w-2.5 shrink-0" />
            <span className="truncate">View full details</span>
            <ChevronRight className="h-2.5 w-2.5 ml-auto text-[var(--text-tertiary)]" />
          </button>
          <button
            className="flex items-center gap-2 w-full text-left fin-body-small text-[var(--text-link)] hover:underline py-1"
            onClick={() => onAction({ type: 'drill-down', payload: { id: viewModel.id } })}
          >
            <FinancialIcon name="trending-up" size={10} className="text-[var(--text-tertiary)]" />
            <span className="truncate">Explore relationships</span>
            <ChevronRight className="h-2.5 w-2.5 ml-auto text-[var(--text-tertiary)]" />
          </button>
        </div>
      </InspectorSection>
    </div>
  );
}
