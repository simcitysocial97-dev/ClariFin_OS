/**
 * Global Header - Stage 8A Financial Operating System Shell
 *
 * Application identity bar (48px height).
 * Shows: app name, active workspace, active household, timeline period.
 * All data derived from runtimes — no business logic.
 * Responsive: truncates household → period → workspace on narrow widths.
 */

'use client';

import { useMemo } from 'react';
import { useWorkspace } from '@/lib/workspace/workspace-context';
import { useTimeline } from '@/lib/runtime';
import { cn } from '@/lib/utils';
import { Building2, CalendarDays } from 'lucide-react';

// ===== Global Header Component =====
interface GlobalHeaderProps {
  className?: string;
}

export function GlobalHeader({ className }: GlobalHeaderProps) {
  const { state: workspaceState } = useWorkspace();
  const { state: timelineState } = useTimeline();

  const workspaceLabel = useMemo(() => {
    return workspaceState.currentWorkspace.charAt(0).toUpperCase() + workspaceState.currentWorkspace.slice(1);
  }, [workspaceState.currentWorkspace]);

  const periodLabel = useMemo(() => {
    if (!timelineState.date) return 'All periods';
    return timelineState.date;
  }, [timelineState.date]);

  return (
    <header
      className={cn(
        'fixed top-0 left-[180px] right-0 z-30',
        'h-12 min-h-12',
        'border-b border-[var(--border-default)]',
        'bg-[var(--surface-default)]',
        'flex items-center px-4 gap-3',
        className,
      )}
    >
      {/* App identity */}
      <div className="flex items-center gap-2 shrink-0">
        <span className="fin-h2 text-[var(--text-primary)] font-semibold tracking-tight">
          ClariFin
        </span>
        <span className="h-4 w-px bg-[var(--border-default)] shrink-0" />
      </div>

      {/* Active workspace */}
      <div className="flex items-center gap-1.5 min-w-0">
        <Building2 className="h-3.5 w-3.5 text-[var(--text-tertiary)] shrink-0" />
        <span className="fin-label font-medium text-[var(--text-primary)] truncate">
          {workspaceLabel}
        </span>
      </div>

      {/* Active period */}
      <div className="flex items-center gap-1.5 min-w-0">
        <CalendarDays className="h-3.5 w-3.5 text-[var(--text-tertiary)] shrink-0" />
        <span className="fin-caption text-[var(--text-secondary)] truncate">
          {periodLabel}
        </span>
      </div>

      {/* Spacer — pushes status indicators right */}
      <div className="flex-1" />

      {/* Sync / connection indicators (future: driven by runtimes) */}
      <div className="flex items-center gap-2 shrink-0">
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            'bg-[var(--color-positive-500)]',
          )}
          title="Connected"
        />
        <span className="fin-caption text-[var(--text-tertiary)] hidden md:inline">
          Synced
        </span>
      </div>
    </header>
  );
}
