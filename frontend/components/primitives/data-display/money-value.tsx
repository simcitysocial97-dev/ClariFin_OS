/**
 * MoneyValue - Stage 8E Data Display Primitive
 *
 * Displays monetary values in paise with consistent formatting.
 * Monospace, tabular numbers, shortened or full display.
 */

import { cn } from '@/lib/utils';

interface MoneyValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  paise: number;
  variant?: 'default' | 'large' | 'compact';
  sign?: 'auto' | 'positive' | 'negative' | 'always' | 'never';
  currency?: 'INR';
  className?: string;
}

const variantClasses = {
  default: 'fin-amount',
  large: 'fin-amount-large',
  compact: 'fin-amount-compact',
};

function formatINR(paise: number): string {
  const abs = Math.abs(paise);
  const rupees = Math.floor(abs / 100);
  const remaining = abs % 100;
  const formattedRupees = rupees.toLocaleString('en-IN');
  return `₹${formattedRupees}.${remaining.toString().padStart(2, '0')}`;
}

export function MoneyValue({
  paise,
  variant = 'default',
  sign = 'auto',
  className,
  ...props
}: MoneyValueProps) {
  const isZero = paise === 0;
  const isNegative = paise < 0;

  let signChar = '';
  if (sign === 'always' && !isZero) signChar = isNegative ? '-' : '+';
  else if (sign === 'negative' && isNegative) signChar = '-';
  else if (sign === 'positive' && !isNegative && !isZero) signChar = '+';
  else if (sign === 'never') signChar = '';
  else if (sign === 'auto') signChar = isNegative ? '-' : '';

  const colorClass = isZero
    ? ''
    : isNegative
      ? 'text-[var(--color-negative-600)]'
      : sign === 'positive' || sign === 'always'
        ? 'text-[var(--color-positive-600)]'
        : '';

  return (
    <span
      className={cn(
        variantClasses[variant],
        colorClass,
        'tabular-nums',
        className
      )}
      {...props}
    >
      {signChar}{formatINR(Math.abs(paise))}
    </span>
  );
}