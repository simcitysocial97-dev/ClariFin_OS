/**
 * Executive Modal — Stage 8 Financial Operating System
 *
 * Renders critical executive insights as modals that require user action.
 * Maximum 1 active at a time. Blocks interaction until resolved.
 *
 * Architecture: FINANCIAL_OS_SHELL_ARCHITECTURE.md §4.5
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { cn } from '@/lib/utils';
import { executiveInsightRuntime } from '@/lib/intelligence/executive-runtime';
import type { ExecutiveInsight } from '@/lib/intelligence/types';
import { AlertTriangle } from 'lucide-react';

// ─── Severity Styling ────────────────────────────────────────────────────────

const severityStyles: Record<string, { bg: string; border: string; icon: string; text: string }> = {
  critical: {
    bg: 'bg-[var(--color-negative-50)] dark:bg-[var(--color-negative-950)]',
    border: 'border-[var(--color-negative-400)]',
    icon: 'text-[var(--color-negative-500)]',
    text: 'text-[var(--color-negative-600)]',
  },
  warning: {
    bg: 'bg-[var(--color-warning-50)] dark:bg-[var(--color-warning-950)]',
    border: 'border-[var(--color-warning-400)]',
    icon: 'text-[var(--color-warning-500)]',
    text: 'text-[var(--color-warning-600)]',
  },
};

// ─── Modal Component ─────────────────────────────────────────────────────────

interface ExecutiveModalProps {
  insight: ExecutiveInsight;
}

function ExecutiveModalContent({ insight }: ExecutiveModalProps) {
  const style = severityStyles[insight.severity];
  const Icon = insight.severity === 'critical' ? AlertTriangle : AlertTriangle;

  const handleAction = useCallback(() => {
    executiveInsightRuntime.executeAction(insight.id);
  }, [insight.id]);

  const handleCancel = useCallback(() => {
    executiveInsightRuntime.executeCancel(insight.id);
  }, [insight.id]);

  return (
    <div className={cn('fixed inset-0 z-[3000] flex items-center justify-center p-4', style.bg)}>
      {/* Backdrop — blocks all interaction */}
      <div className="absolute inset-0 bg-[var(--surface-overlay)] opacity-50" />

      {/* Modal */}
      <div className={cn(
        'relative max-w-[480px] w-full',
        'bg-[var(--surface-default)]',
        'border',
        style.border,
        'rounded-[var(--radius-lg)]',
        'shadow-[var(--elevation-5)]',
        'flex flex-col',
      )}>
        {/* Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border-default)]">
          <Icon className={cn('h-4 w-4 shrink-0', style.icon)} />
          <h2 className="fin-h3 font-semibold text-[var(--text-primary)]">
            {insight.title}
          </h2>
        </div>

        {/* Body */}
        <div className="px-4 py-3 space-y-2">
          <p className="fin-body text-[var(--text-secondary)]">{insight.summary}</p>

          {/* Audit trail metadata */}
          <div className="fin-caption text-[var(--text-tertiary)] space-y-0.5">
            <div className="flex items-center gap-1.5">
              <span>Detected:</span>
              <span>{new Date(insight.auditTrail.detectedAt).toLocaleString()}</span>
            </div>
            {insight.auditTrail.threshold !== undefined && (
              <div className="flex items-center gap-1.5">
                <span>Threshold:</span>
                <span className="font-mono tabular-nums">
                  ₹{(insight.auditTrail.threshold / 100).toFixed(2)}
                </span>
              </div>
            )}
            {insight.auditTrail.actualValue !== undefined && (
              <div className="flex items-center gap-1.5">
                <span>Actual:</span>
                <span className={cn('font-mono tabular-nums', style.text)}>
                  ₹{(insight.auditTrail.actualValue / 100).toFixed(2)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Footer — always required for critical, optional for warning */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-[var(--border-default)]">
          {insight.requiresAction && (
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 rounded-[var(--radius-sm)] text-[var(--text-secondary)] hover:bg-[var(--surface-interactive)] fin-body-small transition-colors"
            >
              {insight.cancelLabel}
            </button>
          )}
          <button
            onClick={handleAction}
            className={cn(
              'px-3 py-1.5 rounded-[var(--radius-sm)] text-white fin-body-small transition-opacity hover:opacity-90',
              insight.severity === 'critical'
                ? 'bg-[var(--color-negative-500)]'
                : 'bg-[var(--color-warning-500)]',
            )}
          >
            {insight.actionLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Panel Component ─────────────────────────────────────────────────────────

export function ExecutiveModal() {
  const [insight, setInsight] = useState<ExecutiveInsight | null>(null);

  useEffect(() => {
    setInsight(executiveInsightRuntime.getActiveInsight());
    const unsubscribe = executiveInsightRuntime.subscribe(() => {
      setInsight(executiveInsightRuntime.getActiveInsight());
    });
    return unsubscribe;
  }, []);

  if (!insight) return null;

  return <ExecutiveModalContent insight={insight} />;
}
