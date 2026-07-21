/**
 * Bottom Status Bar - Stage 8E Financial Operating System Shell
 *
 * System status bar (24px height) at the bottom of the viewport.
 * Displays cache health, sync status, and keyboard hints.
 * Uses Surface, CompactToolbar, ToolbarLabel, FinancialIcon, Kbd.
 */

'use client';

import { useMemo } from 'react';
import { performanceRuntime } from '@/lib/performance';
import { Surface } from '@/components/primitives/surface/surface';
import { CompactToolbar, ToolbarLabel } from '@/components/primitives/toolbar-primitive/compact-toolbar';
import { FinancialIcon } from '@/components/primitives/icon-system/financial-icon';
import { Kbd } from '@/components/primitives/kbd/kbd';
import { cn } from '@/lib/utils';

// ===== Bottom Status Bar Component =====
interface BottomStatusBarProps {
  className?: string;
}

export function BottomStatusBar({ className }: BottomStatusBarProps) {
  // Get cache stats from performance runtime
  const cacheStats = useMemo(() => {
    return performanceRuntime.getCacheStats();
  }, []);

  // Calculate cache health percentage
  const cacheHealth = useMemo(() => {
    const total = cacheStats.hits + cacheStats.misses;
    if (total === 0) return 100;
    return Math.round((cacheStats.hits / total) * 100);
  }, [cacheStats]);

  // Get sync status (for future use)
  // const syncState = useMemo(() => {
  //   return performanceRuntime.getSyncState('system');
  // }, []);

  return (
    <footer
      className={cn(
        'fixed bottom-0 left-[180px] right-0 z-30 h-6',
        'border-t border-[var(--border-default)]',
        'bg-[var(--surface-timeline)]',
        className,
      )}
    >
      <Surface variant="timeline" density="none" borderless className="h-full w-full">
        <CompactToolbar size="sm" className="h-full justify-between px-3">
          {/* Left: System Status */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <FinancialIcon name="check-circle" size={12} className="text-[var(--color-success)]" />
              <ToolbarLabel label="System Ready" />
            </div>

            <div className="flex items-center gap-1">
              <FinancialIcon name="database" size={12} className="text-[var(--text-tertiary)]" />
              <ToolbarLabel label={`${cacheStats.size} cached`} />
            </div>

            <div className="flex items-center gap-1">
              <div
                className={cn(
                  'h-2 w-2 rounded-full',
                  cacheHealth > 90 ? 'bg-[var(--color-success)]' :
                  cacheHealth > 70 ? 'bg-[var(--color-warning)]' :
                  'bg-[var(--color-error)]'
                )}
              />
              <ToolbarLabel label={`${cacheHealth}% hit rate`} />
            </div>
          </div>

          {/* Right: Keyboard Hints */}
          <div className="flex items-center gap-3">
            <Kbd keys={['mod', 'k']} />
            <ToolbarLabel label="Command" />

            <Kbd keys={['mod', 'shift', 'f']} />
            <ToolbarLabel label="Search" />

            <Kbd keys={['?']} />
            <ToolbarLabel label="Help" />
          </div>
        </CompactToolbar>
      </Surface>
    </footer>
  );
}