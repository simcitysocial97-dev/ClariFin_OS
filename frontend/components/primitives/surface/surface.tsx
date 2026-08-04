/**
 * Surface - Stage 8E Financial OS Visual Language
 *
 * The visual language primitive.
 * Everything in the application should be built from Surface.
 */

'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

// ===== Surface Variants =====
export const surfaceVariants = cva(
  'fin-surface transition-all duration-[50ms] ease-out',
  {
    variants: {
      variant: {
        default: '',
        raised: 'fin-surface-raised',
        interactive: 'fin-surface-interactive hover:bg-[var(--surface-interactive)]',
        selected: 'fin-surface-selected',
        floating: 'fin-surface-floating',
        overlay: 'fin-surface-overlay',
        graph: 'fin-surface-graph',
        terminal: 'fin-surface-terminal',
        timeline: 'fin-surface-timeline',
      },
      density: {
        default: 'p-3',
        comfortable: 'p-4',
        compact: 'p-2',
        spacious: 'p-6',
        terminal: 'p-1.5',
        none: 'p-0',
      },
      radius: {
        none: 'rounded-none',
        sm: 'rounded-[var(--radius-sm)]',
        md: 'rounded-[var(--radius-md)]',
        lg: 'rounded-[var(--radius-lg)]',
        xl: 'rounded-[var(--radius-xl)]',
        full: 'rounded-[var(--radius-full)]',
      },
      borderless: {
        true: 'border-0',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      density: 'default',
      radius: 'md',
      borderless: false,
    },
  }
);

// ===== Props =====
export interface SurfaceProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof surfaceVariants> {
  asChild?: boolean;
}

// ===== Surface Component =====
export function Surface({
  className,
  variant,
  density,
  radius,
  borderless,
  children,
  ...props
}: SurfaceProps) {
  return (
    <div
      data-slot="surface"
      data-variant={variant}
      data-density={density}
      className={cn(
        surfaceVariants({ variant, density, radius, borderless }),
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}