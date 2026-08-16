/**
 * Chart - Stage 8E Financial OS Visual Language
 *
 * Chart container primitive with unified loading, error, and empty states.
 * Built on Surface and the design system for consistent visual language.
 * Consumes ViewModel data — no business logic.
 */

'use client';

import { cn } from '@/lib/utils';
import { Surface } from '@/components/primitives/surface/surface';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import type { HTMLAttributes } from 'react';

export type ChartDensity = 'compact' | 'default' | 'comfortable' | 'spacious' | 'terminal';

export interface ChartContainerProps extends HTMLAttributes<HTMLDivElement> {
  isLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
  title?: string;
  density?: ChartDensity;
}

const PADDING_MAP: Record<ChartDensity, string> = {
  compact: 'p-2',
  default: 'p-3',
  comfortable: 'p-4',
  spacious: 'p-6',
  terminal: 'p-1.5',
};

export function ChartContainer({
  isLoading = false,
  isError = false,
  isEmpty = false,
  emptyMessage = 'No data available',
  errorMessage = 'Unable to load chart data',
  onRetry,
  title,
  density = 'default',
  className,
  children,
  ...props
}: ChartContainerProps) {
  const paddingClass = PADDING_MAP[density];

  if (isLoading) {
    return (
      <Surface variant="raised" density={density} className={cn('w-full', paddingClass, className)} {...props}>
        <div className="animate-pulse space-y-2">
          <div className="h-4 w-3/4 bg-[var(--surface-interactive)] rounded" />
          <div className="h-32 w-full bg-[var(--surface-interactive)] rounded" />
        </div>
      </Surface>
    );
  }

  if (isError) {
    return (
      <Surface variant="raised" density={density} className={cn('w-full', paddingClass, 'fin-error', className)} {...props}>
        <p className="fin-caption">{errorMessage}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-1 fin-caption text-[var(--text-link)] underline"
          >
            Retry
          </button>
        )}
      </Surface>
    );
  }

  if (isEmpty) {
    return (
      <Surface variant="raised" density={density} className={cn('w-full', paddingClass, className)} {...props}>
        <div className="flex flex-col items-center justify-center text-center gap-2">
          <FinancialIcon name="search" size={20} className="text-[var(--text-tertiary)] opacity-50" />
          <p className="fin-caption text-[var(--text-tertiary)]">{emptyMessage}</p>
        </div>
      </Surface>
    );
  }

  return (
    <Surface variant="raised" density={density} className={cn('w-full', paddingClass, className)} {...props}>
      {title && (
        <div className="mb-2">
          <p className="fin-section-header text-[var(--text-primary)]">{title}</p>
        </div>
      )}
      {children}
    </Surface>
  );
}
