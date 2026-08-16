/**
 * Executive Toast — Stage 8 Financial Operating System
 *
 * Renders warning-tier executive insights as non-blocking toasts.
 * Auto-dismisses after 5 seconds (unless persistent).
 * Maximum 3 visible simultaneously.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.5
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { executiveInsightRuntime } from '@/lib/intelligence/executive-runtime';
import type { ExecutiveInsight } from '@/lib/intelligence/types';
import { AlertCircle, X, CheckCircle2 } from 'lucide-react';

// ─── Toast Styling ───────────────────────────────────────────────────────────

const toastStyles: Record<string, { bg: string; border: string; icon: string }> = {
  warning: {
    bg: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-950)]',
    border: 'border-[var(--color-warning-300)]',
    icon: 'text-[var(--color-warning-500)]',
  },
  critical: {
    bg: 'bg-[var(--color-negative-50)] dark:bg-[var(--color-negative-950)]',
    border: 'border-[var(--color-negative-300)]',
    icon: 'text-[var(--color-negative-500)]',
  },
};

// ─── Single Toast ─────────────────────────────────────────────────────────────

interface ToastProps {
  insight: ExecutiveInsight;
  onDismiss: (id: string) => void;
}

function ToastItem({ insight, onDismiss }: ToastProps) {
  const style = toastStyles[insight.severity];
  const Icon = insight.severity === 'warning' ? AlertCircle : CheckCircle2;

  const handleDismiss = useCallback(() => {
    onDismiss(insight.id);
  }, [insight.id, onDismiss]);

  // Auto-dismiss after 5 seconds for non-critical
  useEffect(() => {
    if (insight.severity === 'warning') {
      const timer = setTimeout(() => {
        onDismiss(insight.id);
      }, 5000);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [insight.id, insight.severity, onDismiss]);

  return (
    <div
      className={cn(
        'flex items-start gap-2 px-3 py-2.5 rounded-[var(--radius-md)]',
        'border shadow-[var(--elevation-3)]',
        style.bg,
        style.border,
        'max-w-xs',
      )}
    >
      <Icon className={cn('h-3.5 w-3.5 shrink-0 mt-0.5', style.icon)} />
      <div className="min-w-0 flex-1">
        <p className="fin-body-small font-medium text-[var(--text-primary)] truncate">
          {insight.title}
        </p>
        <p className="fin-caption text-[var(--text-secondary)] mt-0.5 line-clamp-2">
          {insight.summary}
        </p>
      </div>
      <button
        onClick={handleDismiss}
        className="shrink-0 h-4 w-4 rounded-full flex items-center justify-center hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)] transition-colors"
        aria-label="Dismiss notification"
      >
        <X className="h-2.5 w-2.5" />
      </button>
    </div>
  );
}

// ─── Toast Stack ──────────────────────────────────────────────────────────────

export function ExecutiveToast() {
  const [toasts, setToasts] = useState<ExecutiveInsight[]>(
    () => executiveInsightRuntime.getToastQueue(),
  );

  useEffect(() => {
    const unsubscribe = executiveInsightRuntime.subscribe(() => {
      setToasts(executiveInsightRuntime.getToastQueue());
    });
    return unsubscribe;
  }, []);

  const handleDismiss = useCallback((id: string) => {
    executiveInsightRuntime.dismissToast(id);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-[3000] flex flex-col gap-2 pointer-events-none"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((insight) => (
        <div key={insight.id} className="pointer-events-auto">
          <ToastItem insight={insight} onDismiss={handleDismiss} />
        </div>
      ))}
    </div>
  );
}
