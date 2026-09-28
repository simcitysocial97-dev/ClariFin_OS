/**
 * Panel - Stage 8E Financial OS Visual Language
 *
 * Reusable panel primitive with Header, Toolbar, Body, Footer, Status slots.
 * Built on top of Surface primitive.
 */

'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Surface } from '@/components/primitives/surface/surface';
import type { SurfaceProps } from '@/components/primitives/surface/surface';

// ===== Panel Variants =====
export const panelVariants = cva('flex flex-col', {
  variants: {
    density: {
      comfortable: '',
      default: '',
      compact: 'text-sm',
      terminal: 'text-xs font-mono',
    },
    fill: {
      true: 'flex-1',
      false: '',
    },
  },
  defaultVariants: {
    density: 'default',
    fill: false,
  },
});

// ===== Panel Component =====
export interface PanelProps
  extends Omit<SurfaceProps, 'density'>,
    VariantProps<typeof panelVariants> {
  fill?: boolean;
}

export function Panel({
  className,
  variant = 'default',
  density = 'default',
  radius = 'md',
  fill = false,
  children,
  ...props
}: PanelProps) {
  return (
    <Surface
      variant={variant}
      radius={radius}
      className={cn(
        panelVariants({ density, fill }),
        className
      )}
      {...props}
    >
      {children}
    </Surface>
  );
}

// ===== Panel Header =====
export interface PanelHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function PanelHeader({
  title,
  subtitle,
  actions,
  children,
  className,
  ...props
}: PanelHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-2 border-b border-[var(--border-default)]',
        className
      )}
      {...props}
    >
      <div className="flex flex-col min-w-0">
        {title && <h3 className="fin-panel-header truncate">{title}</h3>}
        {subtitle && <p className="fin-caption truncate">{subtitle}</p>}
        {children}
      </div>
      {actions && (
        <div className="flex items-center gap-1 ml-2 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}

// ===== Panel Toolbar =====
export interface PanelToolbarProps extends React.HTMLAttributes<HTMLDivElement> {
  divided?: boolean;
}

export function PanelToolbar({
  divided = true,
  children,
  className,
  ...props
}: PanelToolbarProps) {
  return (
    <div
      className={cn(
        'flex items-center gap-1 px-2 py-1',
        divided && 'border-b border-[var(--border-default)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ===== Panel Body =====
export interface PanelBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  scrollable?: boolean;
  loading?: boolean;
  empty?: boolean;
  error?: string | null;
  emptyMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
}

export function PanelBody({
  scrollable = false,
  loading = false,
  empty = false,
  error = null,
  emptyMessage = 'No data',
  errorMessage,
  onRetry,
  children,
  className,
  ...props
}: PanelBodyProps) {
  if (loading) {
    return (
      <div
        className={cn(
          'flex-1 fin-loading',
          scrollable && 'overflow-auto',
          className
        )}
        {...props}
      >
        <div className="fin-loading-pulse p-4 space-y-2">
          <div className="h-3 w-3/4 rounded" />
          <div className="h-3 w-1/2 rounded" />
          <div className="h-3 w-2/3 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className={cn(
          'flex-1 fin-error m-3',
          className
        )}
        {...props}
      >
        <p className="text-sm">{errorMessage || error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-xs underline mt-1 opacity-70 hover:opacity-100"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (empty) {
    return (
      <div
        className={cn(
          'flex-1 fin-empty',
          className
        )}
        {...props}
      >
        <p className="fin-caption">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        'flex-1 min-h-0',
        scrollable && 'overflow-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ===== Panel Footer =====
export interface PanelFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  divided?: boolean;
}

export function PanelFooter({
  divided = true,
  children,
  className,
  ...props
}: PanelFooterProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-1.5',
        divided && 'border-t border-[var(--border-default)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// ===== Panel Status =====
export interface PanelStatusProps extends React.HTMLAttributes<HTMLDivElement> {
  status?: 'success' | 'warning' | 'error' | 'info';
  message: string;
}

export function PanelStatus({
  status = 'info',
  message,
  className,
  ...props
}: PanelStatusProps) {
  const statusClass = {
    success: 'fin-success',
    warning: 'bg-[var(--color-warning-50)] border border-[var(--color-warning-200)] text-[var(--color-warning-700)]',
    error: 'fin-error',
    info: 'bg-[var(--color-info-50)] border border-[var(--color-info-200)] text-[var(--color-info-700)]',
  };

  return (
    <div
      className={cn(
        'px-3 py-1 text-xs',
        statusClass[status],
        className
      )}
      {...props}
    >
      {message}
    </div>
  );
}