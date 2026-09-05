/**
 * Metric Tile — M9-C57 Phase 5
 *
 * A compact card displaying a single metric with label, value, and optional
 * subtitle. Used throughout the dashboard for dimension statuses, counts, etc.
 */

'use client';

import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface MetricTileProps {
  label: string;
  value: string | ReactNode;
  subtitle?: string;
  accent?: 'default' | 'positive' | 'negative' | 'warning';
  className?: string;
}

const ACCENT_CLASSES: Record<string, string> = {
  default: 'border-[var(--border-subtle)]',
  positive: 'border-emerald-500/30',
  negative: 'border-red-500/30',
  warning: 'border-amber-500/30',
};

export function MetricTile({
  label,
  value,
  subtitle,
  accent = 'default',
  className,
}: MetricTileProps) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-[var(--surface-raised)] p-4 flex flex-col gap-1',
        ACCENT_CLASSES[accent],
        className,
      )}
    >
      <span className="text-xs text-[var(--text-tertiary)] uppercase tracking-wider font-medium">
        {label}
      </span>
      <span className="text-xl font-semibold text-[var(--text-primary)] leading-tight">
        {value}
      </span>
      {subtitle && (
        <span className="text-xs text-[var(--text-secondary)]">{subtitle}</span>
      )}
    </div>
  );
}
