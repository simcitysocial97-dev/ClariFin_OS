/**
 * FinancialChip - Stage 8E Financial OS Visual Language
 *
 * Domain-specific chip for display-only financial entities.
 * Each variant maps to a domain model type.
 * Compact, semantic, non-interactive unless specified.
 */

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { X } from 'lucide-react';

export const chipVariants = cva(
  'inline-flex items-center gap-1 rounded-[var(--radius-sm)] px-1.5 py-0.5 text-xs font-medium whitespace-nowrap border transition-colors',
  {
    variants: {
      semantic: {
        account: 'border-[var(--color-info-200)] bg-[var(--color-info-50)] text-[var(--color-info-700)] dark:border-[var(--color-info-800)] dark:bg-[var(--color-info-900)/20] dark:text-[var(--color-info-400)]',
        merchant: 'border-[var(--color-neutral-200)] bg-[var(--color-neutral-100)] text-[var(--color-neutral-700)] dark:border-[var(--color-neutral-700)] dark:bg-[var(--color-neutral-800)/20] dark:text-[var(--color-neutral-400)]',
        category: 'border-[var(--color-neutral-200)] bg-[var(--color-neutral-50)] text-[var(--color-neutral-600)] dark:border-[var(--color-neutral-700)] dark:bg-[var(--color-neutral-800)/10] dark:text-[var(--color-neutral-400)]',
        rule: 'border-[var(--color-info-300)] bg-[var(--color-info-50)] text-[var(--color-info-700)] dark:border-[var(--color-info-800)] dark:text-[var(--color-info-400)]',
        forecast: 'border-[var(--color-info-200)] bg-[var(--color-info-50)] text-[var(--color-info-600)] dark:border-[var(--color-info-800)] dark:text-[var(--color-info-400)]',
        scenario: 'border-[var(--color-warning-200)] bg-[var(--color-warning-50)] text-[var(--color-warning-700)] dark:border-[var(--color-warning-800)] dark:text-[var(--color-warning-400)]',
        risk: 'border-[var(--color-negative-200)] bg-[var(--color-negative-50)] text-[var(--color-negative-700)] dark:border-[var(--color-negative-800)] dark:text-[var(--color-negative-400)]',
        confidence: 'border-[var(--color-positive-200)] bg-[var(--color-positive-50)] text-[var(--color-positive-700)] dark:border-[var(--color-positive-800)] dark:text-[var(--color-positive-400)]',
        filter: 'border-[var(--color-info-200)] bg-[var(--color-info-50)] text-[var(--color-info-700)] dark:border-[var(--color-info-800)] dark:text-[var(--color-info-400)]',
        selection: 'border-[var(--color-selection)] bg-[var(--color-selection-halo)] text-[var(--color-selection)]',
      },
      size: {
        sm: 'text-[10px] px-1 py-0',
        md: 'text-xs px-1.5 py-0.5',
      },
      removable: {
        true: 'pr-1',
        false: '',
      },
    },
    defaultVariants: {
      semantic: 'merchant',
      size: 'md',
      removable: false,
    },
  }
);

interface FinancialChipProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof chipVariants> {
  label: string;
  onRemove?: () => void;
}

export function FinancialChip({
  className,
  semantic = 'merchant',
  size = 'md',
  removable = false,
  label,
  onRemove,
  ...props
}: FinancialChipProps) {
  return (
    <span
      className={cn(
        chipVariants({ semantic, size, removable }),
        className
      )}
      {...props}
    >
      {label}
      {removable && onRemove && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 hover:opacity-70"
          aria-label={`Remove ${label}`}
        >
          <X className="h-2.5 w-2.5" />
        </button>
      )}
    </span>
  );
}