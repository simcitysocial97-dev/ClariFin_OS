/**
 * PercentageValue - Stage 8E Data Display Primitive
 *
 * Displays percentage values with monospace formatting.
 * Applies financial semantic color based on positive/negative.
 */

import { cn } from '@/lib/utils';

interface PercentageValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number; // e.g. 12.5 = 12.5%
  decimals?: number;
  sign?: 'auto' | 'positive' | 'negative' | 'always' | 'never';
  colored?: boolean;
}

export function PercentageValue({
  value,
  decimals = 1,
  sign = 'auto',
  colored = true,
  className,
  ...props
}: PercentageValueProps) {
  const isZero = value === 0;
  const isNegative = value < 0;
  const abs = Math.abs(value);

  let signChar = '';
  if (sign === 'always' && !isZero) signChar = isNegative ? '-' : '+';
  else if (sign === 'negative' && isNegative) signChar = '-';
  else if (sign === 'positive' && !isNegative && !isZero) signChar = '+';
  else if (sign === 'never') signChar = '';
  else if (sign === 'auto') signChar = isNegative ? '-' : '';

  const colorClass = !colored || isZero
    ? ''
    : isNegative
      ? 'text-[var(--color-negative-600)]'
      : 'text-[var(--color-positive-600)]';

  return (
    <span
      className={cn('fin-percentage', colorClass, className)}
      {...props}
    >
      {signChar}{abs.toFixed(decimals)}%
    </span>
  );
}