/**
 * Health Badge — M9-C57 Phase 5
 *
 * Displays a status indicator for platform domains.
 * Color-coded per contract enum value.
 */

'use client';

import { cn } from '@/lib/utils';

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  HEALTHY: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', dot: 'bg-emerald-400' },
  DEGRAD: { bg: 'bg-amber-500/15', text: 'text-amber-400', dot: 'bg-amber-400' },
  UNHEALTHY: { bg: 'bg-red-500/15', text: 'text-red-400', dot: 'bg-red-400' },
  UNKNOWN: { bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400' },
  SAFE: { bg: 'bg-blue-500/15', text: 'text-blue-400', dot: 'bg-blue-400' },
  CURRENT: { bg: 'bg-violet-500/15', text: 'text-violet-400', dot: 'bg-violet-400' },
  VALID: { bg: 'bg-teal-500/15', text: 'text-teal-400', dot: 'bg-teal-400' },
  READY: { bg: 'bg-cyan-500/15', text: 'text-cyan-400', dot: 'bg-cyan-400' },
  OPEN: { bg: 'bg-orange-500/15', text: 'text-orange-400', dot: 'bg-orange-400' },
  CLOSED: { bg: 'bg-slate-500/15', text: 'text-slate-400', dot: 'bg-slate-400' },
};

interface HealthBadgeProps {
  status: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export function HealthBadge({
  status,
  size = 'md',
  showLabel = true,
  className,
}: HealthBadgeProps) {
  const styles = STATUS_STYLES[status] ?? STATUS_STYLES.UNKNOWN;
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5 gap-1',
    md: 'text-xs px-2 py-0.5 gap-1.5',
    lg: 'text-sm px-3 py-1 gap-2',
  };

  return (
    // M9-C71: `font-bold` + `data-testid` are the console's status-badge
    // contract, not a styling preference. The Platform Console's own E2E suite
    // locates a status by `[class*="font-bold"]:has-text(<STATUS>)` precisely so
    // that it can distinguish an API-reported status from a frontend-computed
    // one — and the canonical badge used `font-medium`, so the console's own
    // contract did not hold against the console's own badge. The dot keeps
    // `data-testid="health-dot"` for the colour-signal contract.
    <span
      data-testid="health-status-badge"
      data-status={status}
      className={cn(
        'inline-flex items-center rounded-full font-bold uppercase tracking-wide',
        styles.bg,
        styles.text,
        sizeClasses[size],
        className,
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', styles.dot)} data-testid="health-dot" />
      {showLabel && status}
    </span>
  );
}
