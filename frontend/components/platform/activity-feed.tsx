/**
 * Activity Feed — M9-C57 Phase 5
 *
 * Displays recent platform events in a scrollable list.
 */

'use client';

import { cn } from '@/lib/utils';

interface EventItem {
  id: string;
  event_type: string;
  emitted_at: string;
  payload?: Record<string, unknown>;
}

interface ActivityFeedProps {
  events: EventItem[];
  limit?: number;
  className?: string;
}

const EVENT_ICONS: Record<string, string> = {
  VerificationCompleted: '✓',
  VerificationFailed: '✗',
  task_created: '+',
  task_cancelled: '−',
  execution_started: '▶',
  execution_completed: '⏹',
  evidence_collected: '⟐',
  default: '•',
};

const EVENT_COLORS: Record<string, string> = {
  VerificationCompleted: 'text-emerald-400',
  VerificationFailed: 'text-red-400',
  task_created: 'text-blue-400',
  execution_started: 'text-amber-400',
  default: 'text-slate-400',
};

function formatRelativeTime(isoString: string): string {
  try {
    const diff = Date.now() - new Date(isoString).getTime();
    const seconds = Math.floor(diff / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  } catch {
    return isoString;
  }
}

export function ActivityFeed({ events, limit = 10, className }: ActivityFeedProps) {
  const display = events.slice(0, limit);

  if (display.length === 0) {
    return (
      <div className={cn('text-sm text-[var(--text-tertiary)] italic p-3', className)}>
        No recent events
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {display.map((event) => {
        const icon = EVENT_ICONS[event.event_type] ?? EVENT_ICONS.default;
        const color = EVENT_COLORS[event.event_type] ?? EVENT_COLORS.default;
        const shortType = event.event_type.replace(/^platform\./, '');

        return (
          <div
            key={event.id}
            className="flex items-center gap-3 px-2 py-1.5 rounded hover:bg-[var(--surface-interactive)] transition-colors"
          >
            <span className={cn('text-sm font-mono w-4 text-center shrink-0', color)}>
              {icon}
            </span>
            <span className="text-xs text-[var(--text-secondary)] truncate flex-1 font-mono">
              {shortType}
            </span>
            <span className="text-xs text-[var(--text-tertiary)] font-mono shrink-0">
              {formatRelativeTime(event.emitted_at)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
