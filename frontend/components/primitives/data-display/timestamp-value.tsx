/**
 * TimestampValue - Stage 8E Data Display Primitive
 *
 * Displays dates and timestamps with monospace formatting.
 * Supports relative, absolute, and compact formats.
 */

import { cn } from '@/lib/utils';

interface TimestampValueProps extends React.HTMLAttributes<HTMLTimeElement> {
  value: string; // ISO date string
  format?: 'date' | 'datetime' | 'compact' | 'relative' | 'month-year';
}

function formatTimestamp(value: string, format: NonNullable<TimestampValueProps['format']>): string {
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;

  switch (format) {
    case 'date':
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    case 'datetime':
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    case 'compact':
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: '2-digit', year: '2-digit' });
    case 'relative': {
      const now = Date.now();
      const diff = now - d.getTime();
      const mins = Math.floor(diff / 60000);
      if (mins < 1) return 'just now';
      if (mins < 60) return `${mins}m ago`;
      const hours = Math.floor(mins / 60);
      if (hours < 24) return `${hours}h ago`;
      const days = Math.floor(hours / 24);
      if (days < 30) return `${days}d ago`;
      return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
    }
    case 'month-year':
      return d.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  }
}

export function TimestampValue({
  value,
  format = 'date',
  className,
  ...props
}: TimestampValueProps) {
  return (
    <time
      dateTime={value}
      className={cn('fin-timestamp', className)}
      {...props}
    >
      {formatTimestamp(value, format)}
    </time>
  );
}