/**
 * Right Inspector - Stage 9 Context Panel Experience
 *
 * The Context Panel becomes the operating system's inspector.
 * Displays Accounts → Transactions → Loans → Evidence → Insights → Forecast → Actions → Explanation
 * No navigation — only context driven by SelectionRuntime.
 */

'use client';

import { useState, useMemo } from 'react';
import { selectionRuntime } from '@/lib/runtime/selection-runtime';
import { ContextPanel, useContextPanel } from '@/components/os-shell/context-panel';
import { ScrollRegion } from '@/components/primitives/layout/scroll-region';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { FinancialBadge } from '@/components/primitives/badge-semantic/financial-badge';
import { cn } from '@/lib/utils';
import { ChevronLeft, Minimize2, Maximize2 } from 'lucide-react';

// ===== Right Inspector Component =====
interface RightInspectorProps {
  className?: string;
}

export function RightInspector({ className }: RightInspectorProps) {
  const [width, setWidth] = useState(320);
  const [collapsed, setCollapsed] = useState(false);
  const { hasSelection, entityType } = useContextPanel();

  // Get selection count from runtime
  const selectedCount = useMemo(() => {
    return selectionRuntime.state.multi.size;
  }, []);

  if (collapsed) {
    return (
      <aside
        className={cn(
          'fixed right-0 top-11 bottom-[108px] z-20',
          'w-10 border-l border-[var(--border-default)]',
          'bg-[var(--surface-default)]',
          'flex flex-col items-center pt-2 gap-1',
          className,
        )}
      >
        <button
          onClick={() => setCollapsed(false)}
          className="flex items-center justify-center h-7 w-7 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
          aria-label="Expand inspector"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
        </button>
        {(hasSelection || selectedCount > 0) && (
          <span className="h-1.5 w-1.5 rounded-full bg-[var(--color-selection)]" />
        )}
      </aside>
    );
  }

  return (
    <aside
      className={cn(
        'fixed right-0 top-11 bottom-[108px] z-20',
        'border-l border-[var(--border-default)]',
        'bg-[var(--surface-default)]',
        'flex flex-col',
        className,
      )}
      style={{ width: `${width}px` }}
    >
      {/* Header */}
      <div className="flex items-center justify-between h-10 px-3 border-b border-[var(--border-default)] shrink-0">
        <div className="flex items-center gap-1.5">
          <FinancialIcon name="search" size={13} className="text-[var(--text-tertiary)]" />
          <span className="fin-label font-medium text-[var(--text-primary)]">Context</span>
          {hasSelection && (
            <FinancialBadge semantic="info" variant="ghost" className="text-[9px] px-1 ml-1">
              {entityType}
            </FinancialBadge>
          )}
        </div>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setWidth(w => Math.max(280, w - 20))}
            className="flex items-center justify-center h-6 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Decrease width"
          >
            <Minimize2 className="h-2.5 w-2.5" />
          </button>
          <button
            onClick={() => setWidth(w => Math.min(420, w + 20))}
            className="flex items-center justify-center h-6 w-5 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Increase width"
          >
            <Maximize2 className="h-2.5 w-2.5" />
          </button>
          <button
            onClick={() => setCollapsed(true)}
            className="flex items-center justify-center h-6 w-6 rounded-[var(--radius-sm)] hover:bg-[var(--surface-interactive)] text-[var(--text-tertiary)]"
            aria-label="Collapse inspector"
          >
            <svg className="h-3.5 w-3.5" viewBox="0 0 10 10" fill="none">
              <path d="M2 5H8M5 2L8 5L5 8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content — Context Panel is the sole content of the Right Inspector */}
      <ScrollRegion className="flex-1">
        <ContextPanel />
      </ScrollRegion>

      {/* Footer */}
      <div className="h-7 px-3 border-t border-[var(--border-default)] flex items-center shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="fin-caption text-[var(--text-tertiary)]">
            {hasSelection ? 'Entity context' : 'No selection'}
          </span>
          {hasSelection && (
            <FinancialBadge semantic="info" variant="outline" className="text-[9px] px-1">
              Active
            </FinancialBadge>
          )}
        </div>
      </div>
    </aside>
  );
}