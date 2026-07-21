/**
 * DeltaValue - Stage 8E Data Display Primitive
 *
 * Displays change/delta values with arrow indicators.
 * Green for positive, red for negative.
 */

import { cn } from '@/lib/utils';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface DeltaValueProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: number;
  variant?: 'money' | 'percentage' | 'number';
  showArrow?: boolean;
  colored?: boolean;
}

export function DeltaValue({
  value,
  variant = 'money',
  showArrow = true,
  colored = true,
  className,
  ...props
}: DeltaValueProps) {
  const isZero = value === 0;
  const isPositive = value > 0;

  const colorClass = !colored || isZero
    ? 'text-[var(--text-tertiary)]'
    : isPositive
      ? 'text-[var(--color-positive-600)]'
      : 'text-[var(--color-negative-600)]';

  const displayValue = variant === 'percentage'
    ? `${isPositive ? '+' : ''}${value.toFixed(1)}%`
    : variant === 'money'
      ? `${isPositive ? '+' : ''}₹${Math.abs(value).toLocaleString('en-IN')}`
      : `${isPositive ? '+' : ''}${value}`;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-0.5 fin-amount-compact',
        colorClass,
        className
      )}
      {...props}
    >
      {showArrow && (
        isZero
          ? <Minus className="h-3 w-3" />
          : isPositive
            ? <ArrowUp className="h-3 w-3" />
            : <ArrowDown className="h-3 w-3" />
      )}
      {displayValue}
    </span>
  );
}