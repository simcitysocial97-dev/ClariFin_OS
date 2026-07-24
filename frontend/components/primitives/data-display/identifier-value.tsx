/**
 * IdentifierValue - Stage 8E Data Display Primitive
 *
 * Displays IDs, transaction IDs, account numbers, and other identifiers
 * in monospace with optional copy and truncation.
 */

import { cn } from '@/lib/utils';

interface IdentifierValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: string;
  variant?: 'full' | 'short' | 'truncated';
  prefix?: string;
  copyable?: boolean;
  maxLength?: number;
}

function truncateId(value: string, maxLength: number): string {
  if (value.length <= maxLength) return value;
  const head = value.slice(0, Math.floor(maxLength / 2));
  const tail = value.slice(-Math.floor(maxLength / 3));
  return `${head}...${tail}`;
}

export function IdentifierValue({
  value,
  variant = 'full',
  prefix,
  copyable = false,
  maxLength = 16,
  className,
  ...props
}: IdentifierValueProps) {
  const displayValue = variant === 'truncated'
    ? truncateId(value, maxLength)
    : variant === 'short'
      ? value.slice(0, 8)
      : value;

  const finalValue = prefix ? `${prefix}${displayValue}` : displayValue;

  return (
    <span
      className={cn(
        'fin-identifier',
        copyable && 'cursor-pointer hover:text-[var(--text-link)]',
        className
      )}
      title={copyable ? `Copy: ${value}` : value}
      onClick={copyable ? () => navigator.clipboard.writeText(value) : undefined}
      {...props}
    >
      {finalValue}
    </span>
  );
}