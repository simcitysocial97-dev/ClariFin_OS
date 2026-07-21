/**
 * ConfidenceValue - Stage 8E Data Display Primitive
 *
 * Displays confidence score with color-coded dot indicator.
 * High >= 80 (green), Medium 50-79 (amber), Low < 50 (red).
 */

import { cn } from '@/lib/utils';

interface ConfidenceValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number; // 0-100
  showLabel?: boolean;
  showDot?: boolean;
}

function getConfidenceLabel(value: number): string {
  if (value >= 80) return 'High';
  if (value >= 50) return 'Medium';
  return 'Low';
}

function getConfidenceColor(value: number): string {
  if (value >= 80) return 'bg-[var(--color-confidence-high)]';
  if (value >= 50) return 'bg-[var(--color-confidence-medium)]';
  return 'bg-[var(--color-confidence-low)]';
}

export function ConfidenceValue({
  value,
  showLabel = true,
  showDot = true,
  className,
  ...props
}: ConfidenceValueProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 fin-confidence',
        className
      )}
      {...props}
    >
      {showDot && (
        <span
          className={cn(
            'h-2 w-2 rounded-full',
            getConfidenceColor(value)
          )}
        />
      )}
      <span className="tabular-nums">{value}%</span>
      {showLabel && (
        <span className="fin-caption">{getConfidenceLabel(value)}</span>
      )}
    </span>
  );
}