/**
 * FinancialBadge - Stage 8E Financial OS Visual Language
 *
 * Semantic badges for financial data.
 * Extends shadcn Badge with financial variants.
 */

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

export const financialBadgeVariants = cva('', {
  variants: {
    semantic: {
      positive: 'bg-[var(--color-positive-100)] text-[var(--color-positive-700)] border-[var(--color-positive-200)] dark:bg-[var(--color-positive-900)/30] dark:text-[var(--color-positive-400)] dark:border-[var(--color-positive-800)]',
      negative: 'bg-[var(--color-negative-100)] text-[var(--color-negative-700)] border-[var(--color-negative-200)] dark:bg-[var(--color-negative-900)/30] dark:text-[var(--color-negative-400)] dark:border-[var(--color-negative-800)]',
      warning: 'bg-[var(--color-warning-100)] text-[var(--color-warning-700)] border-[var(--color-warning-200)] dark:bg-[var(--color-warning-900)/30] dark:text-[var(--color-warning-400)] dark:border-[var(--color-warning-800)]',
      info: 'bg-[var(--color-info-100)] text-[var(--color-info-700)] border-[var(--color-info-200)] dark:bg-[var(--color-info-900)/30] dark:text-[var(--color-info-400)] dark:border-[var(--color-info-800)]',
      neutral: 'bg-[var(--color-neutral-100)] text-[var(--color-neutral-700)] border-[var(--color-neutral-200)] dark:bg-[var(--color-neutral-800)/30] dark:text-[var(--color-neutral-400)] dark:border-[var(--color-neutral-700)]',
      confidence: 'bg-[var(--color-info-100)] text-[var(--color-info-700)] border-[var(--color-info-200)] dark:text-[var(--color-info-400)]',
      risk: 'bg-[var(--color-negative-100)] text-[var(--color-negative-700)] border-[var(--color-negative-200)] dark:text-[var(--color-negative-400)]',
      status: '',
    },
    dot: {
      true: 'relative pl-5 before:absolute before:left-1.5 before:top-1/2 before:-translate-y-1/2 before:h-1.5 before:w-1.5 before:rounded-full',
      false: '',
    },
    dotColor: {
      positive: 'before:bg-[var(--color-positive-500)]',
      negative: 'before:bg-[var(--color-negative-500)]',
      warning: 'before:bg-[var(--color-warning-500)]',
      info: 'before:bg-[var(--color-info-500)]',
      neutral: 'before:bg-[var(--color-neutral-500)]',
      high: 'before:bg-[var(--color-confidence-high)]',
      medium: 'before:bg-[var(--color-confidence-medium)]',
      low: 'before:bg-[var(--color-confidence-low)]',
    },
  },
});

interface FinancialBadgeProps
  extends React.ComponentProps<typeof Badge>,
    VariantProps<typeof financialBadgeVariants> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'ghost';
}

export function FinancialBadge({
  className,
  semantic = 'neutral',
  dot = false,
  dotColor,
  variant = 'outline',
  children,
  ...props
}: FinancialBadgeProps) {
  return (
    <Badge
      variant={variant}
      className={cn(
        financialBadgeVariants({ semantic, dot, dotColor }),
        className
      )}
      {...props}
    >
      {children}
    </Badge>
  );
}