/**
 * Card - Stage 8E Financial OS Visual Language
 *
 * Generic card primitive built on Surface.
 * Provides Header, Body, and Footer slots for consistent composition.
 * Follows the unified design language with surface variants, density, and radii.
 */

'use client';

import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Surface } from '@/components/primitives/surface/surface';

export const cardVariants = cva(
  'fin-surface flex flex-col transition-all duration-150 ease-out',
  {
    variants: {
      variant: {
        default: 'fin-surface',
        elevated: 'fin-surface-raised',
        interactive: 'fin-surface-interactive',
        selected: 'fin-surface-selected',
      },
      density: {
        compact: 'p-2',
        default: 'p-3',
        comfortable: 'p-4',
        spacious: 'p-6',
      },
      radius: {
        none: 'rounded-none',
        sm: 'rounded-[var(--radius-sm)]',
        md: 'rounded-[var(--radius-md)]',
        lg: 'rounded-[var(--radius-lg)]',
        xl: 'rounded-[var(--radius-xl)]',
        full: 'rounded-[var(--radius-full)]',
      },
    },
    defaultVariants: {
      variant: 'default',
      density: 'default',
      radius: 'md',
    },
  }
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {
  variant?: 'default' | 'elevated' | 'interactive' | 'selected';
  density?: 'compact' | 'default' | 'comfortable' | 'spacious';
}

export function Card({
  className,
  variant = 'default',
  density = 'default',
  radius = 'md',
  children,
  ...props
}: CardProps) {
  const surfaceVariant =
    variant === 'elevated' ? 'raised'
    : variant === 'interactive' ? 'interactive'
      : variant === 'selected' ? 'selected'
        : 'default';

  return (
    <Surface
      variant={surfaceVariant}
      radius={radius}
      className={cn(
        cardVariants({ variant, density, radius }),
        className
      )}
      {...props}
    >
      {children}
    </Surface>
  );
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function CardHeader({
  title,
  subtitle,
  actions,
  children,
  className,
  ...props
}: CardHeaderProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-2 border-b border-[var(--border-subtle)]',
        className
      )}
      {...props}
    >
      <div className="min-w-0 flex-1">
        {title && <h3 className="fin-panel-header text-[var(--text-primary)] truncate">{title}</h3>}
        {subtitle && <p className="fin-caption text-[var(--text-tertiary)] truncate">{subtitle}</p>}
        {children}
      </div>
      {actions && (
        <div className="flex items-center gap-1 ml-2 shrink-0">
          {actions}
        </div>
      )}
    </div>
  );
}

export interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  scrollable?: boolean;
}

export function CardBody({
  scrollable = false,
  className,
  children,
  ...props
}: CardBodyProps) {
  return (
    <div
      className={cn(
        'flex-1',
        scrollable && 'overflow-y-auto',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  divided?: boolean;
}

export function CardFooter({
  divided = true,
  className,
  children,
  ...props
}: CardFooterProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-between px-3 py-1.5',
        divided && 'border-t border-[var(--border-subtle)]',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

// Attach sub-components to the main Card component
Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;
